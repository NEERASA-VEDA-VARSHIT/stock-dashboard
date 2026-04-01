import pandas as pd

from app.providers.factory import fetch_with_fallback

def fetch_stock_data(symbol: str, period: str = "1y"):
    df, provider_name = fetch_with_fallback(symbol=symbol, period=period)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.attrs["source_provider"] = provider_name
    return df