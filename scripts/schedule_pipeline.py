from pathlib import Path
import sys
import argparse
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_pipeline import run  # noqa: E402
from app.core.schema_sync import init_db_schema  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run stock ETL on a fixed interval")
    parser.add_argument("--symbols", default="INFY.NS,TCS.NS", help="Comma-separated symbols")
    parser.add_argument("--interval-minutes", type=int, default=60, help="Schedule interval in minutes")
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        raise ValueError("At least one symbol is required")

    init_db_schema()
    interval_seconds = max(1, args.interval_minutes) * 60

    while True:
        for symbol in symbols:
            try:
                run(symbol)
            except Exception as exc:
                print(f"Pipeline failed for {symbol}: {exc}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
