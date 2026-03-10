"use client";

import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Trash2,
  SlidersHorizontal,
  ArrowUpDown,
  Tag,
  Grid3X3,
  List,
  X,
  ExternalLink,
  Loader2,
  Database,
  Pencil,
  Check,
  Calendar,
} from "lucide-react";
import { getTools, deleteTool, updateTool, type Tool } from "@/lib/api";
import { TagChip } from "@/components/TagChip";
import { PricingBadge } from "@/components/PricingBadge";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";

/* ─── Types ─────────────────────────────────────────────────────── */

type SortKey = "name" | "trust_score" | "created_at" | "category";
type SortDir = "asc" | "desc";
type ViewMode = "grid" | "list";
type DateRange = "" | "today" | "yesterday" | "this_week" | "this_month" | "older";

function formatToolDate(dateStr?: string): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
  const monthDay = date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const time = date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  if (diffDays === 0) return `Today, ${time}`;
  if (diffDays === 1) return `Yesterday, ${time}`;
  if (diffDays < 7) return `${dayName}, ${monthDay}`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function getDateRange(dateStr?: string): DateRange {
  if (!dateStr) return "older";
  const date = new Date(dateStr);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday.getTime() - 86400000);
  const startOfWeek = new Date(startOfToday.getTime() - startOfToday.getDay() * 86400000);
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  if (date >= startOfToday) return "today";
  if (date >= startOfYesterday) return "yesterday";
  if (date >= startOfWeek) return "this_week";
  if (date >= startOfMonth) return "this_month";
  return "older";
}

const PREDEFINED_CATEGORIES = [
  "AI Assistants",
  "Code Generation",
  "Image Generation",
  "Video Generation",
  "Audio & Music",
  "Writing & Content",
  "Data & Analytics",
  "DevOps & Infrastructure",
  "Search & Research",
  "Chatbots & Agents",
  "Design & UI",
  "Productivity",
  "Education & Learning",
  "Marketing & SEO",
  "Translation & Language",
  "API & Platform",
  "Open Source Tools",
  "Other",
] as const;

/* ─── Page ──────────────────────────────────────────────────────── */

