"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { mutate } from "swr";

import CompanyList from "@/components/CompanyList";
import StockChart from "@/components/StockChart";
import InsightsPanel from "@/components/InsightsPanel";
import AIChatPanel from "@/components/AIChatPanel";
import ThemeToggle from "@/components/ThemeToggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import Spinner from "@/components/ui/spinner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getAIExplanation,
  getCompanies,
  getPrediction,
  getSignal,
  getStockData,
  getTopGainers,
  getTopLosers,
  runPipeline,
  searchStocks,
  uploadCsv,
} from "@/lib/api";

const RANGE_OPTIONS = [
  { label: "30D", value: 30 },
  { label: "90D", value: 90 },
  { label: "1Y", value: 365 },
];

export default function Home() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [days, setDays] = useState<number>(30);
  const [sortBy, setSortBy] = useState<"date" | "close">("date");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [predictionModel, setPredictionModel] = useState<"linear" | "ma" | "arima">("linear");
  const [forecastHorizon, setForecastHorizon] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [uploadSymbol, setUploadSymbol] = useState<string>("INFY");
  const [uploadCleaning, setUploadCleaning] = useState<"standard" | "aggressive" | "minimal">("standard");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const { data: companiesRes, error: companiesErr } = useSWR("companies", getCompanies);
  const { data: gainers } = useSWR("top-gainers", () => getTopGainers(5));
  const { data: losers } = useSWR("top-losers", () => getTopLosers(5));

  const { data: stockData, error: stockErr, isLoading: stockLoading } = useSWR(
    selectedCompany ? ["stock-data", selectedCompany, days, sortBy, order] : null,
    ([, symbol, d, s, o]) => getStockData(symbol as string, d as number, s as "date" | "close", o as "asc" | "desc"),
  );

  const { data: signal, error: signalErr } = useSWR(
    selectedCompany ? ["signal", selectedCompany] : null,
    ([, symbol]) => getSignal(symbol as string),
  );

  const { data: prediction, error: predictionErr } = useSWR(
    selectedCompany ? ["prediction", selectedCompany, days, predictionModel, forecastHorizon] : null,
    ([, symbol, d, model, horizon]) =>
      getPrediction(symbol as string, Math.max(d as number, 30), horizon as number, model as "linear" | "ma" | "arima"),
  );

  const { data: aiExplanation, error: aiErr } = useSWR(
    selectedCompany ? ["ai-explain", selectedCompany, predictionModel, forecastHorizon, days] : null,
    ([, symbol, model, horizon, d]) =>
      getAIExplanation(
        symbol as string,
        model as "linear" | "ma" | "arima",
        horizon as number,
        Math.max(d as number, 30),
      ),
  );

  const { data: suggestions, error: searchErr } = useSWR(
    searchQuery.trim().length >= 2 ? ["search", searchQuery.trim()] : null,
    ([, q]) => searchStocks(q as string),
  );

  const coreLoading = !selectedCompany || stockLoading || !signal || !prediction || !aiExplanation;

  const normalizedManualSymbol = useMemo(() => {
    const raw = searchQuery.trim().toUpperCase();
    if (!raw) {
      return "";
    }
    return raw;
  }, [searchQuery]);

  const mergedSuggestions = useMemo(() => {
    const q = searchQuery.trim().toUpperCase();
    const fromApi = suggestions ?? [];
    const local = (companiesRes?.companies ?? [])
      .filter((symbol) => symbol.toUpperCase().includes(q))
      .map((symbol) => ({ symbol, name: "Already in dashboard" }));

    const seen = new Set<string>();
    return [...fromApi, ...local].filter((item) => {
      const key = item.symbol.toUpperCase();
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }, [suggestions, companiesRes, searchQuery]);

  useEffect(() => {
    if (!companiesRes || companiesRes.companies.length === 0) {
      return;
    }

    if (!selectedCompany) {
      setSelectedCompany(companiesRes.companies[0]);
      setUploadSymbol(companiesRes.companies[0]);
    }
  }, [companiesRes, selectedCompany]);

  useEffect(() => {
    const firstErr = companiesErr || stockErr || signalErr || predictionErr || aiErr;
    if (firstErr) {
      setError(firstErr instanceof Error ? firstErr.message : "Failed to load dashboard data");
    } else {
      setError(null);
    }
  }, [companiesErr, stockErr, signalErr, predictionErr, aiErr]);

  async function handleSuggestionClick(symbol: string) {
    try {
      setIsIngesting(true);
      await runPipeline(symbol, "standard");
      await Promise.all([
        mutate("companies"),
        mutate("top-gainers"),
        mutate("top-losers"),
      ]);
      setSelectedCompany(symbol);
      setUploadSymbol(symbol);
      setSearchQuery("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to ingest selected symbol");
    } finally {
      setIsIngesting(false);
    }
  }

  async function handleCsvUpload() {
    if (!uploadFile) {
      setUploadStatus("Please choose a CSV file first.");
      return;
    }

    try {
      setIsUploading(true);
      const res = await uploadCsv(uploadFile, uploadSymbol, uploadCleaning);
      setUploadStatus(`Uploaded ${res.rows_loaded} rows for ${res.symbol} (${res.cleaning})`);
      await Promise.all([
        mutate("companies"),
        mutate("top-gainers"),
        mutate("top-losers"),
      ]);
      setSelectedCompany(res.symbol);
      setUploadFile(null);
    } catch (e) {
      setUploadStatus(e instanceof Error ? e.message : "CSV upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  const trendBadge = useMemo<"success" | "danger" | "warning" | "secondary">(() => {
    if (!prediction) {
      return "secondary";
    }
    if (prediction.trend === "UP") {
      return "success";
    }
    if (prediction.trend === "DOWN") {
      return "danger";
    }
    return "warning";
  }, [prediction]);

  return (
    <div>
      <div className="min-h-screen bg-[radial-gradient(circle_at_10%_20%,#cffafe_0%,#f8fafc_45%,#f1f5f9_100%)] text-slate-900 transition-colors duration-300 dark:bg-[radial-gradient(circle_at_20%_20%,#0f172a_0%,#020617_70%)] dark:text-slate-100">
        <header className="flex items-center justify-between px-4 py-4 md:px-8">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Stock Intelligence Dashboard</h1>
            <p className="text-sm text-slate-500 dark:text-slate-300">Full-stack analytics on top of your FastAPI backend</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/compare">
              <Button variant="outline" size="sm">Compare Studio</Button>
            </Link>
            <ThemeToggle />
          </div>
        </header>

        <div className="relative px-4 md:px-8">
          <div className="mx-auto max-w-3xl">
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Yahoo symbols (e.g. INFY, TCS, RELIANCE)"
            />
            {isIngesting ? (
              <p className="mt-2 text-xs text-cyan-500">Ingesting selected symbol...</p>
            ) : null}
            {searchErr && searchQuery.trim().length >= 2 ? (
              <p className="mt-2 text-xs text-amber-600 dark:text-amber-300">
                Yahoo suggestions are temporarily rate-limited. Use local matches or ingest typed symbol.
              </p>
            ) : null}
            {searchQuery.trim().length >= 2 ? (
              <div className="mt-2 flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isIngesting || !normalizedManualSymbol}
                  onClick={() => handleSuggestionClick(normalizedManualSymbol)}
                >
                  {isIngesting ? "Ingesting..." : `Ingest ${normalizedManualSymbol || "symbol"}`}
                </Button>
              </div>
            ) : null}
            {mergedSuggestions.length > 0 && searchQuery.trim().length >= 2 ? (
              <div className="absolute z-40 mt-1 w-full max-w-3xl rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
                {mergedSuggestions.slice(0, 8).map((item) => (
                  <button
                    key={item.symbol}
                    onClick={() => handleSuggestionClick(item.symbol)}
                    className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <span>{item.symbol}</span>
                    <span className="text-xs text-slate-500">{item.name}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        <main className="grid grid-cols-1 gap-4 p-4 md:grid-cols-[280px_1fr_360px] md:gap-5 md:p-5">
          <CompanyList companies={companiesRes?.companies ?? []} selected={selectedCompany} onSelect={setSelectedCompany} />

          <section className="space-y-4">
            <Card className="bg-white/70 dark:bg-slate-950/60">
              <CardContent className="flex flex-wrap items-center gap-2 p-3">
              {RANGE_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  onClick={() => setDays(option.value)}
                  size="sm"
                  variant={days === option.value ? "default" : "secondary"}
                >
                  {option.label}
                </Button>
              ))}

              <Select value={sortBy} onValueChange={(value) => setSortBy(value as "date" | "close")}>
                <SelectTrigger className="w-32.5 rounded-full">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Sort: Date</SelectItem>
                  <SelectItem value="close">Sort: Close</SelectItem>
                </SelectContent>
              </Select>

              <Button
                size="sm"
                variant="outline"
                onClick={() => setOrder((prev) => (prev === "desc" ? "asc" : "desc"))}
              >
                Order: {order.toUpperCase()}
              </Button>
              {stockLoading ? <Spinner label="Loading prices" /> : null}
              </CardContent>
            </Card>

            {error ? (
              <div className="rounded-lg border border-rose-300 bg-rose-50 p-3 text-sm text-rose-600 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                {error}
              </div>
            ) : null}

            {coreLoading ? <Spinner label="Loading insights" /> : null}
            <StockChart data={stockData ?? null} prediction={prediction ?? null} />

            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Top Gainers</h3>
                <ul className="space-y-2 text-sm">
                  {gainers?.data.map((row) => (
                    <li key={`g-${row.symbol}`} className="flex justify-between rounded-md bg-emerald-50 px-3 py-2 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                      <span>{row.symbol}</span>
                      <span>{(row.daily_return * 100).toFixed(2)}%</span>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Top Losers</h3>
                <ul className="space-y-2 text-sm">
                  {losers?.data.map((row) => (
                    <li key={`l-${row.symbol}`} className="flex justify-between rounded-md bg-rose-50 px-3 py-2 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                      <span>{row.symbol}</span>
                      <span>{(row.daily_return * 100).toFixed(2)}%</span>
                    </li>
                  ))}
                </ul>
              </Card>
            </div>
          </section>

          <aside className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-xs uppercase tracking-[0.2em] text-slate-500">Prediction Snapshot</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <Select value={predictionModel} onValueChange={(value) => setPredictionModel(value as "linear" | "ma" | "arima")}>
                    <SelectTrigger>
                      <SelectValue placeholder="Model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="linear">linear</SelectItem>
                      <SelectItem value="ma">ma</SelectItem>
                      <SelectItem value="arima">arima</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={String(forecastHorizon)} onValueChange={(value) => setForecastHorizon(Number(value))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Horizon" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 day</SelectItem>
                      <SelectItem value="3">3 days</SelectItem>
                      <SelectItem value="5">5 days</SelectItem>
                      <SelectItem value="7">7 days</SelectItem>
                      <SelectItem value="14">14 days</SelectItem>
                      <SelectItem value="30">30 days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <p className="text-2xl font-semibold">{prediction?.predicted_close ?? "--"}</p>
                <Badge variant={trendBadge}>Trend: {prediction?.trend ?? "N/A"}</Badge>
                <p className="text-xs text-slate-500 dark:text-slate-300">
                  Model: {predictionModel} | Forecast horizon: {forecastHorizon}d
                </p>
              </CardContent>
            </Card>

            <InsightsPanel
              symbol={selectedCompany}
              signal={signal ?? null}
              prediction={prediction ?? null}
              stockData={stockData ?? null}
            />

            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">AI Insights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
                  <span>Provider</span>
                  <Badge variant={aiExplanation?.provider === "gemini" ? "success" : "secondary"}>
                    {aiExplanation?.provider ?? "N/A"}
                  </Badge>
                </div>
                <div className="rounded-md bg-slate-100 px-3 py-2 text-slate-700 dark:bg-slate-900 dark:text-slate-200">
                  <p className="whitespace-pre-wrap">{aiExplanation?.analysis ?? "AI explanation unavailable"}</p>
                </div>
                {aiExplanation?.fallback_used && aiExplanation.fallback_reason ? (
                  <p className="text-xs text-amber-600 dark:text-amber-300">
                    Fallback reason: {aiExplanation.fallback_reason}
                  </p>
                ) : null}
              </CardContent>
            </Card>

            <AIChatPanel symbol={selectedCompany} initialInsight={aiExplanation ?? null} />

            <Card>
              <CardHeader>
                <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">CSV Ingestion</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  value={uploadSymbol}
                  onChange={(e) => setUploadSymbol(e.target.value.toUpperCase())}
                  placeholder="Symbol e.g. INFY or AAPL"
                />

                <Select value={uploadCleaning} onValueChange={(value) => setUploadCleaning(value as "standard" | "aggressive" | "minimal")}>
                  <SelectTrigger>
                    <SelectValue placeholder="Cleaning strategy" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">standard</SelectItem>
                    <SelectItem value="aggressive">aggressive</SelectItem>
                    <SelectItem value="minimal">minimal</SelectItem>
                  </SelectContent>
                </Select>

                <Input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                />

                <Button onClick={handleCsvUpload} disabled={isUploading || !uploadFile} className="w-full">
                  {isUploading ? "Uploading..." : "Upload and Ingest CSV"}
                </Button>

                {uploadStatus ? (
                  <p className="text-xs text-slate-500 dark:text-slate-300">{uploadStatus}</p>
                ) : null}
              </CardContent>
            </Card>
          </aside>
        </main>
      </div>
    </div>
  );
}
