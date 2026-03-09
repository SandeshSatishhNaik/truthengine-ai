"use client";

import { motion } from "framer-motion";
import type { Tool } from "@/lib/api";
import { TagChip } from "./TagChip";
import { PricingBadge } from "./PricingBadge";

export function ToolCard({ tool, index = 0 }: { tool: Tool; index?: number }) {
  const score = tool.trust_score ?? 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
      whileHover={{ y: -4, boxShadow: "0 0 30px rgba(139,92,246,0.12)" }}
      className="group rounded-2xl border border-white/5 bg-card p-6 transition-colors hover:border-accent/30"
    >
      <div className="flex items-start justify-between">
        <div>
          <a
            href={`/tool/${tool.id}`}
            className="text-lg font-semibold text-white group-hover:text-gradient transition-colors"
          >
            {tool.name}
          </a>
          {tool.category && (
            <p className="mt-1 text-xs text-gray-500 uppercase tracking-wider">
              {tool.category}
            </p>
          )}
        </div>
        <PricingBadge model={tool.pricing_model} />
      </div>

      {tool.core_function && (
        <p className="mt-3 text-sm text-gray-400 line-clamp-2">
          {tool.core_function}
        </p>
      )}

      {tool.free_tier_limits && (
        <p className="mt-2 text-xs text-gray-500">
          Free tier: {tool.free_tier_limits}
        </p>
      )}

      <div className="mt-4 flex items-center justify-between">
        <div className="flex flex-wrap gap-1.5">
          {(tool.tags ?? []).slice(0, 4).map((tag) => (
            <TagChip key={tag} label={tag} />
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-xs">
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
          <span className="text-gray-500">{(score * 100).toFixed(0)}%</span>
        </div>
      </div>
    </motion.div>
  );
}
