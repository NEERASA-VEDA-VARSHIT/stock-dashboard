from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.stock_repository import (
    get_all_companies,
    get_stock_data_filtered,
    get_stock_summary,
    get_symbol_price_window,
    get_top_movers,
)
from app.schemas.stock_schema import (
    CompaniesResponse,
    CompareStocksResponse,
    StockComparisonResponse,
    StockDataListResponse,
    StockDataQueryMeta,
    StockDataResponse,
    StockMoverResponse,
    StockSummaryResponse,
    TopMoversResponse,
)
from app.services.service_common import cache_key, round_opt
from app.utils.cache import api_cache
from app.utils.finance import calculate_pct_change


def list_companies(db: Session):
    results = get_all_companies(db)
    return CompaniesResponse(total=len(results), companies=[r[0] for r in results])


def fetch_stock_data(
    db: Session,
    symbol: str,
    days: int = 30,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: str = "date",
    order: str = "desc",
):
    key = cache_key("data", symbol, days, start_date or "none", end_date or "none", sort_by, order)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    rows = get_stock_data_filtered(
        db,
        symbol,
        days=days,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")

    payload = [
        StockDataResponse(
            symbol=row.symbol,
            date=row.date,
            open=round(float(row.open), 4),
            close=round(float(row.close), 4),
            high=round(float(row.high), 4),
            low=round(float(row.low), 4),
            volume=int(row.volume),
            daily_return=round_opt(row.daily_return),
            ma7=round_opt(row.ma7),
            ma30=round_opt(row.ma30),
            momentum_7d=round_opt(row.momentum_7d),
            range_pct=round_opt(row.range_pct),
            trend_strength=round_opt(row.trend_strength),
            drawdown=round_opt(row.drawdown),
            sharpe_like_30=round_opt(row.sharpe_like_30),
            high_52w=round_opt(row.high_52w, 4),
            low_52w=round_opt(row.low_52w, 4),
            volatility=round_opt(row.volatility),
        )
        for row in rows
    ]

    response = StockDataListResponse(
        symbol=symbol,
        count=len(payload),
        query=StockDataQueryMeta(
            days=days,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order,
        ),
        data=payload,
    )
    api_cache.set(key, response, ttl_seconds=60)
    return response


def fetch_stock_summary(db: Session, symbol: str):
    key = cache_key("summary", symbol)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    summary = get_stock_summary(db, symbol)
    if not summary or summary.high_52w is None or summary.low_52w is None or summary.avg_close is None:
        raise HTTPException(status_code=404, detail=f"No summary found for symbol '{symbol}'")

    response = StockSummaryResponse(
        symbol=symbol,
        high_52w=round(float(summary.high_52w), 4),
        low_52w=round(float(summary.low_52w), 4),
        avg_close=round(float(summary.avg_close), 4),
    )
    api_cache.set(key, response, ttl_seconds=300)
    return response


def _build_comparison(rows, symbol: str) -> StockComparisonResponse:
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail=f"Not enough data points to compare symbol '{symbol}'")

    start_close = float(rows[0].close)
    end_close = float(rows[-1].close)
    if start_close == 0:
        raise HTTPException(status_code=400, detail=f"Invalid baseline close price for symbol '{symbol}'")

    pct_change = calculate_pct_change(start_close, end_close)
    return StockComparisonResponse(
        symbol=symbol,
        start_close=start_close,
        end_close=end_close,
        pct_change=pct_change,
    )


def compare_stocks(db: Session, symbol1: str, symbol2: str, days: int = 30) -> CompareStocksResponse:
    key = cache_key("compare", symbol1, symbol2, days)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    rows1 = get_symbol_price_window(db, symbol1, days)
    rows2 = get_symbol_price_window(db, symbol2, days)

    if not rows1:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol1}'")
    if not rows2:
        raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol2}'")

    left = _build_comparison(rows1, symbol1)
    right = _build_comparison(rows2, symbol2)
    winner_symbol = left.symbol if left.pct_change >= right.pct_change else right.symbol
    spread_pct = round(abs(left.pct_change - right.pct_change), 6)

    response = CompareStocksResponse(
        symbol1=left,
        symbol2=right,
        winner_symbol=winner_symbol,
        spread_pct=spread_pct,
    )
    api_cache.set(key, response, ttl_seconds=120)
    return response


def fetch_top_gainers(db: Session, limit: int = 5) -> TopMoversResponse:
    key = cache_key("top-gainers", limit)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    rows = get_top_movers(db, limit=limit, ascending=False)
    response = TopMoversResponse(
        type="gainers",
        count=len(rows),
        data=[
            StockMoverResponse(
                symbol=row.symbol,
                date=row.date,
                daily_return=round(float(row.daily_return), 6),
                close=round(float(row.close), 4),
            )
            for row in rows
        ],
    )
    api_cache.set(key, response, ttl_seconds=60)
    return response


def fetch_top_losers(db: Session, limit: int = 5) -> TopMoversResponse:
    key = cache_key("top-losers", limit)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    rows = get_top_movers(db, limit=limit, ascending=True)
    response = TopMoversResponse(
        type="losers",
        count=len(rows),
        data=[
            StockMoverResponse(
                symbol=row.symbol,
                date=row.date,
                daily_return=round(float(row.daily_return), 6),
                close=round(float(row.close), 4),
            )
            for row in rows
        ],
    )
    api_cache.set(key, response, ttl_seconds=60)
    return response
