import re

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL
from app.repositories.stock_repository import get_stock_data_filtered
from app.schemas.stock_schema import AIChatMessage, StockAIChatResponse, StockAIExplanationResponse
from app.services.service_common import cache_key, round_opt
from app.services.signal_service import build_signal_report, fetch_stock_explanation, generate_signals
from app.utils.cache import api_cache


def _extract_gemini_text(payload: dict) -> str | None:
    candidates = payload.get("candidates")
    if not candidates:
        return None

    first = candidates[0]
    content = first.get("content", {})
    parts = content.get("parts", [])
    texts = [p.get("text", "").strip() for p in parts if isinstance(p, dict)]
    merged = "\n".join([t for t in texts if t])
    return merged or None


def _normalize_gemini_model(model: str) -> str:
    normalized = (model or "").strip()
    alias_map = {
        "gemini-3-flash": "gemini-2.5-flash",
        "gemini-3.0-flash": "gemini-2.5-flash",
        "gemini-pro": "gemini-2.5-pro",
    }
    return alias_map.get(normalized, normalized or "gemini-2.5-flash")


def _gemini_model_candidates(model: str) -> list[str]:
    primary = _normalize_gemini_model(model)
    ordered = [
        primary,
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
    ]
    unique: list[str] = []
    seen = set()
    for name in ordered:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def _sanitize_fallback_reason(reason: str) -> str:
    scrubbed = re.sub(r"([?&]key=)[^&\s]+", r"\1***", reason)
    if len(scrubbed) > 240:
        scrubbed = scrubbed[:240] + "..."
    return scrubbed


def _call_gemini(prompt: str, max_output_tokens: int = 220, temperature: float = 0.2) -> tuple[str, str]:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }

    last_error = "Unknown Gemini error"
    for model_name in _gemini_model_candidates(GEMINI_MODEL):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

        for attempt in range(2):
            try:
                resp = requests.post(url, params={"key": GEMINI_API_KEY}, json=payload, timeout=30)
                resp.raise_for_status()
                text = _extract_gemini_text(resp.json())
                if not text:
                    raise ValueError("Empty Gemini response")
                return text, model_name
            except requests.exceptions.Timeout:
                if attempt == 0:
                    continue
                last_error = "Gemini API request timed out (read timeout). Falling back to rule-based analysis."
            except Exception as exc:
                last_error = str(exc)
                break

    raise RuntimeError(last_error)


def _history_summary(history: list[AIChatMessage], keep_last: int = 8) -> str | None:
    if len(history) <= keep_last:
        return None

    older = history[: len(history) - keep_last]
    lines: list[str] = []
    for msg in older[-6:]:
        text = msg.content.strip().replace("\n", " ")
        if len(text) > 120:
            text = text[:120] + "..."
        lines.append(f"{msg.role}: {text}")

    return " | ".join(lines) if lines else None


