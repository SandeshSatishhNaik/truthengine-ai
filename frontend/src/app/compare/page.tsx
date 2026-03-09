"use client";

import { Suspense, useState, useEffect, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Plus,
  Search,
  Sparkles,
  Shield,
  Loader2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  getTools,
  compareTools,
  type Tool,
  type ComparisonResponse,
} from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/* ─── Trust score bar ────────────────────────────────────────────── */

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
      <div className="h-2 flex-1 rounded-full bg-white/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-2 rounded-full bg-gradient-to-r ${color}`}
        />
      </div>
      <span className="text-sm font-medium text-white">{pct}%</span>
    </div>
  );
}

/* ─── Selected tool pill ─────────────────────────────────────────── */

function SelectedPill({
  tool,
  onRemove,
}: {
  tool: Tool;
  onRemove: () => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className="flex items-center gap-2 rounded-xl border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent"
    >
      {tool.name}
      <button onClick={onRemove} className="text-accent/60 hover:text-accent">
        <X className="h-3.5 w-3.5" />
      </button>
    </motion.div>
  );
}

/* ─── Comparison field rows ──────────────────────────────────────── */

const FIELDS: { key: string; label: string }[] = [
  { key: "core_function", label: "Core Function" },
  { key: "pricing_model", label: "Pricing Model" },
  { key: "free_tier_limits", label: "Free Tier Limits" },
  { key: "community_verdict", label: "Community Verdict" },
];

/* ─── Page ───────────────────────────────────────────────────────── */

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#0a0a0f]">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
        </div>
      }
    >
      <ComparePageContent />
    </Suspense>
  );
}

