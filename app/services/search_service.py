from csv import DictReader
from pathlib import Path
from typing import List

import requests

from app.core.config import ENABLE_YAHOO_SEARCH_FALLBACK, SYMBOLS_DATASET_PATH


_SYMBOL_CACHE: list[dict] | None = None
_SYMBOL_CACHE_MTIME: float | None = None


def _load_local_symbols() -> list[dict]:
    global _SYMBOL_CACHE, _SYMBOL_CACHE_MTIME

    dataset_path = Path(SYMBOLS_DATASET_PATH)
    if not dataset_path.exists():
        _SYMBOL_CACHE = []
        _SYMBOL_CACHE_MTIME = None
        return _SYMBOL_CACHE

    mtime = dataset_path.stat().st_mtime
    if _SYMBOL_CACHE is not None and _SYMBOL_CACHE_MTIME == mtime:
        return _SYMBOL_CACHE

    rows: list[dict] = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        reader = DictReader(handle)
        for row in reader:
            symbol = (row.get("symbol") or "").strip().upper()
            name = (row.get("name") or symbol).strip()
            if not symbol:
                continue
            rows.append({"symbol": symbol, "name": name})

    _SYMBOL_CACHE = rows
    _SYMBOL_CACHE_MTIME = mtime
    return _SYMBOL_CACHE


def _search_local(query: str, limit: int = 10) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []

    scored: list[tuple[int, dict]] = []
    for item in _load_local_symbols():
        symbol_l = item["symbol"].lower()
        name_l = item["name"].lower()
        if q not in symbol_l and q not in name_l:
            continue

        score = 0
        if symbol_l.startswith(q):
            score += 3
        if name_l.startswith(q):
            score += 2
        if q in symbol_l:
            score += 1
        if q in name_l:
            score += 1
        scored.append((score, item))

    scored.sort(key=lambda x: (-x[0], x[1]["name"], x[1]["symbol"]))
    return [item for _, item in scored[:limit]]


def _search_yahoo(query: str, limit: int = 10) -> list[dict]:
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    payload = resp.json()

    results = []
    for item in payload.get("quotes", []):
        symbol = item.get("symbol")
        shortname = item.get("shortname") or item.get("longname") or symbol
        quote_type = item.get("quoteType")
        if not symbol or quote_type not in {"EQUITY", "ETF", "MUTUALFUND"}:
            continue
        results.append({"symbol": symbol, "name": shortname})
        if len(results) >= limit:
            break

    return results


def search_companies(query: str) -> List[dict]:
    local = _search_local(query, limit=10)
    if len(local) >= 3 or not ENABLE_YAHOO_SEARCH_FALLBACK:
        return local

    try:
        remote = _search_yahoo(query, limit=10)
    except Exception:
        remote = []

    combined = []
    seen = set()
    for item in [*local, *remote]:
        key = item["symbol"].upper()
        if key in seen:
            continue
        seen.add(key)
        combined.append(item)
        if len(combined) >= 10:
            break

    return combined
