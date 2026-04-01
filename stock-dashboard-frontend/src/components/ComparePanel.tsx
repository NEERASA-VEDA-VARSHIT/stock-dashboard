"use client";

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

interface ComparePanelProps {
  companies: string[];
  symbol1: string | null;
  symbol2: string | null;
  days: number;
  onSymbol1Change: (value: string) => void;
  onSymbol2Change: (value: string) => void;
  onCompare: () => void;
  loading: boolean;
  result: CompareResponse | null;
}

function formatPct(value: number): string {
  return `${value.toFixed(2)}%`;
}

export default function ComparePanel({
  companies,
  symbol1,
  symbol2,
  days,
  onSymbol1Change,
  onSymbol2Change,
  onCompare,
  loading,
  result,
}: ComparePanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">Compare Stocks</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-2 md:grid-cols-2">
          <Select value={symbol1 ?? ""} onValueChange={onSymbol1Change}>
            <SelectTrigger>
              <SelectValue placeholder="Select symbol 1" />
            </SelectTrigger>
            <SelectContent>
              {companies.map((symbol) => (
                <SelectItem key={`cmp1-${symbol}`} value={symbol}>
                  {symbol}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={symbol2 ?? ""} onValueChange={onSymbol2Change}>
            <SelectTrigger>
              <SelectValue placeholder="Select symbol 2" />
            </SelectTrigger>
            <SelectContent>
              {companies.map((symbol) => (
                <SelectItem key={`cmp2-${symbol}`} value={symbol}>
                  {symbol}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          onClick={onCompare}
          disabled={loading || !symbol1 || !symbol2}
          className="w-full"
        >
          {loading ? "Comparing..." : `Compare (${days}D)`}
        </Button>

        {result ? (
          <div className="space-y-2 text-sm">
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>{result.symbol1.symbol}</span>
            <span>{formatPct(result.symbol1.pct_change)}</span>
          </div>
          <div className="flex justify-between rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-900">
            <span>{result.symbol2.symbol}</span>
            <span>{formatPct(result.symbol2.pct_change)}</span>
          </div>
          <div className="flex items-center justify-between rounded-md bg-emerald-50 px-3 py-2 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
            <span>Winner: {result.winner_symbol}</span>
            <Badge variant="success">Spread {formatPct(result.spread_pct)}</Badge>
          </div>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Select two symbols and run compare.</p>
        )}
      </CardContent>
    </Card>
  );
}
