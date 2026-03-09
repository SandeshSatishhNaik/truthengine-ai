"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ExternalLink,
  Sparkles,
  Shield,
  GitCompareArrows,
  BarChart3,
  Loader2,
  Globe,
} from "lucide-react";
import {
  getTool,
  searchSimilar,
  compareTools,
  getAlternatives,
  type Tool,
  type SearchResult,
  type AlternativeTool,
  type ComparisonResponse,
} from "@/lib/api";
import { PricingBadge } from "@/components/PricingBadge";
import { TagChip } from "@/components/TagChip";

/* ─── Trust bar ─────────────────────────────────────────────────── */

function TrustBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80
      ? "from-green-500 to-emerald-400"
      : pct >= 50
        ? "from-yellow-500 to-amber-400"
        : "from-red-500 to-orange-400";

  return (
    <div className="flex items-center gap-3">
      <div className="h-2.5 flex-1 rounded-full bg-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`h-2.5 rounded-full bg-gradient-to-r ${color}`}
        />
      </div>
      <span className="text-sm font-semibold text-white">{pct}%</span>
    </div>
  );
}

/* ─── Benchmark chart (horizontal bars comparing all tools) ─────── */

function BenchmarkChart({
  mainTool,
  similar,
}: {
  mainTool: Tool;
  similar: AlternativeTool[];
}) {
  const allTools = [
    { tool: mainTool, isCurrent: true },
    ...similar
      .filter((s) => s.tool.id !== mainTool.id)
      .map((s) => ({ tool: s.tool, isCurrent: false })),
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="rounded-2xl border border-white/5 bg-card p-6"
    >
      <div className="mb-5 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-accent" />
        <p className="text-xs font-semibold uppercase tracking-wider text-accent">
          Trust Score Benchmark
        </p>
      </div>

      <div className="space-y-4">
        {allTools.map(({ tool, isCurrent }, i) => {
          const score = tool.trust_score ?? 0;
          const pct = Math.round(score * 100);
          const barColor = isCurrent
            ? "from-violet-500 to-fuchsia-400"
            : pct >= 80
              ? "from-green-500 to-emerald-400"
              : pct >= 50
                ? "from-yellow-500 to-amber-400"
                : "from-red-500 to-orange-400";

          return (
            <motion.div
              key={tool.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + i * 0.08 }}
            >
              <div className="mb-1 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-medium ${
                      isCurrent ? "text-accent" : "text-gray-300"
                    }`}
                  >
                    {tool.name}
                  </span>
                  {isCurrent && (
                    <span className="rounded bg-accent/10 px-1.5 py-0.5 text-[10px] font-medium text-accent">
                      Current
                    </span>
                  )}
                  {tool.pricing_model && (
                    <span className="text-[10px] text-gray-600">
                      {tool.pricing_model}
                    </span>
                  )}
                </div>
                <span className="text-sm font-semibold text-white">
                  {pct}%
                </span>
              </div>
              <div className="h-3 rounded-full bg-white/5">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 1, delay: 0.2 + i * 0.1 }}
                  className={`h-3 rounded-full bg-gradient-to-r ${barColor} ${
                    isCurrent ? "shadow-[0_0_12px_rgba(139,92,246,0.3)]" : ""
                  }`}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-5 flex flex-wrap gap-4 border-t border-white/5 pt-4 text-[10px] text-gray-500">
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-6 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-400" />
          Current tool
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-6 rounded-full bg-gradient-to-r from-green-500 to-emerald-400" />
          High trust (≥80%)
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-6 rounded-full bg-gradient-to-r from-yellow-500 to-amber-400" />
          Medium (50-79%)
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-6 rounded-full bg-gradient-to-r from-red-500 to-orange-400" />
          Low (&lt;50%)
        </div>
      </div>
    </motion.div>
  );
}

/* ─── Comparison table ──────────────────────────────────────────── */

const COMPARE_FIELDS: { key: keyof Tool; label: string }[] = [
  { key: "core_function", label: "Core Function" },
  { key: "pricing_model", label: "Pricing" },
  { key: "free_tier_limits", label: "Free Tier" },
  { key: "community_verdict", label: "Verdict" },
];

function ComparisonTable({ tools }: { tools: Tool[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-white/5">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-white/5 bg-card">
            <th className="w-32 px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">
              Field
            </th>
            {tools.map((t) => (
              <th
                key={t.id}
                className="px-4 py-3 text-sm font-semibold text-white"
              >
                {t.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {COMPARE_FIELDS.map(({ key, label }, ri) => (
            <motion.tr
              key={key}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 + ri * 0.06 }}
              className="border-b border-white/5 transition-colors hover:bg-white/[0.02]"
            >
              <td className="px-4 py-3 text-gray-500">{label}</td>
              {tools.map((t) => (
                <td key={t.id} className="px-4 py-3 text-gray-300">
                  {(t[key] as string) || "N/A"}
                </td>
              ))}
            </motion.tr>
          ))}
          {/* Tags row */}
          <motion.tr
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="border-b border-white/5"
          >
            <td className="px-4 py-3 text-gray-500">Tags</td>
            {tools.map((t) => (
              <td key={t.id} className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {(t.tags || []).slice(0, 4).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md bg-white/5 px-2 py-0.5 text-xs text-gray-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </td>
            ))}
          </motion.tr>
        </tbody>
      </table>
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */

export function ToolPageClient() {
  const params = useParams();
  const id = params.id as string;

  const [tool, setTool] = useState<Tool | null>(null);
  const [loading, setLoading] = useState(true);

  // Similar tools & comparison
  const [similar, setSimilar] = useState<AlternativeTool[]>([]);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [compLoading, setCompLoading] = useState(false);

  // Load tool
  useEffect(() => {
    if (!id) return;
    getTool(id)
      .then(setTool)
      .catch(() => setTool(null))
      .finally(() => setLoading(false));
  }, [id]);

  // Once tool loaded, find alternatives & auto-compare
  useEffect(() => {
    if (!tool) return;

    setCompLoading(true);

    // Try embedding-based alternatives first, fall back to text search
    getAlternatives(tool.id, 5)
      .then((alts) => {
        if (alts.length > 0) return alts;
        // Fallback: text-based search
        const query = `${tool.name} ${tool.category || ""} ${(tool.tags || []).slice(0, 2).join(" ")}`.trim();
        return searchSimilar(query, 5).then((results) =>
          results
            .filter((r) => r.tool.id !== tool.id)
            .map((r) => ({ tool: r.tool, similarity: r.similarity, source: "knowledge_base" }))
        );
      })
      .then((alts) => {
        setSimilar(alts);

        // Auto-compare if we have at least 1 other tool
        if (alts.length > 0) {
          const ids = [tool.id, ...alts.slice(0, 4).map((a) => a.tool.id)];
          return compareTools(ids);
        }
        return null;
      })
      .then((comp) => {
        if (comp) setComparison(comp);
      })
      .catch(() => {
        setSimilar([]);
      })
      .finally(() => setCompLoading(false));
  }, [tool]);

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="animate-pulse space-y-4">
          <div className="h-10 w-1/3 rounded bg-white/5" />
          <div className="h-4 w-full rounded bg-white/5" />
          <div className="h-4 w-2/3 rounded bg-white/5" />
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="h-24 rounded-xl bg-white/5" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!tool) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-10 text-center">
        <Globe className="mx-auto h-10 w-10 text-gray-700" />
        <p className="mt-4 text-gray-500">Tool not found.</p>
      </div>
    );
  }

  const score = tool.trust_score ?? 0;

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 space-y-10">
      {/* ── Main tool info ────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-accent/20 bg-gradient-to-b from-accent/[0.04] to-transparent p-6 sm:p-8"
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-accent" />
              <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                Tool Analysis
              </p>
            </div>
            <h1 className="mt-2 text-3xl font-bold text-white sm:text-4xl">
              {tool.name}
            </h1>
            {tool.category && (
              <p className="mt-1 text-xs text-gray-500 uppercase tracking-wider">
                {tool.category}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <PricingBadge model={tool.pricing_model} />
            {tool.website && (
              <a
                href={tool.website}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-white/10 p-2 text-gray-500 transition hover:border-white/20 hover:text-white"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        {tool.core_function && (
          <p className="mt-5 text-sm leading-relaxed text-gray-300">
            {tool.core_function}
          </p>
        )}

        {/* Trust Score */}
        <div className="mt-6">
          <p className="mb-2 text-xs text-gray-500">Trust Score</p>
          <TrustBar score={score} />
        </div>

        {/* Info grid */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {tool.free_tier_limits && (
            <div className="rounded-xl bg-white/[0.03] p-4">
              <p className="text-xs text-gray-500">Free Tier</p>
              <p className="mt-1 text-sm text-gray-300">
                {tool.free_tier_limits}
              </p>
            </div>
          )}
          {tool.community_verdict && (
            <div className="rounded-xl bg-white/[0.03] p-4">
              <p className="text-xs text-gray-500">Community Verdict</p>
              <p className="mt-1 text-sm text-gray-300">
                {tool.community_verdict}
              </p>
            </div>
          )}
        </div>

        {/* Tags */}
        {tool.tags && tool.tags.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-1.5">
            {tool.tags.map((tag) => (
              <TagChip key={tag} label={tag} />
            ))}
          </div>
        )}
      </motion.div>

      {/* ── Loading state for comparison ──────────────────────── */}
      {compLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center gap-3 py-10"
        >
          <Loader2 className="h-5 w-5 animate-spin text-accent" />
          <span className="text-sm text-gray-400">
            Finding similar tools and generating comparison...
          </span>
        </motion.div>
      )}

      <AnimatePresence>
        {!compLoading && similar.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-10"
          >
            {/* ── Benchmark Chart ─────────────────────────────── */}
            <BenchmarkChart mainTool={tool} similar={similar} />

            {/* ── Side-by-side comparison table ───────────────── */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <Shield className="h-4 w-4 text-gray-500" />
                <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
                  Feature Comparison
                </p>
              </div>
              <ComparisonTable
                tools={[
                  tool,
                  ...similar.slice(0, 4).map((s) => s.tool),
                ]}
              />
            </div>

            {/* ── AI Comparison text ──────────────────────────── */}
            {comparison?.comparison_text && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-accent/10 bg-gradient-to-b from-accent/[0.03] to-transparent p-6"
              >
                <div className="mb-4 flex items-center gap-2">
                  <GitCompareArrows className="h-4 w-4 text-accent" />
                  <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                    AI Comparison Analysis
                  </p>
                </div>
                <div className="prose-ai text-sm leading-relaxed text-gray-300 whitespace-pre-line">
                  {comparison.comparison_text}
                </div>
              </motion.div>
            )}

            {/* ── Similar tool cards ─────────────────────────── */}
            <div>
              <div className="mb-4 flex items-center gap-2">
                <Globe className="h-4 w-4 text-gray-500" />
                <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
                  Similar Tools ({similar.length})
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {similar.map((s, i) => (
                  <motion.div
                    key={s.tool.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="group rounded-xl border border-white/5 bg-card p-5 transition-colors hover:border-accent/20"
                  >
                    <a href={`/tool/${s.tool.id}`} className="block">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-semibold text-white group-hover:text-gradient transition-colors">
                            {s.tool.name}
                          </p>
                          {s.tool.category && (
                            <p className="mt-0.5 text-xs text-gray-500 uppercase">
                              {s.tool.category}
                            </p>
                          )}
                        </div>
                        <PricingBadge model={s.tool.pricing_model} />
                      </div>
                      {s.tool.core_function && (
                        <p className="mt-2 text-sm text-gray-400 line-clamp-2">
                          {s.tool.core_function}
                        </p>
                      )}
                      <div className="mt-3 flex items-center justify-between text-xs">
                        <span className="text-gray-500">
                          {s.similarity != null
                            ? `${(s.similarity * 100).toFixed(0)}% similar`
                            : "Similar"}
                        </span>
                        <div className="flex items-center gap-1">
                          <div
                            className="h-2 w-2 rounded-full"
                            style={{
                              background:
                                (s.tool.trust_score ?? 0) > 0.7
                                  ? "#22c55e"
                                  : (s.tool.trust_score ?? 0) > 0.4
                                    ? "#eab308"
                                    : "#ef4444",
                            }}
                          />
                          <span className="text-gray-500">
                            {((s.tool.trust_score ?? 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </a>
                    <a
                      href={`/compare?tools=${encodeURIComponent(tool.id)},${encodeURIComponent(s.tool.id)}`}
                      className="mt-3 flex items-center justify-center gap-1.5 rounded-lg border border-accent/20 bg-accent/5 px-3 py-1.5 text-xs font-medium text-accent transition-colors hover:bg-accent/10"
                    >
                      <GitCompareArrows className="h-3.5 w-3.5" />
                      Compare
                    </a>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* No similar found */}
        {!compLoading && similar.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-10"
          >
            <p className="text-sm text-gray-500">
              No similar tools found in the knowledge base yet.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