export default function SavedToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedPricing, setSelectedPricing] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [minTrust, setMinTrust] = useState(0);
  const [dateRange, setDateRange] = useState<DateRange>("");

  // Sort & View
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [showFilters, setShowFilters] = useState(false);

  // Fetch tools
  useEffect(() => {
    getTools(undefined, 100)
      .then(setTools)
      .catch(() => setTools([]))
      .finally(() => setLoading(false));
  }, []);

  // Derived data
  // Categories that actually exist in tools (for filtering)
  const filterCategories = useMemo(() => {
    const counts = new Map<string, number>();
    tools.forEach((t) => {
      const cat = t.category || "uncategorized";
      counts.set(cat, (counts.get(cat) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [tools]);

  // All predefined categories (for inline edit dropdowns)
  const editCategories = useMemo(
    () =>
      [
        ...new Set([
          ...PREDEFINED_CATEGORIES,
          ...tools.map((t) => t.category).filter((c): c is string => !!c && c !== "uncategorized"),
        ]),
      ].sort(),
    [tools]
  );

  const pricingModels = useMemo(() => {
    const counts = new Map<string, number>();
    tools.forEach((t) => {
      if (t.pricing_model) counts.set(t.pricing_model, (counts.get(t.pricing_model) ?? 0) + 1);
    });
    return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [tools]);

  const allTags = useMemo(() => {
    const counts = new Map<string, number>();
    tools.forEach((t) => (t.tags ?? []).forEach((tag) => counts.set(tag, (counts.get(tag) ?? 0) + 1)));
    return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [tools]);

  // Filter + sort
  const filtered = useMemo(() => {
    let result = tools;

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          t.core_function?.toLowerCase().includes(q) ||
          t.tags?.some((tag) => tag.toLowerCase().includes(q))
      );
    }
    if (selectedCategory) result = result.filter((t) => (t.category || "uncategorized") === selectedCategory);
    if (selectedPricing) result = result.filter((t) => t.pricing_model === selectedPricing);
    if (selectedTag) result = result.filter((t) => t.tags?.includes(selectedTag));
    if (minTrust > 0) result = result.filter((t) => (t.trust_score ?? 0) >= minTrust / 100);
    if (dateRange) result = result.filter((t) => getDateRange(t.created_at) === dateRange);

    result = [...result].sort((a, b) => {
      let cmp = 0;
      if (sortKey === "name") cmp = a.name.localeCompare(b.name);
      else if (sortKey === "trust_score") cmp = (a.trust_score ?? 0) - (b.trust_score ?? 0);
      else if (sortKey === "created_at") cmp = (a.created_at ?? "").localeCompare(b.created_at ?? "");
      else if (sortKey === "category") cmp = (a.category ?? "").localeCompare(b.category ?? "");
      return sortDir === "asc" ? cmp : -cmp;
    });

    return result;
  }, [tools, search, selectedCategory, selectedPricing, selectedTag, minTrust, dateRange, sortKey, sortDir]);

  // Delete handler
  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    setDeleting(id);
    try {
      await deleteTool(id);
      setTools((prev) => prev.filter((t) => t.id !== id));
    } catch {
      alert("Failed to delete tool.");
    } finally {
      setDeleting(null);
    }
  };

  const handleCategoryChange = async (id: string, category: string) => {
    try {
      await updateTool(id, { category });
      setTools((prev) =>
        prev.map((t) => (t.id === id ? { ...t, category } : t))
      );
    } catch {
      alert("Failed to update category.");
    }
  };

  const clearFilters = () => {
    setSearch("");
    setSelectedCategory(null);
    setSelectedPricing(null);
    setSelectedTag(null);
    setMinTrust(0);
    setDateRange("");
  };

  const activeFilterCount = [selectedCategory, selectedPricing, selectedTag, minTrust > 0 ? true : null, dateRange || null].filter(Boolean).length;

  // Date range counts
  const dateRangeCounts = useMemo(() => {
    const counts: Record<string, number> = { today: 0, yesterday: 0, this_week: 0, this_month: 0, older: 0 };
    tools.forEach((t) => {
      const r = getDateRange(t.created_at);
      if (r) counts[r] = (counts[r] || 0) + 1;
    });
    return counts;
  }, [tools]);

  return (
    <main className="min-h-screen bg-background pt-24 pb-16">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3">
            <Database className="h-8 w-8 text-accent" />
            <h1 className="text-3xl font-bold text-white sm:text-4xl">
              Saved <span className="text-gradient">Tools</span>
            </h1>
          </div>
          <p className="mt-2 text-gray-500">
            {tools.length} tool{tools.length !== 1 ? "s" : ""} in your knowledge base
          </p>
        </motion.div>

        {/* Toolbar */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tools by name, function, or tag..."
              className="w-full rounded-xl border border-white/10 bg-card py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-gray-600 focus:border-accent/40 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            {/* Filter toggle */}
            <button
              onClick={() => setShowFilters((p) => !p)}
              className={`flex items-center gap-1.5 rounded-xl border px-3 py-2 text-sm transition ${
                showFilters || activeFilterCount > 0
                  ? "border-accent/40 bg-accent/10 text-accent"
                  : "border-white/10 text-gray-400 hover:border-white/20 hover:text-white"
              }`}
            >
              <SlidersHorizontal className="h-4 w-4" />
              Filters
              {activeFilterCount > 0 && (
                <span className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-accent text-xs text-white">
                  {activeFilterCount}
                </span>
              )}
            </button>

            {/* Sort */}
            <div className="flex items-center gap-1 rounded-xl border border-white/10 px-1">
              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value as SortKey)}
                className="bg-transparent py-2 pl-2 pr-1 text-sm text-gray-400 focus:outline-none"
              >
                <option value="created_at">Date Added</option>
                <option value="name">Name</option>
                <option value="trust_score">Trust Score</option>
                <option value="category">Category</option>
              </select>
              <button
                onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                className="rounded-lg p-1.5 text-gray-400 hover:text-white"
                title={sortDir === "asc" ? "Ascending" : "Descending"}
              >
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </div>

            {/* View mode */}
            <div className="flex rounded-xl border border-white/10">
              <button
                onClick={() => setViewMode("grid")}
                className={`rounded-l-xl p-2 text-sm transition ${viewMode === "grid" ? "bg-white/10 text-white" : "text-gray-500 hover:text-white"}`}
              >
                <Grid3X3 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`rounded-r-xl p-2 text-sm transition ${viewMode === "list" ? "bg-white/10 text-white" : "text-gray-500 hover:text-white"}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </motion.div>

        {/* Filter panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 overflow-hidden"
            >
              <div className="rounded-2xl border border-white/10 bg-card p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white">Smart Filters</h3>
                  {activeFilterCount > 0 && (
                    <button onClick={clearFilters} className="text-xs text-accent hover:underline">
                      Clear all
                    </button>
                  )}
                </div>

                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
                  {/* Date Added */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date Added
                    </label>
                    <select
                      value={dateRange}
                      onChange={(e) => setDateRange(e.target.value as DateRange)}
                      className="w-full rounded-lg border border-white/10 bg-background px-3 py-2 text-sm text-white focus:border-accent/40 focus:outline-none"
                    >
                      <option value="">All Dates</option>
                      {dateRangeCounts.today > 0 && <option value="today">Today ({dateRangeCounts.today})</option>}
                      {dateRangeCounts.yesterday > 0 && <option value="yesterday">Yesterday ({dateRangeCounts.yesterday})</option>}
                      {dateRangeCounts.this_week > 0 && <option value="this_week">This Week ({dateRangeCounts.this_week})</option>}
                      {dateRangeCounts.this_month > 0 && <option value="this_month">This Month ({dateRangeCounts.this_month})</option>}
                      {dateRangeCounts.older > 0 && <option value="older">Older ({dateRangeCounts.older})</option>}
                    </select>
                  </div>

                  {/* Category */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </label>
                    <select
                      value={selectedCategory ?? ""}
                      onChange={(e) => setSelectedCategory(e.target.value || null)}
                      className="w-full rounded-lg border border-white/10 bg-background px-3 py-2 text-sm text-white focus:border-accent/40 focus:outline-none"
                    >
                      <option value="">All Categories</option>
                      {filterCategories.map(([c, count]) => (
                        <option key={c} value={c}>
                          {c} ({count})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Pricing */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Pricing Model
                    </label>
                    <select
                      value={selectedPricing ?? ""}
                      onChange={(e) => setSelectedPricing(e.target.value || null)}
                      className="w-full rounded-lg border border-white/10 bg-background px-3 py-2 text-sm text-white focus:border-accent/40 focus:outline-none"
                    >
                      <option value="">All Pricing</option>
                      {pricingModels.map(([p, count]) => (
                        <option key={p} value={p}>
                          {p} ({count})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Tags */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tag
                    </label>
                    <select
                      value={selectedTag ?? ""}
                      onChange={(e) => setSelectedTag(e.target.value || null)}
                      className="w-full rounded-lg border border-white/10 bg-background px-3 py-2 text-sm text-white focus:border-accent/40 focus:outline-none"
                    >
                      <option value="">All Tags</option>
                      {allTags.map(([t, count]) => (
                        <option key={t} value={t}>
                          {t} ({count})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Trust score */}
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Min Trust Score: {minTrust}%
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={5}
                      value={minTrust}
                      onChange={(e) => setMinTrust(Number(e.target.value))}
                      className="w-full accent-accent"
                    />
                    <div className="flex justify-between text-xs text-gray-600">
                      <span>0%</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Active filter chips */}
        {activeFilterCount > 0 && (
          <div className="mb-5 flex flex-wrap gap-2">
            {selectedCategory && (
              <FilterChip label={`Category: ${selectedCategory}`} onRemove={() => setSelectedCategory(null)} />
            )}
            {selectedPricing && (
              <FilterChip label={`Pricing: ${selectedPricing}`} onRemove={() => setSelectedPricing(null)} />
            )}
            {selectedTag && (
              <FilterChip label={`Tag: ${selectedTag}`} onRemove={() => setSelectedTag(null)} />
            )}
            {minTrust > 0 && (
              <FilterChip label={`Trust ≥ ${minTrust}%`} onRemove={() => setMinTrust(0)} />
            )}
            {dateRange && (
              <FilterChip
                label={`Date: ${dateRange === "today" ? "Today" : dateRange === "yesterday" ? "Yesterday" : dateRange === "this_week" ? "This Week" : dateRange === "this_month" ? "This Month" : "Older"}`}
                onRemove={() => setDateRange("")}
              />
            )}
          </div>
        )}

        {/* Results count */}
        {!loading && (
          <p className="mb-4 text-xs text-gray-600">
            Showing {filtered.length} of {tools.length} tool{tools.length !== 1 ? "s" : ""}
          </p>
        )}

        {/* Content */}
        {loading ? (
          <LoadingSkeleton count={6} />
        ) : filtered.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="py-20 text-center">
            <Database className="mx-auto h-12 w-12 text-gray-700" />
            <p className="mt-4 text-gray-500">
              {tools.length === 0
                ? "No tools saved yet. Submit a URL to get started."
                : "No tools match your filters."}
            </p>
            {tools.length > 0 && (
              <button onClick={clearFilters} className="mt-3 text-sm text-accent hover:underline">
                Clear filters
              </button>
            )}
          </motion.div>
        ) : viewMode === "grid" ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence>
              {filtered.map((tool, i) => (
                <GridCard
                  key={tool.id}
                  tool={tool}
                  index={i}
                  deleting={deleting === tool.id}
                  onDelete={() => handleDelete(tool.id, tool.name)}
                  categories={editCategories}
                  onCategoryChange={(cat) => handleCategoryChange(tool.id, cat)}
                />
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <div className="space-y-2">
            <AnimatePresence>
              {filtered.map((tool, i) => (
                <ListRow
                  key={tool.id}
                  tool={tool}
                  index={i}
                  deleting={deleting === tool.id}
                  onDelete={() => handleDelete(tool.id, tool.name)}
                  categories={editCategories}
                  onCategoryChange={(cat) => handleCategoryChange(tool.id, cat)}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </main>
  );
}

/* ─── Grid Card ─────────────────────────────────────────────────── */

function GridCard({
  tool,
  index,
  deleting,
  onDelete,
  categories,
  onCategoryChange,
}: {
  tool: Tool;
  index: number;
  deleting: boolean;
  onDelete: () => void;
  categories: string[];
  onCategoryChange: (cat: string) => void;
}) {
  const score = tool.trust_score ?? 0;
  const [editingCat, setEditingCat] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3, delay: Math.min(index * 0.03, 0.3) }}
      whileHover={{ y: -4, boxShadow: "0 0 30px rgba(139,92,246,0.12)" }}
      className="group/card relative rounded-2xl border border-white/5 bg-card p-6 transition-colors hover:border-accent/30"
    >
      {/* Delete button */}
      <button
        onClick={(e) => { e.preventDefault(); onDelete(); }}
        disabled={deleting}
        className="absolute top-3 right-3 z-10 rounded-lg bg-red-500/10 p-1.5 text-red-400 opacity-0 transition-all hover:bg-red-500/20 hover:text-red-300 group-hover/card:opacity-100 disabled:opacity-50"
        title="Delete tool"
      >
        {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
      </button>

      <div className="flex items-start justify-between pr-8">
        <div>
          <a
            href={`/tool/${tool.id}`}
            className="text-lg font-semibold text-white transition-colors hover:text-gradient"
          >
            {tool.name}
          </a>
          {/* Inline category editing */}
          <div className="mt-1 flex items-center gap-1">
            {editingCat ? (
              <select
                autoFocus
                className="rounded bg-white/5 px-2 py-0.5 text-xs text-gray-300 outline-none ring-1 ring-accent/40"
                defaultValue={tool.category || ""}
                onChange={(e) => {
                  onCategoryChange(e.target.value);
                  setEditingCat(false);
                }}
                onBlur={() => setEditingCat(false)}
              >
                <option value="" disabled>Select category</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            ) : (
              <>
                <p className="text-xs text-gray-500 uppercase tracking-wider">
                  {tool.category || "uncategorized"}
                </p>
                <button
                  onClick={() => setEditingCat(true)}
                  className="rounded p-0.5 text-gray-600 opacity-0 transition hover:text-accent group-hover/card:opacity-100"
                  title="Change category"
                >
                  <Pencil className="h-3 w-3" />
                </button>
              </>
            )}
          </div>
        </div>
        <PricingBadge model={tool.pricing_model} />
      </div>

      {tool.created_at && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-gray-600">
          <Calendar className="h-3 w-3" />
          {formatToolDate(tool.created_at)}
        </div>
      )}

      {tool.core_function && (
        <p className="mt-2 text-sm text-gray-400 line-clamp-2">{tool.core_function}</p>
      )}

      {tool.free_tier_limits && (
        <p className="mt-2 text-xs text-gray-500">Free tier: {tool.free_tier_limits}</p>
      )}

      <div className="mt-4 flex items-center justify-between">
        <div className="flex flex-wrap gap-1.5">
          {(tool.tags ?? []).slice(0, 4).map((tag) => (
            <TagChip key={tag} label={tag} />
          ))}
        </div>
        <TrustDot score={score} />
      </div>

      {/* Bottom actions */}
      <div className="mt-4 flex items-center gap-2 border-t border-white/5 pt-3">
        <a
          href={`/tool/${tool.id}`}
          className="flex-1 rounded-lg bg-accent/10 py-1.5 text-center text-xs font-medium text-accent transition hover:bg-accent/20"
        >
          View Details
        </a>
        {tool.website && (
          <a
            href={tool.website}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-white/10 p-1.5 text-gray-500 transition hover:border-white/20 hover:text-white"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
      </div>
    </motion.div>
  );
}

/* ─── List Row ──────────────────────────────────────────────────── */

function ListRow({
  tool,
  index,
  deleting,
  onDelete,
  categories,
  onCategoryChange,
}: {
  tool: Tool;
  index: number;
  deleting: boolean;
  onDelete: () => void;
  categories: string[];
  onCategoryChange: (cat: string) => void;
}) {
  const score = tool.trust_score ?? 0;
  const [editingCat, setEditingCat] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.3) }}
      className="group/row flex items-center gap-4 rounded-xl border border-white/5 bg-card px-5 py-4 transition-colors hover:border-accent/20"
    >
      {/* Trust dot */}
      <TrustDot score={score} />

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <a href={`/tool/${tool.id}`} className="truncate font-semibold text-white hover:text-gradient">
            {tool.name}
          </a>
          <PricingBadge model={tool.pricing_model} />
          {tool.created_at && (
            <span className="hidden items-center gap-1 text-xs text-gray-600 sm:inline-flex">
              <Calendar className="h-3 w-3" />
              {formatToolDate(tool.created_at)}
            </span>
          )}
        </div>
        {tool.core_function && (
          <p className="mt-0.5 truncate text-sm text-gray-500">{tool.core_function}</p>
        )}
      </div>

      {/* Category (inline editable) */}
      <div className="hidden items-center gap-1 md:flex">
        {editingCat ? (
          <select
            autoFocus
            className="rounded bg-white/5 px-2 py-0.5 text-xs text-gray-300 outline-none ring-1 ring-accent/40"
            defaultValue={tool.category || ""}
            onChange={(e) => {
              onCategoryChange(e.target.value);
              setEditingCat(false);
            }}
            onBlur={() => setEditingCat(false)}
          >
            <option value="" disabled>Select category</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        ) : (
          <>
            <span className="text-xs text-gray-600 uppercase tracking-wider">
              {tool.category || "uncategorized"}
            </span>
            <button
              onClick={() => setEditingCat(true)}
              className="rounded p-0.5 text-gray-600 opacity-0 transition hover:text-accent group-hover/row:opacity-100"
              title="Change category"
            >
              <Pencil className="h-3 w-3" />
            </button>
          </>
        )}
      </div>

      {/* Tags */}
      <div className="hidden gap-1 lg:flex">
        {(tool.tags ?? []).slice(0, 3).map((tag) => (
          <TagChip key={tag} label={tag} />
        ))}
      </div>

      {/* Score */}
      <span className="w-12 text-right text-sm font-medium text-gray-400">
        {(score * 100).toFixed(0)}%
      </span>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <a
          href={`/tool/${tool.id}`}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-white/5 hover:text-white"
          title="View details"
        >
          <ExternalLink className="h-4 w-4" />
        </a>
        <button
          onClick={onDelete}
          disabled={deleting}
          className="rounded-lg p-2 text-gray-500 transition hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
          title="Delete tool"
        >
          {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
        </button>
      </div>
    </motion.div>
  );
}

/* ─── Helpers ───────────────────────────────────────────────────── */

function TrustDot({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <div
        className="h-2 w-2 rounded-full"
        style={{
          background: score > 0.7 ? "#22c55e" : score > 0.4 ? "#eab308" : "#ef4444",
        }}
      />
      <span className="text-gray-500">{(score * 100).toFixed(0)}%</span>
    </div>
  );
}

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="inline-flex items-center gap-1.5 rounded-full border border-accent/20 bg-accent/5 px-3 py-1 text-xs text-accent"
    >
      <Tag className="h-3 w-3" />
      {label}
      <button onClick={onRemove} className="ml-0.5 hover:text-white">
        <X className="h-3 w-3" />
      </button>
    </motion.span>
  );
}
