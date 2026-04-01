"use client";

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
import { PredictionResponse, StockResponse } from "@/types/stock";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
);

interface StockChartProps {
  data: StockResponse | null;
  prediction: PredictionResponse | null;
}

export default function StockChart({ data, prediction }: StockChartProps) {
  if (!data || data.count === 0) {
    return (
      <div className="flex h-80 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 text-slate-500 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-400">
        Select a company to see closing prices.
      </div>
    );
  }

  const points = [...data.data].reverse();
  const labels = points.map((d) => new Date(d.date).toLocaleDateString());
  const prices = points.map((d) => d.close);
  const ma7 = points.map((d) => d.ma7 ?? null);

  const hasPrediction = !!prediction && prices.length > 0;
  const chartLabels = hasPrediction ? [...labels, "Forecast"] : labels;
  const closeSeries = hasPrediction ? [...prices, null] : prices;
  const ma7Series = hasPrediction ? [...ma7, null] : ma7;
  const predictionSeries = hasPrediction
    ? [...Array(Math.max(prices.length - 1, 0)).fill(null), prices[prices.length - 1], prediction!.predicted_close]
    : [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/85 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950/70">
      <Line
        data={{
          labels: chartLabels,
          datasets: [
            {
              label: `${data.symbol} Close`,
              data: closeSeries,
              borderColor: "#0ea5e9",
              backgroundColor: "rgba(14,165,233,0.15)",
              fill: true,
              tension: 0.35,
              borderWidth: 2,
              pointRadius: 1.5,
            },
            {
              label: "MA7",
              data: ma7Series,
              borderColor: "#f97316",
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.3,
            },
            ...(hasPrediction
              ? [
                  {
                    label: `ML Forecast (${prediction!.model})`,
                    data: predictionSeries,
                    borderColor: "#22c55e",
                    borderWidth: 2,
                    borderDash: [6, 6],
                    pointRadius: 3,
                    pointHoverRadius: 4,
                    tension: 0,
                  },
                ]
              : []),
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true },
          },
          scales: {
            x: {
              grid: { color: "rgba(148,163,184,0.15)" },
            },
            y: {
              grid: { color: "rgba(148,163,184,0.15)" },
            },
          },
        }}
        height={320}
      />
    </div>
  );
}
