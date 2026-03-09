"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Tags,
  Activity,
  Clock,
  Database,
  Zap,
  RefreshCw,
  Server,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { getTools, getSystemMetrics, type Tool, type SystemMetrics } from "@/lib/api";

/* ─── Animated metric card ───────────────────────────────────────── */

function MetricCard({
  label,
  value,
  sub,
  icon,
  trend,
  delay = 0,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | null;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="rounded-2xl border border-white/5 bg-card p-5"
    >
      <div className="flex items-start justify-between">
        <span className="rounded-lg bg-white/5 p-2 text-accent">{icon}</span>
        {trend && (
          <span
            className={`flex items-center gap-0.5 text-xs ${trend === "up" ? "text-green-400" : "text-red-400"}`}
          >
            {trend === "up" ? (
              <ArrowUp className="h-3 w-3" />
            ) : (
              <ArrowDown className="h-3 w-3" />
            )}
          </span>
        )}
      </div>
      <p className="mt-3 text-2xl font-bold text-white">{value}</p>
      <p className="mt-0.5 text-xs text-gray-500">{label}</p>
      {sub && <p className="mt-1 text-[11px] text-gray-600">{sub}</p>}
    </motion.div>
  );
}

/* ─── Horizontal bar ─────────────────────────────────────────────── */

