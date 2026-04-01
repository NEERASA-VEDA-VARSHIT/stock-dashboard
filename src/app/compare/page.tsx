"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import useSWR from "swr";
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";

import { compareStocks, getCompanies, getStockData } from "@/lib/api";
import { CompareResponse } from "@/types/stock";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Spinner from "@/components/ui/spinner";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
);

const RANGE_OPTIONS = [7, 14, 30, 60, 90];

function pct(value: number): string {
  return `${value.toFixed(2)}%`;
}

export default function ComparePage() {
  const { data: companiesRes, isLoading, error } = useSWR("companies", getCompanies);
  const companies = companiesRes?.companies ?? [];

  const [symbol1, setSymbol1] = useState<string>("");
  const [symbol2, setSymbol2] = useState<string>("");
  const [days, setDays] = useState<number>(30);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loadingCompare, setLoadingCompare] = useState<boolean>(false);
  const [compareError, setCompareError] = useState<string>("");

  const { data: stockData1, isLoading: loadingData1 } = useSWR(
    symbol1 ? ["compare-data", symbol1, days] : null,
    ([, symbol, windowDays]) => getStockData(symbol as string, windowDays as number, "date", "desc"),
  );

  const { data: stockData2, isLoading: loadingData2 } = useSWR(
    symbol2 ? ["compare-data", symbol2, days] : null,
    ([, symbol, windowDays]) => getStockData(symbol as string, windowDays as number, "date", "desc"),
  );

  const canCompare = !!symbol1 && !!symbol2 && symbol1 !== symbol2 && !loadingCompare;

  const winnerPct = useMemo(() => {
    if (!result) {
      return 0;
    }
    return result.winner_symbol === result.symbol1.symbol
      ? result.symbol1.pct_change
      : result.symbol2.pct_change;
  }, [result]);

  const chartPayload = useMemo(() => {
    if (!stockData1 || !stockData2 || stockData1.data.length === 0 || stockData2.data.length === 0) {
      return null;
    }

    const s1 = [...stockData1.data].reverse();
    const s2 = [...stockData2.data].reverse();
    const minLen = Math.min(s1.length, s2.length);
    const aligned1 = s1.slice(-minLen);
    const aligned2 = s2.slice(-minLen);
    const labels = aligned1.map((p) => new Date(p.date).toLocaleDateString());
    const close1 = aligned1.map((p) => p.close);
    const close2 = aligned2.map((p) => p.close);

    const base1 = close1[0] || 1;
    const base2 = close2[0] || 1;
    const normalized1 = close1.map((v) => ((v / base1) - 1) * 100);
    const normalized2 = close2.map((v) => ((v / base2) - 1) * 100);

    return {
      labels,
      close1,
      close2,
      normalized1,
      normalized2,
    };
  }, [stockData1, stockData2]);

  async function runCompare() {
    if (!canCompare) {
      return;
    }
    try {
      setLoadingCompare(true);
      setCompareError("");
      const payload = await compareStocks(symbol1, symbol2, days);
      setResult(payload);
    } catch (e) {
      setCompareError(e instanceof Error ? e.message : "Compare request failed");
    } finally {
      setLoadingCompare(false);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_10%_20%,#cffafe_0%,#f8fafc_45%,#f1f5f9_100%)] p-4 text-slate-900 md:p-8 dark:bg-[radial-gradient(circle_at_20%_20%,#0f172a_0%,#020617_70%)] dark:text-slate-100">
      <div className="mx-auto max-w-5xl space-y-5">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Compare Stocks</h1>
            <p className="text-sm text-slate-500 dark:text-slate-300">Dedicated compare workspace with clearer winner analytics.</p>
          </div>
          <Link href="/">
            <Button variant="outline" size="sm">Back to Dashboard</Button>
          </Link>
        </header>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Setup</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? <Spinner label="Loading symbols" /> : null}
            {error ? <p className="text-sm text-rose-600 dark:text-rose-300">Failed to load symbols.</p> : null}

            <div className="grid gap-3 md:grid-cols-2">
              <Select value={symbol1} onValueChange={setSymbol1}>
                <SelectTrigger>
                  <SelectValue placeholder="Select first symbol" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((symbol) => (
                    <SelectItem key={`c1-${symbol}`} value={symbol}>
                      {symbol}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={symbol2} onValueChange={setSymbol2}>
                <SelectTrigger>
                  <SelectValue placeholder="Select second symbol" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((symbol) => (
                    <SelectItem key={`c2-${symbol}`} value={symbol}>
                      {symbol}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-wrap gap-2">
              {RANGE_OPTIONS.map((value) => (
                <Button
                  key={value}
                  size="sm"
                  variant={days === value ? "default" : "secondary"}
                  onClick={() => setDays(value)}
                >
                  {value}D
                </Button>
              ))}
            </div>

            <Button onClick={runCompare} disabled={!canCompare} className="w-full md:w-auto">
              {loadingCompare ? "Comparing..." : `Compare (${days}D)`}
            </Button>
            {compareError ? <p className="text-sm text-rose-600 dark:text-rose-300">{compareError}</p> : null}
            {!result && !compareError ? <p className="text-sm text-slate-500">Select two symbols and run compare.</p> : null}
          </CardContent>
        </Card>

        {result ? (
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Result</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
                  <span>{result.symbol1.symbol}</span>
                  <span>{pct(result.symbol1.pct_change)}</span>
                </div>
                <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
                  <span>{result.symbol2.symbol}</span>
                  <span>{pct(result.symbol2.pct_change)}</span>
                </div>
                <div className="flex items-center justify-between rounded-md bg-emerald-50 px-3 py-2 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                  <span>Winner: {result.winner_symbol}</span>
                  <Badge variant="success">Spread {pct(result.spread_pct)}</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Performance Snapshot</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p className="text-slate-500 dark:text-slate-300">Winner return over selected window</p>
                <p className="text-3xl font-semibold">{pct(winnerPct)}</p>
                <div className="h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className="h-full bg-cyan-500"
                    style={{ width: `${Math.min(Math.abs(winnerPct) * 4, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-300">
                  Width is scaled for visibility and does not represent absolute risk.
                </p>
              </CardContent>
            </Card>
          </div>
        ) : null}

        {symbol1 && symbol2 && (loadingData1 || loadingData2) ? <Spinner label="Loading chart data" /> : null}

        {chartPayload ? (
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Normalized Performance (%)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <Line
                    data={{
                      labels: chartPayload.labels,
                      datasets: [
                        {
                          label: symbol1,
                          data: chartPayload.normalized1,
                          borderColor: "#06b6d4",
                          backgroundColor: "rgba(6,182,212,0.12)",
                          borderWidth: 2,
                          pointRadius: 0,
                          tension: 0.3,
                        },
                        {
                          label: symbol2,
                          data: chartPayload.normalized2,
                          borderColor: "#f97316",
                          backgroundColor: "rgba(249,115,22,0.12)",
                          borderWidth: 2,
                          pointRadius: 0,
                          tension: 0.3,
                        },
                      ],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: true } },
                    }}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Close Price Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <Line
                    data={{
                      labels: chartPayload.labels,
                      datasets: [
                        {
                          label: symbol1,
                          data: chartPayload.close1,
                          borderColor: "#0891b2",
                          borderWidth: 2,
                          pointRadius: 0,
                          tension: 0.3,
                        },
                        {
                          label: symbol2,
                          data: chartPayload.close2,
                          borderColor: "#ea580c",
                          borderWidth: 2,
                          pointRadius: 0,
                          tension: 0.3,
                        },
                      ],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: true } },
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </div>
  );
}
