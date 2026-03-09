export function TagChip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center rounded-md bg-accent/10 px-2 py-0.5 text-xs text-accent">
      {label}
    </span>
  );
}
