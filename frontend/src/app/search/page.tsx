"use client";

import { Suspense, useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Globe,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { ToolCard } from "@/components/ToolCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { searchTools, type SearchResult, type SearchResponse } from "@/lib/api";

export default function SearchPage() {
  return (
    <Suspense fallback={<LoadingSkeleton count={3} />}>
      <SearchPageContent />
    </Suspense>
  );
}

/* ─── Suggested follow-ups ──────────────────────────────────────── */

function deriveFollowUps(query: string, results: SearchResult[]): string[] {
  const suggestions: string[] = [];
  if (results.length > 0) {
    const firstName = results[0].tool.name;
    suggestions.push(`${firstName} pricing details`);
    suggestions.push(`${firstName} vs alternatives`);
    if (results.length > 1) {
      suggestions.push(
        `Compare ${firstName} and ${results[1].tool.name}`
      );
    }
  }
  if (!query.toLowerCase().includes("free")) {
    suggestions.push(`free ${query} options`);
  }
  return suggestions.slice(0, 3);
}

/* ─── Animated typing text ──────────────────────────────────────── */

function TypedAnswer({ text }: { text: string }) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(interval);
        setDone(true);
      }
    }, 8);
    return () => clearInterval(interval);
  }, [text]);

  return (
    <span>
      {displayed}
      {!done && <span className="cursor-blink" />}
    </span>
  );
}

/* ─── Source chip ────────────────────────────────────────────────── */

function SourceChip({
  tool,
  index,
  similarity,
}: {
  tool: SearchResult["tool"];
  index: number;
  similarity: number;
}) {
  return (
    <motion.a
      href={`/tool/${tool.id}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
      className="group flex items-center gap-2 rounded-xl border border-white/5 bg-card/80 px-3 py-2 text-xs transition hover:border-accent/30"
    >
      <Globe className="h-3.5 w-3.5 text-gray-600 group-hover:text-accent" />
      <span className="text-gray-300 group-hover:text-white">{tool.name || "Unknown Tool"}</span>
      <span className="text-gray-600">{(similarity * 100).toFixed(0)}%</span>
    </motion.a>
  );
}

/* ─── Main content ──────────────────────────────────────────────── */

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuery = searchParams.get("q") || "";
  const inputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [followUps, setFollowUps] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setSearched(true);
    setAnswer(null);
    setFollowUps([]);
    setError(null);
    try {
      const res: SearchResponse = await searchTools(q.trim());
      setResults(res.results);
      setAnswer(res.answer || null);
      setFollowUps(deriveFollowUps(q, res.results));
    } catch {
      setResults([]);
      setAnswer(null);
      setError("Search service is temporarily unavailable. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialQuery) handleSearch(initialQuery);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const submitSearch = (q: string) => {
    setQuery(q);
    router.replace(`/search?q=${encodeURIComponent(q)}`, { scroll: false });
    handleSearch(q);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitSearch(query);
  };

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {/* ── Search input ─────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="relative">
        <motion.div
          layout
          className="relative"
        >
          <Search className="absolute left-5 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-500" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about AI tools..."
            className="w-full rounded-2xl border border-white/10 bg-card py-4 pl-14 pr-28 text-white placeholder:text-gray-500 focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/30 transition-all text-base"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 rounded-xl bg-gradient-accent px-5 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowRight className="h-4 w-4" />
            )}
            {loading ? "Thinking" : "Ask"}
          </button>
        </motion.div>
      </form>

      <AnimatePresence mode="wait">
        {loading ? (
          /* ── Loading state ─────────────────────────────────── */
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-10"
          >
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin text-accent" />
              Searching knowledge base and generating answer...
            </div>
            <div className="mt-6">
              <LoadingSkeleton count={3} />
            </div>
          </motion.div>
        ) : searched ? (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-8"
          >
            {/* ── Sources row ──────────────────────────────────── */}
            {results.length > 0 && (
              <div className="mb-6">
                <p className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <Globe className="h-3.5 w-3.5" />
                  Sources ({results.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {results.map((r, i) => (
                    <SourceChip
                      key={r.tool.id}
                      tool={r.tool}
                      index={i}
                      similarity={r.similarity}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* ── AI Answer ────────────────────────────────────── */}
            {answer && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="rounded-2xl border border-accent/10 bg-gradient-to-b from-accent/[0.03] to-transparent p-6"
              >
                <div className="mb-3 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-accent" />
                  <p className="text-xs font-semibold uppercase tracking-wider text-accent">
                    AI Answer
                  </p>
                </div>
                <div className="prose-ai text-sm leading-relaxed text-gray-300">
                  <TypedAnswer text={answer} />
                </div>
              </motion.div>
            )}

            {/* ── Tool cards ───────────────────────────────────── */}
            {results.length > 0 && (
              <div className="mt-8">
                <p className="mb-4 text-xs font-medium uppercase tracking-wider text-gray-500">
                  Matching Tools
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  {results.map((r, i) => (
                    <ToolCard key={r.tool.id} tool={r.tool} index={i} />
                  ))}
                </div>
              </div>
            )}

            {/* ── Follow-up suggestions ────────────────────────── */}
            {followUps.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-8"
              >
                <p className="mb-3 text-xs font-medium uppercase tracking-wider text-gray-500">
                  Related searches
                </p>
                <div className="flex flex-col gap-2">
                  {followUps.map((q) => (
                    <button
                      key={q}
                      onClick={() => submitSearch(q)}
                      className="flex items-center gap-3 rounded-xl border border-white/5 bg-card/50 px-4 py-3 text-left text-sm text-gray-400 transition hover:border-accent/20 hover:text-white"
                    >
                      <ChevronRight className="h-4 w-4 text-accent/60" />
                      {q}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* ── Empty state ──────────────────────────────────── */}
            {results.length === 0 && !answer && (
              <div className="mt-16 text-center">
                <Search className="mx-auto h-10 w-10 text-gray-700" />
                <p className="mt-4 text-gray-500">
                  {error || "No results found. Try a different query."}
                </p>
              </div>
            )}
          </motion.div>
        ) : (
          /* ── Empty / intro state ─────────────────────────────── */
          <motion.div
            key="intro"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-20 text-center"
          >
            <Sparkles className="mx-auto h-10 w-10 text-gray-700" />
            <p className="mt-4 text-lg text-gray-500">
              Ask anything about AI tools
            </p>
            <p className="mt-2 text-sm text-gray-600">
              Get AI-powered answers with verified sources from our knowledge base
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-2">
              {[
                "What are the best free LLM APIs?",
                "Compare GPT-4 and Claude",
                "Free image generation tools",
                "AI coding assistants with free tiers",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => submitSearch(q)}
                  className="flex items-center gap-2 rounded-xl border border-white/5 bg-card/50 px-4 py-2.5 text-sm text-gray-400 transition hover:border-accent/20 hover:text-white"
                >
                  <Search className="h-3.5 w-3.5 text-gray-600" />
                  {q}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
