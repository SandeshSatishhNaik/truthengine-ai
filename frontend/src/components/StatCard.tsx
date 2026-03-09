"use client";

import { motion } from "framer-motion";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  index?: number;
}

export function StatCard({ label, value, icon, index = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className="rounded-2xl border border-white/5 bg-card p-6"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{label}</p>
        {icon && <div className="text-accent">{icon}</div>}
      </div>
      <p className="mt-2 text-3xl font-bold text-gradient">{value}</p>
    </motion.div>
  );
}
