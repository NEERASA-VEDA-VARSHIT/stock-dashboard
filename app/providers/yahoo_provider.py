import pandas as pd
import yfinance as yf

from app.providers.base import StockProvider


class YahooProvider(StockProvider):
    name = "yahoo"

    def fetch(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        df = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=False)

        if df.empty:
            raise ValueError(f"No data found for {symbol} from Yahoo")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.reset_index(inplace=True)
        df["symbol"] = symbol
        return df
