import pandas as pd

def transform_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Daily Return = (Close - Open) / Open.
    open_price = df["Open"].replace(0, pd.NA)
    df["daily_return"] = ((df["Close"] - df["Open"]) / open_price).astype(float)

    # 7-day Moving Average
    df["ma7"] = df["Close"].rolling(window=7, min_periods=1).mean()

    # 30-day Moving Average and trend strength (MA7 - MA30).
    df["ma30"] = df["Close"].rolling(window=30, min_periods=1).mean()
    df["trend_strength"] = df["ma7"] - df["ma30"]

    # 7-day momentum and intraday range percentage.
    df["momentum_7d"] = df["Close"] - df["Close"].shift(7)
    safe_close = df["Close"].replace(0, pd.NA)
    df["range_pct"] = ((df["High"] - df["Low"]) / safe_close).astype(float)

    # 52-week High/Low (~252 trading days)
    df["52w_high"] = df["High"].rolling(window=252, min_periods=1).max()
    df["52w_low"] = df["Low"].rolling(window=252, min_periods=1).min()

    # Volatility (custom metric 🔥)
    df["volatility"] = df["daily_return"].rolling(window=7, min_periods=2).std()

    # Drawdown from running peak close.
    rolling_peak = df["Close"].cummax().replace(0, pd.NA)
    df["drawdown"] = ((df["Close"] - rolling_peak) / rolling_peak).astype(float)

    # Sharpe-like rolling score over 30 sessions.
    rolling_mean = df["daily_return"].rolling(window=30, min_periods=5).mean()
    rolling_std = df["daily_return"].rolling(window=30, min_periods=5).std()
    df["sharpe_like_30"] = (rolling_mean / rolling_std.replace(0, pd.NA)).astype(float)

    return df