import {
  AIChatRequest,
  AIChatResponse,
  AIExplanationResponse,
  CompaniesResponse,
  CompareResponse,
  PipelineRunResponse,
  PredictionResponse,
  SearchCompanyResponse,
  SignalResponse,
  StockResponse,
  TopMoversResponse,
} from "@/types/stock";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api/v1";
const INGEST_ADMIN_KEY = process.env.NEXT_PUBLIC_INGEST_ADMIN_KEY;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return (await res.json()) as T;
}

export function getCompanies() {
  return request<CompaniesResponse>("/stocks/companies");
}

export function getStockData(
  symbol: string,
  days: number,
  sortBy: "date" | "close" = "date",
  order: "asc" | "desc" = "desc",
) {
  return request<StockResponse>(
    `/stocks/${encodeURIComponent(symbol)}/data?days=${days}&sort_by=${sortBy}&order=${order}`,
  );
}

export function getSignal(symbol: string) {
  return request<SignalResponse>(`/stocks/${encodeURIComponent(symbol)}/signal`);
}

export function getPrediction(
  symbol: string,
  days = 60,
  horizon = 1,
  model: "linear" | "ma" | "arima" = "linear",
) {
  return request<PredictionResponse>(
    `/stocks/${encodeURIComponent(symbol)}/predict?days=${days}&horizon=${horizon}&model=${model}`,
  );
}

export function getAIExplanation(
  symbol: string,
  model: "linear" | "ma" | "arima" = "linear",
  horizon = 1,
  days = 60,
) {
  return request<AIExplanationResponse>(
    `/stocks/${encodeURIComponent(symbol)}/ai-explain?model=${model}&horizon=${horizon}&days=${days}`,
  );
}

export function chatWithAI(symbol: string, payload: AIChatRequest) {
  return request<AIChatResponse>(`/stocks/${encodeURIComponent(symbol)}/ai-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getTopGainers(limit = 5) {
  return request<TopMoversResponse>(`/stocks/top-gainers?limit=${limit}`);
}

export function getTopLosers(limit = 5) {
  return request<TopMoversResponse>(`/stocks/top-losers?limit=${limit}`);
}

export function compareStocks(symbol1: string, symbol2: string, days: number) {
  return request<CompareResponse>(
    `/stocks/compare?symbol1=${encodeURIComponent(symbol1)}&symbol2=${encodeURIComponent(symbol2)}&days=${days}`,
  );
}

export function searchStocks(query: string) {
  return request<SearchCompanyResponse[]>(`/stocks/search?q=${encodeURIComponent(query)}`);
}

export function runPipeline(symbol: string, cleaning: "standard" | "aggressive" | "minimal" = "standard") {
  const headers = INGEST_ADMIN_KEY ? { "x-admin-key": INGEST_ADMIN_KEY } : undefined;
  return request<PipelineRunResponse>(
    `/stocks/pipeline/run?symbol=${encodeURIComponent(symbol)}&cleaning=${cleaning}`,
    { method: "POST", headers },
  );
}

export async function uploadCsv(
  file: File,
  symbol: string,
  cleaning: "standard" | "aggressive" | "minimal" = "standard",
) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${BASE_URL}/stocks/upload?symbol=${encodeURIComponent(symbol)}&cleaning=${cleaning}`,
    {
      method: "POST",
      headers: INGEST_ADMIN_KEY ? { "x-admin-key": INGEST_ADMIN_KEY } : undefined,
      body: formData,
    },
  );

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }

  return (await res.json()) as PipelineRunResponse;
}
