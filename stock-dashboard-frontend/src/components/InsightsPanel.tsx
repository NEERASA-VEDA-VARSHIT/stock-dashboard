"use client";

import { PredictionResponse, SignalResponse, StockResponse } from "@/types/stock";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface InsightsPanelProps {
  symbol: string | null;
  signal: SignalResponse | null;
  prediction: PredictionResponse | null;
  stockData: StockResponse | null;
}

function computeVolatilityLabel(stockData: StockResponse | null): string {
  if (!stockData || stockData.data.length === 0) {
    return "N/A";
  }

  const latest = stockData.data.reduce((acc, row) => {
    if (!acc) {
      return row;
    }
    return new Date(row.date) > new Date(acc.date) ? row : acc;
  }, stockData.data[0]);

  const v = latest.volatility ?? null;
  if (v === null) {
    return "N/A";
  }
  if (v < 0.01) {
    return "LOW";
  }
  if (v < 0.02) {
    return "MEDIUM";
  }
  return "HIGH";
}

function predictionPct(stockData: StockResponse | null, prediction: PredictionResponse | null): string {
  if (!stockData || !prediction || stockData.data.length === 0) {
    return "N/A";
  }

  const latest = stockData.data.reduce((acc, row) => {
    if (!acc) {
      return row;
    }
    return new Date(row.date) > new Date(acc.date) ? row : acc;
  }, stockData.data[0]);

  if (!latest.close) {
    return "N/A";
  }

  const pct = ((prediction.predicted_close - latest.close) / latest.close) * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
}

export default function InsightsPanel({
  symbol,
  signal,
  prediction,
  stockData,
}: InsightsPanelProps) {
  const volatility = computeVolatilityLabel(stockData);
  const predPct = predictionPct(stockData, prediction);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Insights</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>Symbol</span>
            <span>{symbol ?? "N/A"}</span>
          </div>
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>Signal</span>
            <Badge
              variant={
                signal?.signal === "BUY"
                  ? "success"
                  : signal?.signal === "SELL"
                    ? "danger"
                    : "secondary"
              }
            >
              {signal?.signal ?? "N/A"}
            </Badge>
          </div>
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>Volatility</span>
            <Badge
              variant={
                volatility === "LOW"
                  ? "success"
                  : volatility === "MEDIUM"
                    ? "warning"
                    : volatility === "HIGH"
                      ? "danger"
                      : "secondary"
              }
            >
              {volatility}
            </Badge>
          </div>
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>Trend</span>
            <span>{prediction?.trend ?? "N/A"}</span>
          </div>
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>Prediction</span>
            <span>{predPct}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
