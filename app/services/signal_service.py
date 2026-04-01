from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.stock_repository import get_latest_stock_point
from app.schemas.stock_schema import StockExplanationResponse, StockSignalResponse
from app.services.service_common import cache_key
from app.utils.cache import api_cache


def fetch_signal(db: Session, symbol: str) -> StockSignalResponse:
    key = cache_key("signal", symbol)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    row = get_latest_stock_point(db, symbol)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")

    close_price = float(row.close)
    ma7_value = float(row.ma7) if row.ma7 is not None else None
    ma30_value = float(row.ma30) if row.ma30 is not None else None
    volatility = float(row.volatility) if row.volatility is not None else None

    if ma7_value is None or ma30_value is None:
        signal = "HOLD"
    elif ma7_value > ma30_value and (volatility is None or volatility <= 0.02):
        signal = "BUY"
    elif ma7_value < ma30_value or (volatility is not None and volatility >= 0.03):
        signal = "SELL"
    else:
        signal = "HOLD"

    response = StockSignalResponse(
        symbol=row.symbol,
        date=row.date,
        close=round(close_price, 4),
        ma7=round(ma7_value, 4) if ma7_value is not None else None,
        signal=signal,
    )
    api_cache.set(key, response, ttl_seconds=60)
    return response


def fetch_stock_explanation(db: Session, symbol: str) -> StockExplanationResponse:
    key = cache_key("explain", symbol)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    row = get_latest_stock_point(db, symbol)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")

    signal_obj = fetch_signal(db, symbol)
    trend_strength = float(row.trend_strength) if row.trend_strength is not None else 0.0
    volatility = float(row.volatility) if row.volatility is not None else 0.0
    drawdown = float(row.drawdown) if row.drawdown is not None else None

    if trend_strength > 0:
        trend = "UP"
    elif trend_strength < 0:
        trend = "DOWN"
    else:
        trend = "FLAT"

    if volatility < 0.01:
        volatility_band = "LOW"
    elif volatility < 0.02:
        volatility_band = "MEDIUM"
    else:
        volatility_band = "HIGH"

    drawdown_pct = round(drawdown * 100, 2) if drawdown is not None else None
    summary_parts = []
    if volatility < 0.02:
        summary_parts.append("Low volatility")
    if row.daily_return is not None and float(row.daily_return) > 0:
        summary_parts.append("Positive momentum")
    if row.ma7 is not None and row.close is not None and float(row.ma7) > float(row.close):
        summary_parts.append("Uptrend signal")
    summary = " | ".join(summary_parts) if summary_parts else "Mixed signals"

    explanation = (
        f"{symbol} is in a {trend.lower()} trend with {volatility_band.lower()} volatility. "
        f"Signal is {signal_obj.signal}. "
        + (
            f"Current drawdown is {drawdown_pct}% from recent peak."
            if drawdown_pct is not None
            else "Drawdown is currently unavailable."
        )
    )

    response = StockExplanationResponse(
        symbol=symbol,
        date=row.date,
        signal=signal_obj.signal,
        trend=trend,
        volatility_band=volatility_band,
        drawdown_pct=drawdown_pct,
        summary=summary,
        explanation=explanation,
    )
    api_cache.set(key, response, ttl_seconds=60)
    return response


def generate_signals(data) -> list[str]:
    if not data:
        return ["Insufficient market data available"]

    latest = data[0]
    signals: list[str] = []

    if latest.ma7 is not None and latest.close is not None:
        if float(latest.close) > float(latest.ma7):
            signals.append("Price is above 7-day moving average (uptrend)")
        else:
            signals.append("Price is below 7-day moving average (downtrend)")
    else:
        signals.append("Moving-average trend signal unavailable")

    if latest.daily_return is not None:
        if float(latest.daily_return) > 0:
            signals.append("Recent daily returns are positive")
        else:
            signals.append("Recent daily returns are negative")
    else:
        signals.append("Daily return signal unavailable")

    if latest.volatility is not None:
        if float(latest.volatility) > 0.02:
            signals.append("High volatility (riskier movement)")
        elif float(latest.volatility) > 0.01:
            signals.append("Moderate volatility (stable movement)")
        else:
            signals.append("Low volatility (stable movement)")
    else:
        signals.append("Volatility signal unavailable")

    if latest.momentum_7d is not None:
        if float(latest.momentum_7d) > 0:
            signals.append("7-day momentum is positive")
        else:
            signals.append("7-day momentum is negative")

    if latest.drawdown is not None:
        dd = round(float(latest.drawdown) * 100, 2)
        signals.append(f"Current drawdown is {dd}% from recent peak")

    return signals


def build_signal_report(signals: list[str], trend: str) -> str:
    directional = "Bullish" if trend == "UP" else "Bearish" if trend == "DOWN" else "Neutral"
    confidence = "Moderate"
    if len(signals) >= 4:
        confidence = "High"

    support_lines = "\n".join([f"- {s}" for s in signals[:4]])
    return (
        f"Directional View: {directional}\n"
        f"Confidence Level: {confidence}\n"
        "Supporting Signals:\n"
        f"{support_lines}\n"
        "Summary:\n"
        "Current market condition reflects the directional and risk signals above.\n"
        "Use trend and volatility together before making decisions."
    )