function ComparePageContent() {
  const searchParams = useSearchParams();
  const [allTools, setAllTools] = useState<Tool[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [toolsLoading, setToolsLoading] = useState(true);

  /* search within selector */
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");

  useEffect(() => {
    getTools(undefined, 50)
      .then((tools) => {
        setAllTools(tools);
        // Pre-select tools from URL query param (?tools=id1,id2)
        const param = searchParams.get("tools");
        if (param) {
          const ids = param.split(",").filter((id) => tools.some((t) => t.id === id));
          if (ids.length > 0) setSelected(ids);
        }
      })
      .catch(() => setAllTools([]))
      .finally(() => setToolsLoading(false));
  }, [searchParams]);

  const filtered = useMemo(() => {
    const q = filterQuery.toLowerCase();
    return allTools.filter(
      (t) =>
        !selected.includes(t.id) &&
        (t.name.toLowerCase().includes(q) ||
          (t.core_function || "").toLowerCase().includes(q))
    );
  }, [allTools, filterQuery, selected]);

  const selectedTools = useMemo(
    () => selected.map((id) => allTools.find((t) => t.id === id)!).filter(Boolean),
    [selected, allTools]
  );

  const addTool = (id: string) => {
    if (selected.length >= 5) return;
    setSelected((p) => [...p, id]);
    setFilterQuery("");
    if (selected.length >= 1) setSelectorOpen(false);
  };

  const removeTool = (id: string) => {
    setSelected((p) => p.filter((x) => x !== id));
    setComparison(null);
  };

  const handleCompare = async () => {
    if (selected.length < 2) return;
    setLoading(true);
    try {
      const result = await compareTools(selected);
      setComparison(result);
    } catch {
      setComparison(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      {/* Header */}
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold text-white"
      >
        Compare Tools
      </motion.h1>
      <p className="mt-1 text-gray-500">
        Select 2-5 tools for a side-by-side AI-powered comparison
      </p>

      {/* Selected pills */}
      <div className="mt-6 flex flex-wrap items-center gap-2">
        <AnimatePresence mode="popLayout">
          {selectedTools.map((t) => (
            <SelectedPill
              key={t.id}
              tool={t}
              onRemove={() => removeTool(t.id)}
            />
          ))}
        </AnimatePresence>

        {selected.length < 5 && (
          <button
            onClick={() => setSelectorOpen((o) => !o)}
            className="flex items-center gap-1.5 rounded-xl border border-dashed border-white/10 px-3 py-2 text-sm text-gray-500 transition hover:border-white/20 hover:text-gray-300"
          >
            <Plus className="h-4 w-4" />
            Add tool
            {selectorOpen ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>

      {/* Selector dropdown */}
      <AnimatePresence>
        {selectorOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 rounded-2xl border border-white/5 bg-card p-4">
              <div className="relative mb-3">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-600" />
                <input
                  autoFocus
                  type="text"
                  placeholder="Search tools..."
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  className="w-full rounded-xl border border-white/5 bg-background py-2 pl-10 pr-4 text-sm text-white placeholder:text-gray-600 focus:border-accent/30 focus:outline-none"
                />
              </div>
              {toolsLoading ? (
                <p className="py-4 text-center text-sm text-gray-500">
                  Loading...
                </p>
              ) : filtered.length === 0 ? (
                <p className="py-4 text-center text-sm text-gray-500">
                  No tools found
                </p>
              ) : (
                <div className="grid max-h-48 gap-1 overflow-y-auto">
                  {filtered.slice(0, 20).map((t) => (
                    <button
                      key={t.id}
                      onClick={() => addTool(t.id)}
                      className="flex items-center justify-between rounded-lg px-3 py-2 text-left text-sm text-gray-300 transition hover:bg-white/5"
                    >
                      <span>{t.name}</span>
                      <span className="text-xs text-gray-600">
                        {t.pricing_model || "—"}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Compare button */}
      <button
        onClick={handleCompare}
        disabled={selected.length < 2 || loading}
        className="mt-6 flex items-center gap-2 rounded-xl bg-gradient-accent px-6 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-40"
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="h-4 w-4" />
        )}
        {loading
          ? "Analyzing..."
          : `Compare ${selected.length} tools`}
      </button>

      {/* Comparison Result */}
      <AnimatePresence>
        {comparison && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-10 space-y-6"
          >
            {/* Trust score cards */}
            <div>
              <p className="mb-4 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                <Shield className="h-3.5 w-3.5" />
                Trust Scores
              </p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {comparison.tools.map((t, i) => (
                  <motion.div
                    key={t.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="rounded-xl border border-white/5 bg-card p-4"
                  >
                    <p className="mb-2 text-sm font-medium text-white">
                      {t.name}
                    </p>
                    <TrustBar score={t.trust_score ?? 0} />
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Comparison table */}
            <div className="overflow-x-auto rounded-2xl border border-white/5">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/5 bg-card">
                    <th className="w-40 px-5 py-3.5 text-xs font-medium uppercase tracking-wider text-gray-500">
                      Field
                    </th>
                    {comparison.tools.map((t) => (
                      <th
                        key={t.id}
                        className="px-5 py-3.5 text-sm font-semibold text-white"
                      >
                        {t.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {FIELDS.map(({ key, label }, ri) => (
                    <motion.tr
                      key={key}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.15 + ri * 0.06 }}
                      className="border-b border-white/5 transition-colors hover:bg-white/[0.02]"
                    >
                      <td className="px-5 py-3.5 text-gray-500">{label}</td>
                      {comparison.tools.map((t) => (
                        <td
                          key={t.id}
                          className="px-5 py-3.5 text-gray-300"
                        >
                          {(t as unknown as Record<string, unknown>)[key] as string ||
                            "N/A"}
                        </td>
                      ))}
                    </motion.tr>
                  ))}
                  {/* Tags row */}
                  <motion.tr
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.45 }}
                    className="border-b border-white/5"
                  >
                    <td className="px-5 py-3.5 text-gray-500">Tags</td>
                    {comparison.tools.map((t) => (
                      <td key={t.id} className="px-5 py-3.5">
                        <div className="flex flex-wrap gap-1">
                          {(t.tags || []).map((tag) => (
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

            {/* AI Analysis */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="rounded-2xl border border-accent/10 bg-gradient-to-b from-accent/[0.03] to-transparent p-6"
            >
              <div className="mb-3 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-accent" />
                <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                  AI Analysis
                </p>
              </div>
              <div className="prose prose-invert prose-sm max-w-none text-gray-300 prose-headings:text-white prose-strong:text-white prose-li:text-gray-300">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {comparison.comparison_text}
                </ReactMarkdown>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
