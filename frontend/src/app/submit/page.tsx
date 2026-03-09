"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  Sparkles,
  Globe,
  Shield,
  AlertCircle,
  ExternalLink,
  ArrowRight,
  GitCompareArrows,
  Search,
} from "lucide-react";
import { ToolCard } from "@/components/ToolCard";
import { PricingBadge } from "@/components/PricingBadge";
import { TagChip } from "@/components/TagChip";
import { ingestURL, type AnalysisReport, type AlternativeTool } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

/* ─── Alternative card ──────────────────────────────────────────── */

function AlternativeCard({
  alt,
  index,
}: {
  alt: AlternativeTool;
  index: number;
}) {
  const score = alt.tool.trust_score ?? 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      className="rounded-xl border border-white/5 bg-card p-5 transition-colors hover:border-accent/20"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <a
              href={`/tool/${alt.tool.id}`}
              className="text-base font-semibold text-white hover:text-gradient transition-colors truncate"
            >
              {alt.tool.name}
            </a>
            <span
              className={`rounded-md px-1.5 py-0.5 text-[10px] font-medium uppercase ${
                alt.source === "knowledge_base"
                  ? "bg-blue-500/10 text-blue-400"
                  : "bg-purple-500/10 text-purple-400"
              }`}
            >
              {alt.source === "knowledge_base" ? "KB" : "Web"}
            </span>
          </div>
          {alt.tool.category && (
            <p className="mt-0.5 text-xs text-gray-500 uppercase tracking-wider">
              {alt.tool.category}
            </p>
          )}
        </div>
        <PricingBadge model={alt.tool.pricing_model} />
      </div>

      {alt.tool.core_function && (
        <p className="mt-2 text-sm text-gray-400 line-clamp-2">
          {alt.tool.core_function}
        </p>
      )}

      <div className="mt-3 flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {(alt.tool.tags ?? []).slice(0, 3).map((tag) => (
            <TagChip key={tag} label={tag} />
          ))}
        </div>
        <div className="flex items-center gap-3 text-xs">
          {alt.similarity != null && (
            <span className="text-gray-500">
              {(alt.similarity * 100).toFixed(0)}% similar
            </span>
          )}
          <div className="flex items-center gap-1">
            <div
              className="h-2 w-2 rounded-full"
              style={{
                background:
                  score > 0.7
                    ? "#22c55e"
                    : score > 0.4
                      ? "#eab308"
                      : "#ef4444",
              }}
            />
            <span className="text-gray-500">
              {(score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ─── Pipeline step indicator ───────────────────────────────────── */

const PIPELINE_STEPS = [
  { label: "Crawling website", icon: Globe },
  { label: "Extracting with AI", icon: Sparkles },
  { label: "Verifying data", icon: Shield },
  { label: "Finding alternatives", icon: Search },
  { label: "Generating comparison", icon: GitCompareArrows },
];

function PipelineProgress() {
  const [step, setStep] = useState(0);

  useState(() => {
    const timers = PIPELINE_STEPS.map((_, i) =>
      setTimeout(() => setStep(i), i * 8000)
    );
    return () => timers.forEach(clearTimeout);
  });

  return (
    <div className="mx-auto mt-8 max-w-md space-y-3">
      {PIPELINE_STEPS.map((s, i) => {
        const Icon = s.icon;
        const active = i === step;
        const done = i < step;

        return (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm transition-colors ${
              active
                ? "bg-accent/10 text-accent"
                : done
                  ? "text-gray-500"
                  : "text-gray-700"
            }`}
          >
            {active ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Icon className="h-4 w-4" />
            )}
            {s.label}
            {done && (
              <span className="ml-auto text-xs text-green-500">Done</span>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */

export default function SubmitPage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() || loading) return;

    setLoading(true);
    setReport(null);
    setError(null);

    try {
      const result = await ingestURL(url.trim());
      setReport(result);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Something went wrong";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const tool = report?.tool;

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold text-white">Submit AI Tool</h1>
        <p className="mt-1 text-gray-500">
          Paste a URL — we&apos;ll analyze it, find alternatives, and compare
          them automatically.
        </p>
      </motion.div>

      {/* URL Input */}
      <form onSubmit={handleSubmit} className="mt-8">
        <motion.div
          layout
          className="relative"
        >
          <Globe className="absolute left-5 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-500" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com — any AI tool website"
            required
            className="w-full rounded-2xl border border-white/10 bg-card py-4 pl-14 pr-32 text-white placeholder:text-gray-500 focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/30 transition-all text-base"
          />
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 rounded-xl bg-gradient-accent px-6 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            {loading ? "Analyzing" : "Analyze"}
          </button>
        </motion.div>
      </form>

      <AnimatePresence mode="wait">
        {/* ── Loading state ─────────────────────────────────────── */}
        {loading && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-10 text-center"
          >
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-accent" />
            <p className="mt-4 text-gray-400">
              Analyzing tool and finding alternatives...
            </p>
            <p className="mt-1 text-xs text-gray-600">
              This may take up to a minute
            </p>
            <PipelineProgress />
          </motion.div>
        )}

        {/* ── Error state ───────────────────────────────────────── */}
        {error && !loading && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-8 flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/5 p-5"
          >
            <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-400" />
            <div>
              <p className="font-medium text-red-300">Analysis failed</p>
              <p className="mt-1 text-sm text-red-400/80">{error}</p>
            </div>
          </motion.div>
        )}

        {/* ── Results ───────────────────────────────────────────── */}
        {report && tool && !loading && (
          <motion.div
            key="report"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-10 space-y-8"
          >
            {/* ── Main tool card ────────────────────────────────── */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-accent/20 bg-gradient-to-b from-accent/[0.04] to-transparent p-6"
            >
              <div className="flex items-center gap-2 mb-1">
                <Sparkles className="h-4 w-4 text-accent" />
                <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                  Analyzed Tool
                </p>
              </div>

              <div className="mt-4 flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">
                    {tool.name}
                  </h2>
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
                      className="rounded-lg border border-white/10 p-2 text-gray-500 transition hover:text-white hover:border-white/20"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </div>

              {tool.core_function && (
                <p className="mt-4 text-sm leading-relaxed text-gray-300">
                  {tool.core_function}
                </p>
              )}

              {/* Trust score */}
              {tool.trust_score != null && (
                <div className="mt-5">
                  <p className="mb-2 text-xs text-gray-500">Trust Score</p>
                  <TrustBar score={tool.trust_score} />
                </div>
              )}

              {/* Details grid */}
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {tool.free_tier_limits && (
                  <div className="rounded-lg bg-white/[0.03] p-3">
                    <p className="text-xs text-gray-500">Free Tier</p>
                    <p className="mt-1 text-sm text-gray-300">
                      {tool.free_tier_limits}
                    </p>
                  </div>
                )}
                {tool.community_verdict && (
                  <div className="rounded-lg bg-white/[0.03] p-3">
                    <p className="text-xs text-gray-500">Community Verdict</p>
                    <p className="mt-1 text-sm text-gray-300">
                      {tool.community_verdict}
                    </p>
                  </div>
                )}
              </div>

              {/* Tags */}
              {tool.tags && tool.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {tool.tags.map((tag) => (
                    <TagChip key={tag} label={tag} />
                  ))}
                </div>
              )}
            </motion.div>

            {/* ── Alternatives ──────────────────────────────────── */}
            {report.alternatives.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
              >
                <div className="mb-4 flex items-center gap-2">
                  <Search className="h-4 w-4 text-gray-500" />
                  <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
                    Alternatives Found ({report.alternatives.length})
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {report.alternatives.map((alt, i) => (
                    <AlternativeCard key={alt.tool.id} alt={alt} index={i} />
                  ))}
                </div>
              </motion.div>
            )}

            {/* ── AI Comparison ─────────────────────────────────── */}
            {report.comparison && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-2xl border border-accent/10 bg-gradient-to-b from-accent/[0.03] to-transparent p-6"
              >
                <div className="mb-4 flex items-center gap-2">
                  <GitCompareArrows className="h-4 w-4 text-accent" />
                  <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                    AI Comparison
                  </p>
                </div>
                <div className="prose prose-invert prose-sm max-w-none text-gray-300 prose-headings:text-white prose-strong:text-white prose-li:text-gray-300">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {report.comparison}
                  </ReactMarkdown>
                </div>
              </motion.div>
            )}

            {/* ── Submit another ────────────────────────────────── */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.45 }}
              className="text-center"
            >
              <button
                onClick={() => {
                  setReport(null);
                  setUrl("");
                  setError(null);
                }}
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-5 py-2.5 text-sm text-gray-400 transition hover:border-accent/30 hover:text-white"
              >
                <ArrowRight className="h-4 w-4" />
                Analyze another tool
              </button>
            </motion.div>
          </motion.div>
        )}

        {/* ── Empty state ───────────────────────────────────────── */}
        {!loading && !report && !error && (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-16 text-center"
          >
            <Send className="mx-auto h-10 w-10 text-gray-700" />
            <p className="mt-4 text-lg text-gray-500">
              Submit any AI tool URL
            </p>
            <p className="mt-2 max-w-md mx-auto text-sm text-gray-600">
              We&apos;ll crawl the site, extract features and pricing with AI,
              find similar alternatives from our knowledge base and the web,
              then generate a detailed comparison.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-2">
              {[
                "https://cursor.sh",
                "https://bolt.new",
                "https://v0.dev",
              ].map((u) => (
                <button
                  key={u}
                  onClick={() => setUrl(u)}
                  className="flex items-center gap-2 rounded-xl border border-white/5 bg-card/50 px-4 py-2.5 text-sm text-gray-400 transition hover:border-accent/20 hover:text-white"
                >
                  <Globe className="h-3.5 w-3.5 text-gray-600" />
                  {u}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
