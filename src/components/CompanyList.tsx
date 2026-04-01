"use client";

interface CompanyListProps {
  companies: string[];
  selected: string | null;
  onSelect: (symbol: string) => void;
}

export default function CompanyList({
  companies,
  selected,
  onSelect,
}: CompanyListProps) {
  return (
    <aside className="w-full border-b border-slate-200 bg-white/80 p-4 backdrop-blur-lg md:w-72 md:border-r md:border-b-0 dark:border-slate-800 dark:bg-slate-950/70">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-300">
        Companies
      </h2>
      <div className="max-h-[42vh] space-y-1 overflow-auto pr-1 md:max-h-[78vh]">
        {companies.map((symbol) => {
          const isSelected = selected === symbol;
          return (
            <button
              key={symbol}
              onClick={() => onSelect(symbol)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-all duration-200 ${
                isSelected
                  ? "bg-cyan-500 text-white shadow-md shadow-cyan-500/30"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              }`}
            >
              {symbol}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
