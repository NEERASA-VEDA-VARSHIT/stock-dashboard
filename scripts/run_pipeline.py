from pathlib import Path
import sys
import argparse

# Ensure the project root is importable when running this file directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.db import SessionLocal
from app.core.schema_sync import init_db_schema
from app.pipelines.fetcher import fetch_stock_data
from app.pipelines.cleaner import clean_stock_data
from app.pipelines.transformer import transform_stock_data
from app.pipelines.loader import load_stock_data

def run(symbol: str, cleaning: str = "standard"):
    db = SessionLocal()

    try:
        df = fetch_stock_data(symbol)
        source_provider = df.attrs.get("source_provider", "yfinance")
        df = clean_stock_data(df, strategy=cleaning)
        df = transform_stock_data(df)
        load_stock_data(db, df)

        print(f"Pipeline completed for {symbol} (cleaning={cleaning}, source={source_provider})")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run stock ETL pipeline")
    parser.add_argument("--symbol", default="INFY.NS", help="Ticker symbol, e.g. INFY.NS")
    parser.add_argument(
        "--symbols",
        default="",
        help="Comma-separated symbols, e.g. INFY.NS,TCS.NS,RELIANCE.NS",
    )
    parser.add_argument(
        "--cleaning",
        default="standard",
        choices=["standard", "aggressive", "minimal"],
        help="Cleaning strategy",
    )
    args = parser.parse_args()

    init_db_schema()
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = [args.symbol]

    for symbol in symbols:
        run(symbol, cleaning=args.cleaning)