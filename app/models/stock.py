from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint, desc
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_stock_prices_symbol_date"),
        Index("idx_stock_prices_symbol_date", "symbol", "date"),
        Index("idx_stock_prices_symbol_date_desc", "symbol", desc("date")),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)

    # Raw, immutable market truth.
    open = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    features = relationship("StockFeature", back_populates="price", uselist=False)


class StockFeature(Base):
    __tablename__ = "stock_features"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_stock_features_symbol_date"),
        ForeignKeyConstraint(
            ["symbol", "date"],
            ["stock_prices.symbol", "stock_prices.date"],
            name="fk_stock_features_price_symbol_date",
            ondelete="CASCADE",
        ),
        Index("idx_stock_features_symbol_date", "symbol", "date"),
        Index("idx_stock_features_date_daily_return", "date", "daily_return"),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)

    # Derived and recomputable features.
    daily_return = Column(Float)
    ma7 = Column(Float)
    ma30 = Column(Float)
    momentum_7d = Column(Float)
    range_pct = Column(Float)
    trend_strength = Column(Float)
    drawdown = Column(Float)
    sharpe_like_30 = Column(Float)
    high_52w = Column(Float)
    low_52w = Column(Float)
    volatility = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    price = relationship("StockPrice", back_populates="features")