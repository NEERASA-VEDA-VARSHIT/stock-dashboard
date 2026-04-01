export default function Spinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="inline-flex items-center gap-2 text-sm text-cyan-600 dark:text-cyan-300">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
      <span>{label}</span>
    </div>
  );
}
