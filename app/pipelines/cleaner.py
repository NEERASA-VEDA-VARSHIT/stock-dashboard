import pandas as pd

NUMERIC_COLS = ["Open", "Close", "High", "Low", "Volume"]


def _base_type_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().drop_duplicates()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def minimal_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = _base_type_clean(df)
    return df.sort_values(by="Date").reset_index(drop=True)


def standard_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = _base_type_clean(df)
    # Keep raw OHLCV untouched: only filter out invalid rows.
    df = df.dropna(subset=["Date", "Open", "Close", "High", "Low", "Volume"])
    df = df[(df["Open"] > 0) & (df["High"] > 0) & (df["Low"] > 0) & (df["Close"] > 0) & (df["Volume"] >= 0)]
    df = df[(df["High"] >= df["Low"]) & (df["High"] >= df["Open"]) & (df["High"] >= df["Close"]) ]
    df = df[(df["Low"] <= df["Open"]) & (df["Low"] <= df["Close"]) ]
    return df.sort_values(by="Date").reset_index(drop=True)


def aggressive_clean(df: pd.DataFrame) -> pd.DataFrame:
    # Aggressive strategy now means stricter row validation, not value mutation.
    df = standard_clean(df)
    # Reject candle outliers where intraday range exceeds 40% of close.
    safe_close = df["Close"].replace(0, pd.NA)
    intraday_range = (df["High"] - df["Low"]) / safe_close
    df = df[intraday_range <= 0.40]
    return df.reset_index(drop=True)


def clean_stock_data(df: pd.DataFrame, strategy: str = "standard") -> pd.DataFrame:
    if strategy == "minimal":
        return minimal_clean(df)
    if strategy == "aggressive":
        return aggressive_clean(df)
    return standard_clean(df)