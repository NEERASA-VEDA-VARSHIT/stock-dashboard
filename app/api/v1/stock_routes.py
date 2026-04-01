from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from datetime import date
from typing import Literal
from app.core.db import get_db
from app.services.stock_service import (
    list_companies,
    fetch_stock_data,
    fetch_stock_summary,
    compare_stocks,
    fetch_top_gainers,
    fetch_top_losers,
    fetch_signal,
    fetch_prediction,
    fetch_stock_explanation,
    fetch_ai_stock_explanation,
    fetch_ai_chat_response,
)
from app.services.pipeline_service import run_pipeline_for_symbol, run_pipeline_for_csv
from app.services.search_service import search_companies
from app.core.config import INGEST_ADMIN_KEY, REQUIRE_INGEST_ADMIN
from app.schemas.stock_schema import (
    CompaniesResponse,
    StockDataListResponse,
    StockSummaryResponse,
    CompareStocksResponse,
    TopMoversResponse,
    StockSignalResponse,
    StockPredictionResponse,
    StockExplanationResponse,
    StockAIExplanationResponse,
    StockAIChatRequest,
    StockAIChatResponse,
    SearchCompanyResponse,
    PipelineRunResponse,
)

router = APIRouter(prefix="/stocks", tags=["stocks"])


def _verify_ingest_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not REQUIRE_INGEST_ADMIN:
        return

    # Treat missing server key as disabled ingestion instead of a server error.
    if not INGEST_ADMIN_KEY or x_admin_key != INGEST_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin access required for ingestion endpoints")


@router.get("/companies")
def get_companies(db: Session = Depends(get_db)) -> CompaniesResponse:
    return list_companies(db)


@router.get("/search", response_model=list[SearchCompanyResponse])
def search_stocks(q: str = Query(min_length=1, max_length=50)) -> list[SearchCompanyResponse]:
    try:
        return search_companies(q)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search provider error: {exc}") from exc


def _get_data_impl(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    sort_by: Literal[
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "daily_return",
        "ma7",
        "ma30",
        "momentum_7d",
        "range_pct",
        "trend_strength",
        "drawdown",
        "sharpe_like_30",
        "volatility",
    ] = Query(default="date"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
) -> StockDataListResponse:
    return fetch_stock_data(
        db,
        symbol,
        days=days,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{symbol}/data", response_model=StockDataListResponse)
def get_data(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    sort_by: Literal[
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "daily_return",
        "ma7",
        "ma30",
        "momentum_7d",
        "range_pct",
        "trend_strength",
        "drawdown",
        "sharpe_like_30",
        "volatility",
    ] = Query(default="date"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
) -> StockDataListResponse:
    return _get_data_impl(symbol, days, start_date, end_date, sort_by, order, db)


@router.get("/data/{symbol}", response_model=StockDataListResponse, deprecated=True)
def get_data_legacy(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    sort_by: Literal[
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "daily_return",
        "ma7",
        "volatility",
    ] = Query(default="date"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
) -> StockDataListResponse:
    return _get_data_impl(symbol, days, start_date, end_date, sort_by, order, db)


@router.get("/summary/{symbol}", response_model=StockSummaryResponse)
def get_summary(symbol: str, db: Session = Depends(get_db)) -> StockSummaryResponse:
    return fetch_stock_summary(db, symbol)


@router.get("/compare", response_model=CompareStocksResponse)
def compare(
    symbol1: str,
    symbol2: str,
    days: int = Query(default=30, ge=2, le=365),
    db: Session = Depends(get_db),
) -> CompareStocksResponse:
    return compare_stocks(db, symbol1, symbol2, days)


@router.get("/top-gainers", response_model=TopMoversResponse)
def top_gainers(limit: int = Query(default=5, ge=1, le=50), db: Session = Depends(get_db)) -> TopMoversResponse:
    return fetch_top_gainers(db, limit=limit)


@router.get("/top-losers", response_model=TopMoversResponse)
def top_losers(limit: int = Query(default=5, ge=1, le=50), db: Session = Depends(get_db)) -> TopMoversResponse:
    return fetch_top_losers(db, limit=limit)


@router.get("/{symbol}/signal", response_model=StockSignalResponse)
def signal(symbol: str, db: Session = Depends(get_db)) -> StockSignalResponse:
    return fetch_signal(db, symbol)


@router.get("/{symbol}/predict", response_model=StockPredictionResponse)
def predict(
    symbol: str,
    days: int = Query(default=60, ge=10, le=365),
    horizon: int = Query(default=1, ge=1, le=30),
    model: Literal["linear", "ma", "arima"] = Query(default="linear"),
    ma_window: int = Query(default=7, ge=2, le=60),
    db: Session = Depends(get_db),
) -> StockPredictionResponse:
    return fetch_prediction(db, symbol, days=days, horizon=horizon, model=model, ma_window=ma_window)


@router.get("/{symbol}/explain", response_model=StockExplanationResponse)
def explain(symbol: str, db: Session = Depends(get_db)) -> StockExplanationResponse:
    return fetch_stock_explanation(db, symbol)


@router.get("/{symbol}/ai-explain", response_model=StockAIExplanationResponse)
def ai_explain(
    symbol: str,
    model: Literal["linear", "ma", "arima"] = Query(default="linear"),
    horizon: int = Query(default=1, ge=1, le=30),
    days: int = Query(default=60, ge=10, le=365),
    db: Session = Depends(get_db),
) -> StockAIExplanationResponse:
    return fetch_ai_stock_explanation(db, symbol, model=model, horizon=horizon, days=days)


@router.post("/{symbol}/ai-chat", response_model=StockAIChatResponse)
def ai_chat(symbol: str, payload: StockAIChatRequest, db: Session = Depends(get_db)) -> StockAIChatResponse:
    return fetch_ai_chat_response(
        db,
        symbol=symbol,
        message=payload.message,
        history=payload.history,
        conversation_summary=payload.conversation_summary,
    )


@router.post("/pipeline/run", response_model=PipelineRunResponse)
def run_pipeline(
    symbol: str = Query(...),
    cleaning: Literal["standard", "aggressive", "minimal"] = Query(default="standard"),
    period: str = Query(default="1y"),
    _admin: None = Depends(_verify_ingest_admin),
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    return run_pipeline_for_symbol(db, symbol=symbol, cleaning=cleaning, period=period)


@router.post("/upload", response_model=PipelineRunResponse)
async def upload_csv(
    file: UploadFile = File(...),
    symbol: str = Query(...),
    cleaning: Literal["standard", "aggressive", "minimal"] = Query(default="standard"),
    _admin: None = Depends(_verify_ingest_admin),
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = (await file.read()).decode("utf-8", errors="ignore")
    return run_pipeline_for_csv(db, csv_content=content, symbol=symbol, cleaning=cleaning)