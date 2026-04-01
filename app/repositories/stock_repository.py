from sqlalchemy.orm import Session
from app.models.stock import StockFeature, StockPrice
from sqlalchemy import func
from datetime import date, timedelta


class StockJoinedRow:
    def __init__(self, price: StockPrice, feature: StockFeature):
        self.symbol = price.symbol
        self.date = price.date
        self.open = price.open
        self.close = price.close
        self.high = price.high
        self.low = price.low
        self.volume = price.volume

        self.daily_return = feature.daily_return
        self.ma7 = feature.ma7
        self.ma30 = feature.ma30
        self.momentum_7d = feature.momentum_7d
        self.range_pct = feature.range_pct
        self.trend_strength = feature.trend_strength
        self.drawdown = feature.drawdown
        self.sharpe_like_30 = feature.sharpe_like_30
        self.high_52w = feature.high_52w
        self.low_52w = feature.low_52w
        self.volatility = feature.volatility

def get_all_companies(db: Session):
    return db.query(StockPrice.symbol).distinct().order_by(StockPrice.symbol.asc()).all()

def get_stock_data(db: Session, symbol: str, days: int = 30):
    return get_stock_data_filtered(db, symbol, days=days)


def get_stock_data_filtered(
    db: Session,
    symbol: str,
    days: int = 30,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: str = "date",
    order: str = "desc",
):
    sortable_columns = {
        "date": StockPrice.date,
        "open": StockPrice.open,
        "close": StockPrice.close,
        "high": StockPrice.high,
        "low": StockPrice.low,
        "volume": StockPrice.volume,
        "daily_return": StockFeature.daily_return,
        "ma7": StockFeature.ma7,
        "ma30": StockFeature.ma30,
        "momentum_7d": StockFeature.momentum_7d,
        "range_pct": StockFeature.range_pct,
        "trend_strength": StockFeature.trend_strength,
        "drawdown": StockFeature.drawdown,
        "sharpe_like_30": StockFeature.sharpe_like_30,
        "volatility": StockFeature.volatility,
    }

    sort_column = sortable_columns.get(sort_by, StockPrice.date)
    base_query = (
        db.query(StockPrice, StockFeature)
        .join(
            StockFeature,
            (StockPrice.symbol == StockFeature.symbol) & (StockPrice.date == StockFeature.date),
        )
        .filter(StockPrice.symbol == symbol)
    )

    if start_date:
        base_query = base_query.filter(StockPrice.date >= start_date)
    if end_date:
        base_query = base_query.filter(StockPrice.date <= end_date)

    # Correct semantics: get latest N records by date first, then sort that window.
    latest_rows = base_query.order_by(StockPrice.date.desc()).limit(days).all()
    joined_rows = [StockJoinedRow(price, feature) for price, feature in latest_rows]
    reverse = order == "desc"
    return sorted(joined_rows, key=lambda r: getattr(r, sort_by, r.date), reverse=reverse)

def get_stock_summary(db: Session, symbol: str):
    one_year_ago = date.today() - timedelta(days=365)
    return (
        db.query(
            func.max(StockPrice.high).label("high_52w"),
            func.min(StockPrice.low).label("low_52w"),
            func.avg(StockPrice.close).label("avg_close"),
        )
        .filter(StockPrice.symbol == symbol)
        .filter(StockPrice.date >= one_year_ago)
        .first()
    )


def get_symbol_price_window(db: Session, symbol: str, days: int = 30):
    rows = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol)
        .order_by(StockPrice.date.desc())
        .limit(days)
        .all()
    )
    return list(reversed(rows))


def get_latest_stock_point(db: Session, symbol: str):
    row = (
        db.query(StockPrice, StockFeature)
        .join(
            StockFeature,
            (StockPrice.symbol == StockFeature.symbol) & (StockPrice.date == StockFeature.date),
        )
        .filter(StockPrice.symbol == symbol)
        .order_by(StockPrice.date.desc())
        .first()
    )
    if not row:
        return None
    return StockJoinedRow(row[0], row[1])


def get_top_movers(db: Session, limit: int = 5, ascending: bool = False):
    latest_by_symbol = (
        db.query(StockFeature.symbol.label("symbol"), func.max(StockFeature.date).label("max_date"))
        .group_by(StockFeature.symbol)
        .subquery()
    )

    order_column = StockFeature.daily_return.asc() if ascending else StockFeature.daily_return.desc()

    return (
        db.query(StockFeature.symbol, StockFeature.date, StockFeature.daily_return, StockPrice.close)
        .join(
            latest_by_symbol,
            (StockFeature.symbol == latest_by_symbol.c.symbol)
            & (StockFeature.date == latest_by_symbol.c.max_date),
        )
        .join(
            StockPrice,
            (StockPrice.symbol == StockFeature.symbol)
            & (StockPrice.date == StockFeature.date),
        )
        .filter(StockFeature.daily_return.isnot(None))
        .order_by(order_column)
        .limit(limit)
        .all()
    )


def get_symbol_close_window(db: Session, symbol: str, days: int = 60):
    rows = (
        db.query(StockPrice.date, StockPrice.close)
        .filter(StockPrice.symbol == symbol)
        .order_by(StockPrice.date.desc())
        .limit(days)
        .all()
    )
    return list(reversed(rows))