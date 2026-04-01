import importlib

import numpy as np
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.stock_repository import get_symbol_close_window
from app.schemas.stock_schema import StockPredictionResponse
from app.services.service_common import cache_key
from app.utils.cache import api_cache


def fetch_prediction(
    db: Session,
    symbol: str,
    days: int = 60,
    horizon: int = 1,
    model: str = "linear",
    ma_window: int = 7,
) -> StockPredictionResponse:
    key = cache_key("predict", symbol, days, horizon, model, ma_window)
    cached = api_cache.get(key)
    if cached is not None:
        return cached

    rows = get_symbol_close_window(db, symbol, days=days)
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail=f"Not enough close-price history for symbol '{symbol}'")

    closes = np.array([float(row.close) for row in rows], dtype=float)
    slope = 0.0
    if model == "linear":
        x = np.arange(len(closes), dtype=float)
        slope, intercept = np.polyfit(x, closes, deg=1)
        prediction_x = len(closes) + horizon - 1
        predicted_close = (slope * prediction_x) + intercept
    elif model == "ma":
        window = min(ma_window, len(closes))
        predicted_close = float(np.mean(closes[-window:]))
        slope = predicted_close - float(closes[-1])
    elif model == "arima":
        try:
            module_name = ".".join(["statsmodels", "tsa", "arima", "model"])
            arima_module = importlib.import_module(module_name)
            ARIMA = getattr(arima_module, "ARIMA")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"ARIMA unavailable: {exc}") from exc

        model_fit = ARIMA(closes, order=(1, 1, 1)).fit()
        forecast = model_fit.forecast(steps=horizon)
        predicted_close = float(forecast[-1])
        slope = predicted_close - float(closes[-1])
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model '{model}'")

    trend = "FLAT"
    if slope > 0:
        trend = "UP"
    elif slope < 0:
        trend = "DOWN"

    response = StockPredictionResponse(
        symbol=symbol,
        model=model,
        days_used=len(closes),
        horizon=horizon,
        predicted_close=round(float(predicted_close), 4),
        slope=round(float(slope), 6),
        trend=trend,
    )
    api_cache.set(key, response, ttl_seconds=120)
    return response