def fetch_ai_stock_explanation(
    db: Session,
    symbol: str,
    model: str = "linear",
    horizon: int = 1,
    days: int = 60,
) -> StockAIExplanationResponse:
    key = cache_key("ai-explain", symbol, model, horizon, days)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    baseline = fetch_stock_explanation(db, symbol)

    rows = get_stock_data_filtered(
        db,
        symbol,
        days=days,
        sort_by="date",
        order="desc",
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")

    signals = generate_signals(rows)
    signal_block = "\n".join([f"- {s}" for s in signals])

    if not GEMINI_API_KEY:
        fallback_text = (
            "Directional View: "
            + ("Bullish" if baseline.trend == "UP" else "Bearish" if baseline.trend == "DOWN" else "Neutral")
            + "\nConfidence: Moderate\n"
            + "Supporting Signals:\n"
            + signal_block
            + "\nSummary:\nMarket setup is mixed with trend and volatility signals shown above."
        )
        response = StockAIExplanationResponse(
            symbol=symbol,
            provider="fallback",
            model="rule-based",
            analysis=fallback_text,
            fallback_used=True,
            fallback_reason="GEMINI_API_KEY not configured",
        )
        api_cache.set(key, response, ttl_seconds=120)
        return response

    prompt = (
        "You are a financial analyst.\n\n"
        "Based on the following signals:\n"
        f"{signal_block}\n\n"
        "Generate:\n"
        "1) Directional view (Bullish/Bearish/Neutral)\n"
        "2) Confidence level (Low/Moderate/High)\n"
        "3) 3-4 supporting signals (clear bullet points)\n"
        "4) A short summary (2 lines)\n\n"
        "Do NOT predict future prices.\n"
        "Do NOT mention machine learning.\n"
        "Keep it professional and concise.\n"
    )

    try:
        text, model_name = _call_gemini(prompt=prompt, max_output_tokens=420, temperature=0.2)
        if len(text.strip()) < 120 or "confidence" not in text.lower():
            text = build_signal_report(signals, baseline.trend)
        response = StockAIExplanationResponse(
            symbol=symbol,
            provider="gemini",
            model=model_name,
            analysis=text,
            fallback_used=False,
        )
        api_cache.set(key, response, ttl_seconds=180)
        return response
    except Exception as exc:
        last_error = _sanitize_fallback_reason(str(exc))

    response = StockAIExplanationResponse(
        symbol=symbol,
        provider="fallback",
        model="rule-based",
        analysis=build_signal_report(signals, baseline.trend),
        fallback_used=True,
        fallback_reason=last_error,
    )
    api_cache.set(key, response, ttl_seconds=120)
    return response


def fetch_ai_chat_response(
    db: Session,
    symbol: str,
    message: str,
    history: list[AIChatMessage] | None = None,
    conversation_summary: str | None = None,
) -> StockAIChatResponse:
    if not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = history or []
    baseline = fetch_stock_explanation(db, symbol)

    latest_rows = get_stock_data_filtered(
        db,
        symbol,
        days=30,
        sort_by="date",
        order="desc",
    )
    if not latest_rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")

    latest = latest_rows[0]
    context_lines = [
        f"Symbol: {symbol}",
        f"Latest date: {latest.date}",
        f"Latest close: {round(float(latest.close), 4)}",
        f"Signal: {baseline.signal}",
        f"Trend: {baseline.trend}",
        f"Volatility band: {baseline.volatility_band}",
        f"Drawdown pct: {baseline.drawdown_pct}",
    ]

    recent_points = []
    for row in latest_rows[:7]:
        recent_points.append(
            f"{row.date}: close={round(float(row.close), 4)}, "
            f"ret={round_opt(row.daily_return)}, vol={round_opt(row.volatility)}"
        )

    compact_history = history[-8:]
    auto_summary = _history_summary(history, keep_last=8)
    summary = conversation_summary or auto_summary

    history_block = "\n".join([f"{m.role}: {m.content.strip()}" for m in compact_history])
    prompt = (
        "You are a stock assistant in a dashboard chat. "
        "Use only provided context and be explicit about uncertainty. "
        "Keep response under 180 words and include actionable bullets when relevant.\n\n"
        "Market context:\n"
        + "\n".join(context_lines)
        + "\n\nRecent points:\n"
        + "\n".join(recent_points)
        + "\n\nConversation summary:\n"
        + (summary or "None")
        + "\n\nRecent chat turns:\n"
        + (history_block or "None")
        + "\n\nUser question:\n"
        + message.strip()
    )

    if not GEMINI_API_KEY:
        fallback_reply = (
            f"{baseline.explanation} You asked: {message.strip()} "
            "(Gemini key not configured, so this is deterministic guidance.)"
        )
        return StockAIChatResponse(
            symbol=symbol,
            provider="fallback",
            model="rule-based",
            reply=fallback_reply,
            fallback_used=True,
            fallback_reason="GEMINI_API_KEY not configured",
            context_window_used=len(compact_history),
            conversation_summary=summary,
        )

    try:
        reply, model_name = _call_gemini(prompt=prompt, max_output_tokens=320, temperature=0.3)
        return StockAIChatResponse(
            symbol=symbol,
            provider="gemini",
            model=model_name,
            reply=reply,
            fallback_used=False,
            fallback_reason=None,
            context_window_used=len(compact_history),
            conversation_summary=summary,
        )
    except Exception as exc:
        reason = _sanitize_fallback_reason(str(exc))
        fallback_reply = (
            f"{baseline.explanation} I could not reach Gemini right now. "
            "Try again in a moment."
        )
        return StockAIChatResponse(
            symbol=symbol,
            provider="fallback",
            model="rule-based",
            reply=fallback_reply,
            fallback_used=True,
            fallback_reason=reason,
            context_window_used=len(compact_history),
            conversation_summary=summary,
        )
