import pandas as pd
import requests

from app.core.config import ALPHA_VANTAGE_API_KEY
from app.providers.base import StockProvider


class AlphaVantageProvider(StockProvider):
    name = "alpha_vantage"

    def fetch(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        if not ALPHA_VANTAGE_API_KEY:
            raise ValueError("ALPHA_VANTAGE_API_KEY is not configured")

        outputsize = "compact"
        if period in {"2y", "5y", "10y", "max"}:
            outputsize = "full"

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }

        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        series = payload.get("Time Series (Daily)")
        if not series:
            note = payload.get("Note") or payload.get("Information") or payload
            raise ValueError(f"Alpha Vantage response unavailable for {symbol}: {note}")

        rows = []
        for day, values in series.items():
            rows.append(
                {
                    "Date": day,
                    "Open": float(values["1. open"]),
                    "High": float(values["2. high"]),
                    "Low": float(values["3. low"]),
                    "Close": float(values["4. close"]),
                    "Volume": float(values["5. volume"]),
                    "symbol": symbol,
                }
            )

        df = pd.DataFrame(rows)
        if df.empty:
            raise ValueError(f"No data found for {symbol} from Alpha Vantage")

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        return df
