from sqlalchemy.orm import Session
from app.models.stock import StockFeature, StockPrice
import math
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.core.db import engine
from app.utils.cache import api_cache

def safe_value(val):
    if val is None:
        return None
    if hasattr(val, "item"):
        val = val.item()  # Convert numpy scalar -> native Python scalar.
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def load_stock_data(db: Session, df):
    price_records = []
    feature_records = []
    symbols = set()

    for _, row in df.iterrows():
        symbol = str(row["symbol"])
        price_record = {
            "symbol": symbol,
            "date": row["Date"].date(),
            "open": float(safe_value(row["Open"]) or 0.0),
            "close": float(safe_value(row["Close"]) or 0.0),
            "high": float(safe_value(row["High"]) or 0.0),
            "low": float(safe_value(row["Low"]) or 0.0),
            "volume": int(float(safe_value(row["Volume"]) or 0.0)),
        }
        feature_record = {
            "symbol": symbol,
            "date": row["Date"].date(),
            "daily_return": safe_value(row.get("daily_return")),
            "ma7": safe_value(row.get("ma7")),
            "ma30": safe_value(row.get("ma30")),
            "momentum_7d": safe_value(row.get("momentum_7d")),
            "range_pct": safe_value(row.get("range_pct")),
            "trend_strength": safe_value(row.get("trend_strength")),
            "drawdown": safe_value(row.get("drawdown")),
            "sharpe_like_30": safe_value(row.get("sharpe_like_30")),
            "high_52w": safe_value(row.get("52w_high")),
            "low_52w": safe_value(row.get("52w_low")),
            "volatility": safe_value(row.get("volatility")),
        }
        price_records.append(price_record)
        feature_records.append(feature_record)
        symbols.add(symbol)

    if not price_records:
        return

    price_update_columns = {
        "open": None,
        "close": None,
        "high": None,
        "low": None,
        "volume": None,
    }
    feature_update_columns = {
        "daily_return": None,
        "ma7": None,
        "ma30": None,
        "momentum_7d": None,
        "range_pct": None,
        "trend_strength": None,
        "drawdown": None,
        "sharpe_like_30": None,
        "high_52w": None,
        "low_52w": None,
        "volatility": None,
    }

    dialect = engine.dialect.name
    if dialect == "postgresql":
        price_insert_stmt = pg_insert(StockPrice.__table__).values(price_records)
        price_set_map = {k: getattr(price_insert_stmt.excluded, k) for k in price_update_columns.keys()}
        price_set_map["updated_at"] = func.now()
        price_stmt = price_insert_stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=price_set_map,
        )
        db.execute(price_stmt)

        feature_insert_stmt = pg_insert(StockFeature.__table__).values(feature_records)
        feature_set_map = {k: getattr(feature_insert_stmt.excluded, k) for k in feature_update_columns.keys()}
        feature_set_map["updated_at"] = func.now()
        feature_stmt = feature_insert_stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=feature_set_map,
        )
        db.execute(feature_stmt)
    elif dialect == "sqlite":
        price_insert_stmt = sqlite_insert(StockPrice.__table__).values(price_records)
        price_set_map = {k: getattr(price_insert_stmt.excluded, k) for k in price_update_columns.keys()}
        price_set_map["updated_at"] = func.now()
        price_stmt = price_insert_stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=price_set_map,
        )
        db.execute(price_stmt)

        feature_insert_stmt = sqlite_insert(StockFeature.__table__).values(feature_records)
        feature_set_map = {k: getattr(feature_insert_stmt.excluded, k) for k in feature_update_columns.keys()}
        feature_set_map["updated_at"] = func.now()
        feature_stmt = feature_insert_stmt.on_conflict_do_update(
            index_elements=["symbol", "date"],
            set_=feature_set_map,
        )
        db.execute(feature_stmt)
    else:
        db.bulk_insert_mappings(StockPrice, price_records)
        db.bulk_insert_mappings(StockFeature, feature_records)

    db.commit()

    # Granular cache invalidation after data mutation.
    api_cache.invalidate_prefixes([
        "v1:companies",
        "v1:top-gainers",
        "v1:top-losers",
        "v1:compare",
        "v1:search",
    ])
    for symbol in symbols:
        api_cache.invalidate_prefixes([
            f"v1:data:{symbol}:",
            f"v1:summary:{symbol}",
            f"v1:signal:{symbol}",
            f"v1:predict:{symbol}:",
            f"v1:explain:{symbol}",
            f"v1:ai-explain:{symbol}:",
        ])