function HBar({
  label,
  value,
  max,
  gradient,
}: {
  label: string;
  value: number;
  max: number;
  gradient: string;
}) {
  const pct = max === 0 ? 0 : (value / max) * 100;
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 truncate text-sm text-gray-400">{label}</span>
      <div className="flex-1">
        <div className="h-2 rounded-full bg-white/5">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className={`h-2 rounded-full bg-gradient-to-r ${gradient}`}
          />
        </div>
      </div>
      <span className="w-8 text-right text-sm text-gray-400">{value}</span>
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */

export default function AnalyticsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    try {
      const [t, m] = await Promise.all([
        getTools(undefined, 100).catch(() => [] as Tool[]),
        getSystemMetrics().catch(() => null),
      ]);
      setTools(t);
      setMetrics(m);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  /* Derived tool analytics */
  const categories = tools.reduce<Record<string, number>>((acc, t) => {
    const cat = t.category || "uncategorized";
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});

  const pricingModels = tools.reduce<Record<string, number>>((acc, t) => {
    const model = t.pricing_model || "unknown";
    acc[model] = (acc[model] || 0) + 1;
    return acc;
  }, {});

  const allTags = tools.flatMap((t) => t.tags || []);
  const tagCounts = allTags.reduce<Record<string, number>>((acc, tag) => {
    acc[tag] = (acc[tag] || 0) + 1;
    return acc;
  }, {});
  const topTags = Object.entries(tagCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 12);

  const avgTrust =
    tools.length > 0
      ? tools.reduce((s, t) => s + (t.trust_score || 0), 0) / tools.length
      : 0;

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex items-center gap-3 text-gray-500">
          <Activity className="h-4 w-4 animate-pulse" />
          Loading analytics...
        </div>
      </div>
    );
  }

  const req = metrics?.requests;
  const cache = metrics?.cache;
  const uptime = metrics?.uptime_seconds;

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold text-white"
          >
            Analytics
          </motion.h1>
          <p className="mt-1 text-gray-500">
            Knowledge base &amp; system performance
          </p>
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 rounded-xl border border-white/5 px-4 py-2 text-sm text-gray-400 transition hover:border-white/10 hover:text-white disabled:opacity-40"
        >
          <RefreshCw
            className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
          />
          Refresh
        </button>
      </div>

      {/* ─── KPI Row ─────────────────────────────────────────── */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total Tools"
          value={tools.length}
          icon={<Database className="h-5 w-5" />}
          delay={0}
        />
        <MetricCard
          label="Categories"
          value={Object.keys(categories).length}
          icon={<PieChart className="h-5 w-5" />}
          delay={0.05}
        />
        <MetricCard
          label="Avg Trust Score"
          value={`${(avgTrust * 100).toFixed(0)}%`}
          icon={<TrendingUp className="h-5 w-5" />}
          trend={avgTrust >= 0.7 ? "up" : avgTrust > 0 ? "down" : null}
          delay={0.1}
        />
        <MetricCard
          label="Unique Tags"
          value={Object.keys(tagCounts).length}
          icon={<Tags className="h-5 w-5" />}
          delay={0.15}
        />
      </div>

      {/* ─── System Metrics Row (if available) ───────────────── */}
      {metrics && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Total Requests"
            value={req?.total ?? 0}
            sub={`${req?.active ?? 0} active`}
            icon={<Activity className="h-5 w-5" />}
            delay={0.2}
          />
          <MetricCard
            label="Avg Latency"
            value={
              req?.latency?.avg
                ? `${(req.latency.avg * 1000).toFixed(0)}ms`
                : "—"
            }
            icon={<Clock className="h-5 w-5" />}
            delay={0.25}
          />
          <MetricCard
            label="Cache Hit Rate"
            value={
              cache && cache?.hits + cache?.misses > 0
                ? `${((cache.hits / (cache.hits + cache.misses)) * 100).toFixed(0)}%`
                : "—"
            }
            sub={`${cache?.hits ?? 0} hits / ${cache?.misses ?? 0} misses`}
            icon={<Zap className="h-5 w-5" />}
            trend={
              cache && cache.hits + cache.misses > 0
                ? cache.hits / (cache.hits + cache.misses) > 0.5
                  ? "up"
                  : "down"
                : null
            }
            delay={0.3}
          />
          <MetricCard
            label="Uptime"
            value={
              uptime ? `${(uptime / 3600).toFixed(1)}h` : "—"
            }
            icon={<Server className="h-5 w-5" />}
            delay={0.35}
          />
        </div>
      )}

      {/* ─── Charts Grid ────────────────────────────────────── */}
      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        {/* Category bar chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl border border-white/5 bg-card p-6"
        >
          <h3 className="flex items-center gap-2 text-base font-semibold text-white">
            <BarChart3 className="h-4 w-4 text-accent" />
            Tools by Category
          </h3>
          <div className="mt-5 space-y-3">
            {Object.entries(categories)
              .sort(([, a], [, b]) => b - a)
              .map(([cat, count]) => (
                <HBar
                  key={cat}
                  label={cat}
                  value={count}
                  max={tools.length}
                  gradient="from-purple-500 to-blue-500"
                />
              ))}
          </div>
        </motion.div>

        {/* Pricing model bar chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-2xl border border-white/5 bg-card p-6"
        >
          <h3 className="flex items-center gap-2 text-base font-semibold text-white">
            <PieChart className="h-4 w-4 text-green-400" />
            Pricing Models
          </h3>
          <div className="mt-5 space-y-3">
            {Object.entries(pricingModels)
              .sort(([, a], [, b]) => b - a)
              .map(([model, count]) => (
                <HBar
                  key={model}
                  label={model}
                  value={count}
                  max={tools.length}
                  gradient="from-green-500 to-emerald-400"
                />
              ))}
          </div>
        </motion.div>
      </div>

      {/* ─── Agent Performance (if metrics available) ────────── */}
      {metrics?.agents && Object.keys(metrics.agents).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 rounded-2xl border border-white/5 bg-card p-6"
        >
          <h3 className="flex items-center gap-2 text-base font-semibold text-white">
            <Zap className="h-4 w-4 text-yellow-400" />
            Agent Performance
          </h3>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="pb-3 text-xs font-medium uppercase tracking-wider text-gray-500">
                    Agent
                  </th>
                  <th className="pb-3 text-xs font-medium uppercase tracking-wider text-gray-500">
                    Calls
                  </th>
                  <th className="pb-3 text-xs font-medium uppercase tracking-wider text-gray-500">
                    Success
                  </th>
                  <th className="pb-3 text-xs font-medium uppercase tracking-wider text-gray-500">
                    Errors
                  </th>
                  <th className="pb-3 text-xs font-medium uppercase tracking-wider text-gray-500">
                    Avg Time
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.agents).map(([name, data]) => (
                    <tr
                      key={name}
                      className="border-b border-white/5 transition-colors hover:bg-white/[0.02]"
                    >
                      <td className="py-3 font-medium text-white capitalize">
                        {name.replace(/_/g, " ")}
                      </td>
                      <td className="py-3 text-gray-300">
                        {data.calls ?? 0}
                      </td>
                      <td className="py-3 text-green-400">
                        {Math.max(0, (data.calls ?? 0) - (data.errors ?? 0))}
                      </td>
                      <td className="py-3 text-red-400">
                        {data.errors ?? 0}
                      </td>
                      <td className="py-3 text-gray-300">
                        {data.latency?.avg
                          ? `${(data.latency.avg * 1000).toFixed(0)}ms`
                          : "—"}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* ─── Top Tags ────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-8 rounded-2xl border border-white/5 bg-card p-6"
      >
        <h3 className="flex items-center gap-2 text-base font-semibold text-white">
          <Tags className="h-4 w-4 text-accent" />
          Top Tags
        </h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {topTags.map(([tag, count], i) => (
            <motion.span
              key={tag}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + i * 0.03 }}
              className="rounded-xl border border-accent/10 bg-accent/5 px-3 py-1.5 text-sm text-accent"
            >
              {tag}{" "}
              <span className="ml-0.5 text-xs text-gray-600">({count})</span>
            </motion.span>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
