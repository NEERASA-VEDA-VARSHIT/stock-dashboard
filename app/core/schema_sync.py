from sqlalchemy import inspect, text

from app.core.db import Base, engine
from app.models.stock import StockFeature, StockPrice  # noqa: F401


def _float_sql_type() -> str:
    if engine.dialect.name == "postgresql":
        return "DOUBLE PRECISION"
    return "FLOAT"


def _datetime_sql_type() -> str:
    if engine.dialect.name == "postgresql":
        return "TIMESTAMP WITH TIME ZONE"
    return "DATETIME"


def ensure_stocks_table_columns() -> None:
    inspector = inspect(engine)
    if "stocks" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("stocks")}
    required_columns = {
        "daily_return": _float_sql_type(),
        "ma7": _float_sql_type(),
        "ma30": _float_sql_type(),
        "momentum_7d": _float_sql_type(),
        "range_pct": _float_sql_type(),
        "trend_strength": _float_sql_type(),
        "drawdown": _float_sql_type(),
        "sharpe_like_30": _float_sql_type(),
        "high_52w": _float_sql_type(),
        "low_52w": _float_sql_type(),
        "volatility": _float_sql_type(),
    }

    with engine.begin() as connection:
        for column_name, sql_type in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE stocks ADD COLUMN {column_name} {sql_type}")
                )


def init_db_schema() -> None:
    # Create missing tables first; then backfill missing columns on existing tables.
    Base.metadata.create_all(bind=engine)
    ensure_stocks_table_columns()
    ensure_split_table_columns()
    ensure_stock_prices_unique_key()
    ensure_stock_prices_indexes()
    ensure_stock_features_unique_key()
    ensure_stock_features_indexes()
    ensure_stock_features_foreign_key()
    ensure_stock_prices_volume_type()
    migrate_legacy_stocks_to_split_tables()


def ensure_split_table_columns() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    timestamp_type = _datetime_sql_type()
    split_specs = {
        "stock_prices": {
            "created_at": f"{timestamp_type} DEFAULT CURRENT_TIMESTAMP",
            "updated_at": f"{timestamp_type} DEFAULT CURRENT_TIMESTAMP",
        },
        "stock_features": {
            "created_at": f"{timestamp_type} DEFAULT CURRENT_TIMESTAMP",
            "updated_at": f"{timestamp_type} DEFAULT CURRENT_TIMESTAMP",
        },
    }

    with engine.begin() as connection:
        for table_name, required_columns in split_specs.items():
            if table_name not in tables:
                continue
            existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
            for column_name, sql_type in required_columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"))


def ensure_stock_prices_indexes() -> None:
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date ON stock_prices (symbol, date)")
            )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date_desc ON stock_prices (symbol, date DESC)")
            )
        elif engine.dialect.name == "sqlite":
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date ON stock_prices (symbol, date)")
            )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date_desc ON stock_prices (symbol, date DESC)")
            )


def ensure_stock_prices_unique_key() -> None:
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(
                text(
                    """
                    DELETE FROM stock_prices a
                    USING stock_prices b
                    WHERE a.id < b.id
                      AND a.symbol = b.symbol
                      AND a.date = b.date
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_prices_symbol_date_idx ON stock_prices (symbol, date)"
                )
            )
        elif engine.dialect.name == "sqlite":
            connection.execute(
                text(
                    """
                    DELETE FROM stock_prices
                    WHERE id NOT IN (
                        SELECT MAX(id)
                        FROM stock_prices
                        GROUP BY symbol, date
                    )
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_prices_symbol_date_idx ON stock_prices (symbol, date)"
                )
            )


def ensure_stock_features_unique_key() -> None:
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(
                text(
                    """
                    DELETE FROM stock_features a
                    USING stock_features b
                    WHERE a.id < b.id
                      AND a.symbol = b.symbol
                      AND a.date = b.date
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_features_symbol_date_idx ON stock_features (symbol, date)"
                )
            )
        elif engine.dialect.name == "sqlite":
            connection.execute(
                text(
                    """
                    DELETE FROM stock_features
                    WHERE id NOT IN (
                        SELECT MAX(id)
                        FROM stock_features
                        GROUP BY symbol, date
                    )
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_features_symbol_date_idx ON stock_features (symbol, date)"
                )
            )


def ensure_stock_features_indexes() -> None:
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_stock_features_symbol_date ON stock_features (symbol, date)")
            )
            connection.execute(
                text("CREATE INDEX IF NOT EXISTS idx_stock_features_date_daily_return ON stock_features (date, daily_return)")
            )


def ensure_stock_features_foreign_key() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'fk_stock_features_price_symbol_date'
                    ) THEN
                        ALTER TABLE stock_features
                        ADD CONSTRAINT fk_stock_features_price_symbol_date
                        FOREIGN KEY (symbol, date)
                        REFERENCES stock_prices(symbol, date)
                        ON DELETE CASCADE;
                    END IF;
                END $$;
                """
            )
        )


def ensure_stock_prices_volume_type() -> None:
    # SQLite uses dynamic typing, so model-level BigInteger is sufficient there.
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("stock_prices")}
    volume_col = columns.get("volume")
    if volume_col and "BIGINT" in str(volume_col.get("type", "")).upper():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE stock_prices
                ALTER COLUMN volume TYPE BIGINT
                USING ROUND(volume)::BIGINT
                """
            )
        )


def migrate_legacy_stocks_to_split_tables() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "stocks" not in tables or "stock_prices" not in tables or "stock_features" not in tables:
        return

    with engine.begin() as connection:
        has_new_data = connection.execute(text("SELECT 1 FROM stock_prices LIMIT 1")).fetchone() is not None
        if has_new_data:
            return

        if engine.dialect.name == "postgresql":
            connection.execute(
                text(
                    """
                    INSERT INTO stock_prices (symbol, date, open, close, high, low, volume)
                    SELECT symbol, date, open, close, high, low, volume
                    FROM stocks
                    ON CONFLICT (symbol, date) DO NOTHING
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO stock_features (
                        symbol, date, daily_return, ma7, ma30, momentum_7d,
                        range_pct, trend_strength, drawdown, sharpe_like_30,
                        high_52w, low_52w, volatility
                    )
                    SELECT
                        symbol, date, daily_return, ma7, ma30, momentum_7d,
                        range_pct, trend_strength, drawdown, sharpe_like_30,
                        high_52w, low_52w, volatility
                    FROM stocks
                    ON CONFLICT (symbol, date) DO NOTHING
                    """
                )
            )
        else:
            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO stock_prices (symbol, date, open, close, high, low, volume)
                    SELECT symbol, date, open, close, high, low, volume
                    FROM stocks
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT OR IGNORE INTO stock_features (
                        symbol, date, daily_return, ma7, ma30, momentum_7d,
                        range_pct, trend_strength, drawdown, sharpe_like_30,
                        high_52w, low_52w, volatility
                    )
                    SELECT
                        symbol, date, daily_return, ma7, ma30, momentum_7d,
                        range_pct, trend_strength, drawdown, sharpe_like_30,
                        high_52w, low_52w, volatility
                    FROM stocks
                    """
                )
            )
