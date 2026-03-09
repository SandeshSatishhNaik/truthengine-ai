export function PricingBadge({ model }: { model?: string }) {
  if (!model) return null;

  const lower = model.toLowerCase();
  let color = "bg-gray-700 text-gray-300";
  if (lower.includes("free")) color = "bg-green-900/50 text-green-400";
  else if (lower.includes("freemium")) color = "bg-yellow-900/50 text-yellow-400";
  else if (lower.includes("paid")) color = "bg-red-900/50 text-red-400";
  else if (lower.includes("open")) color = "bg-blue-900/50 text-blue-400";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}
    >
      {model}
    </span>
  );
}
