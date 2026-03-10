const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const API_ROOT = process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1$/, "") || "http://localhost:8000";

async function fetchWithRetry(url: string, options?: RequestInit, retries = 2): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, options);
      if (res.ok || i === retries) return res;
    } catch {
      if (i === retries) throw new Error("Network error");
      await new Promise((r) => setTimeout(r, 2000 * (i + 1)));
    }
  }
  throw new Error("Network error");
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetchWithRetry(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || res.statusText);
  }
  return res.json();
}

async function rootFetch<T>(path: string): Promise<T> {
  const res = await fetchWithRetry(`${API_ROOT}${path}`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

// Types
export interface Tool {
  id: string;
  name: string;
  website?: string;
  category?: string;
  core_function?: string;
  pricing_model?: string;
  free_tier_limits?: string;
  community_verdict?: string;
  trust_score?: number;
  tags?: string[];
  created_at?: string;
}

export interface SearchResult {
  tool: Tool;
  similarity: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  answer?: string;
}

export interface ComparisonResponse {
  tools: Tool[];
  comparison_text: string;
}

export interface AlternativeTool {
  tool: Tool;
  similarity: number | null;
  source: string; // "knowledge_base" | "web_discovery"
}

export interface AnalysisReport {
  tool: Tool;
  alternatives: AlternativeTool[];
  comparison: string | null;
}

// API functions
export async function getTools(category?: string, limit = 20): Promise<Tool[]> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  params.set("limit", String(limit));
  return apiFetch<Tool[]>(`/tools?${params}`);
}

export async function getTool(id: string): Promise<Tool> {
  return apiFetch<Tool>(`/tools/${encodeURIComponent(id)}`);
}

export async function deleteTool(id: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`/tools/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export async function updateTool(
  id: string,
  data: { category?: string; pricing_model?: string; tags?: string[] }
): Promise<Tool> {
  return apiFetch<Tool>(`/tools/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function searchTools(query: string, limit = 10): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/search", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
}

export async function ingestURL(url: string, category?: string): Promise<AnalysisReport> {
  return apiFetch<AnalysisReport>("/ingest", {
    method: "POST",
    body: JSON.stringify({ url, category }),
  });
}

export async function compareTools(toolIds: string[]): Promise<ComparisonResponse> {
  return apiFetch<ComparisonResponse>("/compare", {
    method: "POST",
    body: JSON.stringify({ tool_ids: toolIds }),
  });
}

export async function searchSimilar(query: string, limit = 5): Promise<SearchResult[]> {
  const res = await apiFetch<SearchResponse>("/search", {
    method: "POST",
    body: JSON.stringify({ query, limit }),
  });
  return res.results;
}

export async function getAlternatives(toolId: string, limit = 5): Promise<AlternativeTool[]> {
  return apiFetch<AlternativeTool[]>(
    `/tools/${encodeURIComponent(toolId)}/alternatives?limit=${limit}`
  );
}

// System metrics (from /metrics root endpoint, not /api/v1)
export interface SystemMetrics {
  uptime_seconds: number;
  requests: {
    total: number;
    active: number;
    by_method: Record<string, number>;
    by_status: Record<string, number>;
    latency: { count: number; total: number; avg: number; min: number; max: number };
  };
  cache: { hits: number; misses: number; hit_rate: number };
  agents: Record<string, { calls: number; errors: number; latency: { count: number; avg: number } }>;
  crawler: { requests: number; failures: number; pages_crawled: number; latency: { count: number; avg: number } };
  ingestion: { started: number; completed: number; failed: number };
  scheduler: Record<string, { executed: number; failed: number }>;
}

export async function getSystemMetrics(): Promise<SystemMetrics> {
  return rootFetch<SystemMetrics>("/metrics");
}
