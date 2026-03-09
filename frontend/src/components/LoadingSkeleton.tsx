"use client";

import { motion } from "framer-motion";

export function LoadingSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.15 }}
          className="rounded-2xl border border-white/5 bg-card p-6"
        >
          <div className="h-5 w-2/3 rounded bg-white/5" />
          <div className="mt-3 h-3 w-full rounded bg-white/5" />
          <div className="mt-2 h-3 w-4/5 rounded bg-white/5" />
          <div className="mt-4 flex gap-2">
            <div className="h-5 w-12 rounded-md bg-white/5" />
            <div className="h-5 w-16 rounded-md bg-white/5" />
          </div>
        </motion.div>
      ))}
    </div>
  );
}
