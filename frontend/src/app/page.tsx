"use client";

import { useRef, useEffect, useState } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useInView,
} from "framer-motion";
import { SearchBar } from "@/components/SearchBar";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  Globe,
  Shield,
  Zap,
  ArrowDown,
  Database,
  Brain,
  BarChart3,
} from "lucide-react";
import { useCountUp } from "@/hooks/useCountUp";
import { getTools, getSystemMetrics, type Tool } from "@/lib/api";

/* ─── Data ──────────────────────────────────────────────────────── */

const features = [
  {
    icon: <Globe className="h-7 w-7" />,
    title: "Submit & Analyze",
    desc: "Paste any AI tool URL — we crawl it and extract features, pricing, and more with AI.",
  },
  {
    icon: <Shield className="h-7 w-7" />,
    title: "Truth Verification",
    desc: "Cross-references pricing and features against multiple independent sources.",
  },
  {
    icon: <Sparkles className="h-7 w-7" />,
    title: "Auto Alternatives",
    desc: "Automatically finds similar tools from our knowledge base and the web.",
  },
  {
    icon: <Zap className="h-7 w-7" />,
    title: "Instant Comparison",
    desc: "AI-generated side-by-side comparison with every submission.",
  },
];

const pipeline = [
  { icon: <Globe className="h-5 w-5" />, label: "Crawl", detail: "Fetch homepage, pricing & docs" },
  { icon: <Brain className="h-5 w-5" />, label: "Extract", detail: "LLM structures the data" },
  { icon: <Shield className="h-5 w-5" />, label: "Verify", detail: "Cross-check & trust score" },
  { icon: <Sparkles className="h-5 w-5" />, label: "Discover", detail: "Find similar tools" },
  { icon: <Database className="h-5 w-5" />, label: "Compare", detail: "AI side-by-side analysis" },
  { icon: <BarChart3 className="h-5 w-5" />, label: "Report", detail: "Full analysis delivered" },
];

/* ─── Animated Counter Card ─────────────────────────────────────── */

function CounterCard({
  label,
  value,
  suffix,
  index,
}: {
  label: string;
  value: number;
  suffix?: string;
  index: number;
}) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  const count = useCountUp(isInView ? value : 0, 2000);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="text-center"
    >
      <p className="text-4xl font-bold text-gradient sm:text-5xl">
        {count}
        {suffix}
      </p>
      <p className="mt-2 text-sm text-gray-500">{label}</p>
    </motion.div>
  );
}

/* ─── Page ──────────────────────────────────────────────────────── */

