from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class StockDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    date: date
    open: float
    close: float
    high: float
    low: float
    volume: int
    # Derived metrics are nullable for warm-up windows and sparse history.
    daily_return: Optional[float] = Field(default=None, description="Nullable derived metric")
    ma7: Optional[float] = Field(default=None, description="Nullable derived metric")
    ma30: Optional[float] = Field(default=None, description="Nullable derived metric")
    momentum_7d: Optional[float] = Field(default=None, description="Nullable derived metric")
    range_pct: Optional[float] = Field(default=None, description="Nullable derived metric")
    trend_strength: Optional[float] = Field(default=None, description="Nullable derived metric")
    drawdown: Optional[float] = Field(default=None, description="Nullable derived metric")
    sharpe_like_30: Optional[float] = Field(default=None, description="Nullable derived metric")
    high_52w: Optional[float] = Field(default=None, description="Nullable derived metric")
    low_52w: Optional[float] = Field(default=None, description="Nullable derived metric")
    volatility: Optional[float] = Field(default=None, description="Nullable derived metric")


class CompaniesResponse(BaseModel):
    total: int
    companies: list[str]


class StockDataQueryMeta(BaseModel):
    days: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sort_by: str
    order: Literal["asc", "desc"]


class StockDataListResponse(BaseModel):
    symbol: str
    count: int
    query: StockDataQueryMeta
    data: list[StockDataResponse]


class StockSummaryResponse(BaseModel):
    symbol: str
    high_52w: float
    low_52w: float
    avg_close: float


class StockComparisonResponse(BaseModel):
    symbol: str
    start_close: float
    end_close: float
    pct_change: float


class CompareStocksResponse(BaseModel):
    symbol1: StockComparisonResponse
    symbol2: StockComparisonResponse
    winner_symbol: str
    spread_pct: float


class StockMoverResponse(BaseModel):
    symbol: str
    date: date
    daily_return: float
    close: float


class TopMoversResponse(BaseModel):
    type: Literal["gainers", "losers"]
    count: int
    data: list[StockMoverResponse]


class StockSignalResponse(BaseModel):
    symbol: str
    date: date
    close: float
    ma7: Optional[float] = None
    signal: Literal["BUY", "SELL", "HOLD"]


class StockPredictionResponse(BaseModel):
    symbol: str
    model: Literal["linear", "ma", "arima"]
    days_used: int
    horizon: int
    predicted_close: float
    slope: float
    trend: Literal["UP", "DOWN", "FLAT"]


class StockExplanationResponse(BaseModel):
    symbol: str
    date: date
    signal: Literal["BUY", "SELL", "HOLD"]
    trend: Literal["UP", "DOWN", "FLAT"]
    volatility_band: Literal["LOW", "MEDIUM", "HIGH"]
    drawdown_pct: Optional[float] = None
    summary: str
    explanation: str


class StockAIExplanationResponse(BaseModel):
    symbol: str
    provider: Literal["gemini", "fallback"]
    model: str
    analysis: str
    fallback_used: bool
    fallback_reason: Optional[str] = None


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class StockAIChatRequest(BaseModel):
    message: str
    history: list[AIChatMessage] = Field(default_factory=list)
    conversation_summary: Optional[str] = None


class StockAIChatResponse(BaseModel):
    symbol: str
    provider: Literal["gemini", "fallback"]
    model: str
    reply: str
    fallback_used: bool
    fallback_reason: Optional[str] = None
    context_window_used: int
    conversation_summary: Optional[str] = None


class SearchCompanyResponse(BaseModel):
    symbol: str
    name: str


class PipelineRunResponse(BaseModel):
    symbol: str
    rows_loaded: int
    cleaning: Literal["standard", "aggressive", "minimal"]
    source: Literal["yfinance", "csv", "yahoo", "alpha_vantage"]