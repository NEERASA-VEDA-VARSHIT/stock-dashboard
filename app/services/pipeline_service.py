from io import StringIO
from typing import Literal

import pandas as pd
from sqlalchemy.orm import Session

from app.pipelines.cleaner import clean_stock_data
from app.pipelines.fetcher import fetch_stock_data
from app.pipelines.loader import load_stock_data
from app.pipelines.transformer import transform_stock_data

CleaningStrategy = Literal["standard", "aggressive", "minimal"]


def run_pipeline_for_symbol(
    db: Session,
    symbol: str,
    cleaning: CleaningStrategy = "standard",
    period: str = "1y",
) -> dict:
    df = fetch_stock_data(symbol, period=period)
    source_provider = df.attrs.get("source_provider", "yfinance")
    df = clean_stock_data(df, strategy=cleaning)
    df = transform_stock_data(df)
    load_stock_data(db, df)

    return {
        "symbol": symbol,
        "rows_loaded": int(len(df)),
        "cleaning": cleaning,
        "source": source_provider,
    }


def run_pipeline_for_csv(
    db: Session,
    csv_content: str,
    symbol: str,
    cleaning: CleaningStrategy = "standard",
) -> dict:
    df = pd.read_csv(StringIO(csv_content))
    if "symbol" not in df.columns:
        df["symbol"] = symbol

    df = clean_stock_data(df, strategy=cleaning)
    df = transform_stock_data(df)
    load_stock_data(db, df)

    return {
        "symbol": symbol,
        "rows_loaded": int(len(df)),
        "cleaning": cleaning,
        "source": "csv",
    }