export default function LandingPage() {
  const router = useRouter();
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });

  const heroY = useTransform(scrollYProgress, [0, 1], [0, 150]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  const [stats, setStats] = useState({ tools: 0, tags: 0, categories: 0, avgTrust: 0 });

  useEffect(() => {
    const fetchStats = () =>
      Promise.all([
        getTools(undefined, 200).catch(() => [] as Tool[]),
        getSystemMetrics().catch(() => null),
      ]).then(([tools, metrics]) => {
        if (tools.length === 0) return false;
        const categories = new Set(tools.map((t) => t.category).filter(Boolean)).size;
        const avgTrust =
          tools.length > 0
            ? Math.round(
                (tools.reduce((sum, t) => sum + (t.trust_score ?? 0), 0) / tools.length) * 100
              )
            : 0;
        const uniqueTags = new Set(tools.flatMap((t) => t.tags ?? [])).size;
        setStats({ tools: tools.length, tags: uniqueTags, categories, avgTrust });
        return true;
      });

    fetchStats().then((ok) => {
      if (!ok) setTimeout(() => fetchStats(), 5000);
    });
  }, []);

  const handleSearch = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="flex flex-col items-center aurora-bg">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section
        ref={heroRef}
        className="relative flex min-h-screen flex-col items-center justify-center px-6 text-center grid-pattern"
      >
        <motion.div style={{ y: heroY, opacity: heroOpacity }}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-4 py-1.5 text-xs font-medium text-accent">
              <Sparkles className="h-3.5 w-3.5" /> Autonomous AI Knowledge Engine
            </p>
            <h1 className="text-5xl font-bold leading-[1.1] tracking-tight sm:text-7xl lg:text-8xl">
              <span className="text-gradient">TruthEngine</span>{" "}
              <span className="text-white">AI</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-400 sm:text-xl">
              Submit any AI tool — we analyze it, find alternatives, and compare
              them instantly. Powered by LLM extraction, truth verification, and
              semantic search.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="mt-10 w-full max-w-2xl"
          >
            <SearchBar
              onSearch={handleSearch}
              placeholder="Search AI tools... e.g. 'free image generation'"
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.7 }}
            className="mt-6 flex flex-wrap justify-center gap-2 text-sm text-gray-500"
          >
            <span>Try:</span>
            {["free LLM API", "image generation", "AI code assistant"].map((q) => (
              <button
                key={q}
                onClick={() => handleSearch(q)}
                className="rounded-full border border-white/10 px-3 py-1 text-gray-400 transition hover:border-accent/40 hover:text-white"
              >
                {q}
              </button>
            ))}
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-10"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <ArrowDown className="h-5 w-5 text-gray-600" />
          </motion.div>
        </motion.div>
      </section>

      {/* ── Stats ────────────────────────────────────────────── */}
      <section className="w-full max-w-5xl px-6 py-20">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          <CounterCard label="AI Tools Indexed" value={stats.tools} suffix="+" index={0} />
          <CounterCard label="Unique Tags" value={stats.tags} suffix="+" index={1} />
          <CounterCard label="Categories" value={stats.categories} index={2} />
          <CounterCard label="Avg Trust Score" value={stats.avgTrust} suffix="%" index={3} />
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section className="w-full max-w-6xl px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Everything you need, <span className="text-gradient">verified</span>
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-gray-500">
            An autonomous system that replaces hours of manual research with
            AI-powered intelligence.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              whileHover={{ y: -4, borderColor: "rgba(139,92,246,0.3)" }}
              className="group rounded-2xl border border-white/5 bg-card/80 p-8 backdrop-blur-sm transition-colors"
            >
              <div className="mb-4 inline-flex rounded-xl bg-accent/10 p-3 text-accent transition-colors group-hover:bg-accent/20">
                {f.icon}
              </div>
              <h3 className="text-xl font-semibold text-white">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-400">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Pipeline ─────────────────────────────────────────── */}
      <section className="w-full max-w-5xl px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            How it <span className="text-gradient">works</span>
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-gray-500">
            Submit a URL and the engine handles the rest — fully autonomous,
            end-to-end.
          </p>
        </motion.div>

        <div className="mt-16 flex flex-col gap-0">
          {pipeline.map((step, i) => (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="flex items-center gap-6 py-4"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-accent/20 bg-accent/5 text-accent">
                {step.icon}
              </div>
              {/* connector line */}
              <div className="hidden h-px flex-1 bg-gradient-to-r from-accent/20 to-transparent sm:block" />
              <div className="min-w-0 flex-1 sm:flex-none">
                <p className="text-sm font-semibold text-white">{step.label}</p>
                <p className="text-xs text-gray-500">{step.detail}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <section className="w-full max-w-3xl px-6 py-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Start exploring <span className="text-gradient">now</span>
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-gray-500">
            Search the knowledge base, compare tools, or submit a new URL for
            analysis.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <a
              href="/submit"
              className="rounded-xl bg-gradient-accent px-8 py-3 text-sm font-medium text-white transition hover:opacity-90"
            >
              Submit Tool
            </a>
            <a
              href="/search"
              className="rounded-xl border border-white/10 px-8 py-3 text-sm font-medium text-gray-400 transition hover:border-accent/30 hover:text-white"
            >
              Search Tools
            </a>
            <a
              href="/saved"
              className="rounded-xl border border-white/10 px-8 py-3 text-sm font-medium text-gray-400 transition hover:border-accent/30 hover:text-white"
            >
              Saved Tools
            </a>
          </div>
        </motion.div>
      </section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="w-full border-t border-white/5 py-8 text-center text-xs text-gray-600">
        TruthEngine AI — Autonomous AI Knowledge Engine
      </footer>
    </div>
  );
}
