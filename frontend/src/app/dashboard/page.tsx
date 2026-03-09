"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Database, Search, Globe, TrendingUp } from "lucide-react";
import { ToolCard } from "@/components/ToolCard";
import { StatCard } from "@/components/StatCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { getTools, type Tool } from "@/lib/api";

export default function DashboardPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTools(undefined, 200)
      .then(setTools)
      .catch(() => setTools([]))
      .finally(() => setLoading(false));
  }, []);

  const avgTrust =
    tools.length > 0
      ? tools.reduce((sum, t) => sum + (t.trust_score || 0), 0) / tools.length
      : 0;

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold text-white"
      >
        Dashboard
      </motion.h1>
      <p className="mt-1 text-gray-500">Knowledge base overview</p>

      {/* Stats */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Tools"
          value={tools.length}
          icon={<Database className="h-5 w-5" />}
          index={0}
        />
        <StatCard
          label="Categories"
          value={new Set(tools.map((t) => t.category).filter(Boolean)).size}
          icon={<Globe className="h-5 w-5" />}
          index={1}
        />
        <StatCard
          label="Avg Trust"
          value={`${(avgTrust * 100).toFixed(0)}%`}
          icon={<TrendingUp className="h-5 w-5" />}
          index={2}
        />
        <StatCard
          label="Searchable"
          value={tools.length}
          icon={<Search className="h-5 w-5" />}
          index={3}
        />
      </div>

      {/* Tool Grid */}
      <h2 className="mt-12 text-xl font-semibold text-white">Recent Tools</h2>
      <div className="mt-4">
        {loading ? (
          <LoadingSkeleton count={6} />
        ) : tools.length === 0 ? (
          <p className="text-gray-500">
            No tools yet. Submit a URL via the API or Telegram bot to get started.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tools.slice(0, 12).map((tool, i) => (
              <ToolCard key={tool.id} tool={tool} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
