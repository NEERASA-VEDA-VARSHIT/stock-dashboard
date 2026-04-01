export interface StockData {
  symbol: string;
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  daily_return?: number;
  ma7?: number;
  ma30?: number;
  momentum_7d?: number;
  range_pct?: number;
  trend_strength?: number;
  drawdown?: number;
  sharpe_like_30?: number;
  high_52w?: number;
  low_52w?: number;
  volatility?: number;
}

export interface CompaniesResponse {
  total: number;
  companies: string[];
}

export interface StockQueryMeta {
  days: number;
  start_date?: string | null;
  end_date?: string | null;
  sort_by: string;
  order: "asc" | "desc";
}

export interface StockResponse {
  symbol: string;
  count: number;
  query: StockQueryMeta;
  data: StockData[];
}

export interface StockComparison {
  symbol: string;
  start_close: number;
  end_close: number;
  pct_change: number;
}

export interface CompareResponse {
  symbol1: StockComparison;
  symbol2: StockComparison;
  winner_symbol: string;
  spread_pct: number;
}

export interface TopMover {
  symbol: string;
  date: string;
  daily_return: number;
  close: number;
}

export interface TopMoversResponse {
  type: "gainers" | "losers";
  count: number;
  data: TopMover[];
}

export interface SignalResponse {
  symbol: string;
  date: string;
  close: number;
  ma7?: number | null;
  signal: "BUY" | "SELL" | "HOLD";
}

export interface SummaryResponse {
  symbol: string;
  high_52w: number;
  low_52w: number;
  avg_close: number;
}

export interface PredictionResponse {
  symbol: string;
  model: "linear" | "ma" | "arima";
  days_used: number;
  horizon: number;
  predicted_close: number;
  slope: number;
  trend: "UP" | "DOWN" | "FLAT";
}

export interface SearchCompanyResponse {
  symbol: string;
  name: string;
}

export interface PipelineRunResponse {
  symbol: string;
  rows_loaded: number;
  cleaning: "standard" | "aggressive" | "minimal";
  source: "yfinance" | "csv" | "yahoo" | "alpha_vantage";
}

export interface AIExplanationResponse {
  symbol: string;
  provider: "gemini" | "fallback";
  model: string;
  analysis: string;
  fallback_used: boolean;
  fallback_reason?: string | null;
}

export interface ExplanationResponse {
  symbol: string;
  date: string;
  signal: "BUY" | "SELL" | "HOLD";
  trend: "UP" | "DOWN" | "FLAT";
  volatility_band: "LOW" | "MEDIUM" | "HIGH";
  drawdown_pct?: number | null;
  summary: string;
  explanation: string;
}

export interface AIChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AIChatRequest {
  message: string;
  history?: AIChatMessage[];
  conversation_summary?: string | null;
}

export interface AIChatResponse {
  symbol: string;
  provider: "gemini" | "fallback";
  model: string;
  reply: string;
  fallback_used: boolean;
  fallback_reason?: string | null;
  context_window_used: number;
  conversation_summary?: string | null;
}
