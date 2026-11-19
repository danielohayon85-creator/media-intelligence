const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface AnalysisResult {
  relevance: "direct" | "indirect" | "background" | "not_relevant";
  relevance_confidence: number;
  sentiment: "positive" | "negative" | "neutral" | "mixed";
  sentiment_confidence: number;
  coverage_style: string;
  framing: string[];
  ai_provider: string;
  manually_corrected: boolean;
  correction_notes: string | null;
}

export interface MediaItem {
  id: string;
  organization_id: string;
  source_connection_id: string;
  external_id: string | null;
  title: string;
  content: string | null;
  summary: string | null;
  published_at: string;
  outlet_name: string;
  author_name: string | null;
  media_type: string;
  url: string | null;
  keywords: string[];
  entities: string[];
  exposure_count: number | null;
  engagement_count: number | null;
  dedup_role: "original" | "duplicate" | "reprint" | "follow_up";
  dedup_of_item_id: string | null;
  ingested_at: string;
  analysis: AnalysisResult | null;
}

export interface MediaItemListResponse {
  total: number;
  items: MediaItem[];
}

export interface KpiResponse {
  total_mentions: number;
  unique_publications: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  mixed_pct: number;
  change_vs_previous_period_pct: number | null;
  period_start: string;
  period_end: string;
}

export interface TrendPoint {
  bucket: string;
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
  total: number;
}

export interface TrendResponse {
  granularity: string;
  points: TrendPoint[];
}

export interface DataQualityResponse {
  last_synced_at: string | null;
  items_fetched: number;
  items_new: number;
  items_duplicate: number;
  items_rejected: number;
  items_pending_analysis: number;
  items_with_full_content_pct: number;
  items_with_exposure_data_pct: number;
  sync_errors: Record<string, unknown>[];
}

export interface Insight {
  id: string;
  level: "descriptive" | "comparative" | "interpretive" | "operational";
  title: string;
  explanation: string;
  supporting_item_ids: string[];
  confidence: number;
  recommendation: string | null;
  period_start: string;
  period_end: string;
  generated_at: string;
  ai_provider: string;
}

export interface Organization {
  id: string;
  name: string;
  profile_key: string;
  relevance_profile: Record<string, unknown>;
  is_demo: boolean;
  created_at: string;
}

export interface SourceConnection {
  id: string;
  organization_id: string;
  name: string;
  source_type: "csv" | "json" | "api_generic" | "demo";
  config: Record<string, unknown>;
  is_active: boolean;
  last_synced_at: string | null;
  created_at: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export interface DashboardFilters {
  organizationId: string;
  dateFrom?: string;
  dateTo?: string;
  outletName?: string;
  mediaType?: string;
  keyword?: string;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  return search.toString();
}

export const api = {
  listOrganizations: () => apiFetch<Organization[]>("/api/organizations"),

  listSources: (organizationId: string) =>
    apiFetch<SourceConnection[]>(`/api/sources?organization_id=${organizationId}`),

  createSource: (payload: { organization_id: string; name: string; source_type: string; config: Record<string, unknown> }) =>
    apiFetch<SourceConnection>("/api/sources", { method: "POST", body: JSON.stringify(payload) }),

  syncSource: (sourceId: string) => apiFetch(`/api/sources/${sourceId}/sync`, { method: "POST" }),

  ingestFile: async (sourceId: string, kind: "csv" | "json", file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/ingest/${kind}?source_id=${sourceId}`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
    return res.json();
  },

  getKpis: (filters: DashboardFilters) =>
    apiFetch<KpiResponse>(
      `/api/dashboard/kpis?${buildQuery({
        organization_id: filters.organizationId,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        outlet_name: filters.outletName,
        media_type: filters.mediaType,
        keyword: filters.keyword,
      })}`
    ),

  getTrend: (filters: DashboardFilters) =>
    apiFetch<TrendResponse>(
      `/api/dashboard/trend?${buildQuery({
        organization_id: filters.organizationId,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        outlet_name: filters.outletName,
        media_type: filters.mediaType,
        keyword: filters.keyword,
      })}`
    ),

  getDataQuality: (organizationId: string) =>
    apiFetch<DataQualityResponse>(`/api/dashboard/data-quality?organization_id=${organizationId}`),

  getInsights: (filters: DashboardFilters) =>
    apiFetch<Insight[]>(
      `/api/insights?${buildQuery({
        organization_id: filters.organizationId,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
      })}`
    ),

  listItems: (
    filters: DashboardFilters & {
      page?: number;
      pageSize?: number;
      sentiment?: string;
      search?: string;
    }
  ) =>
    apiFetch<MediaItemListResponse>(
      `/api/items?${buildQuery({
        organization_id: filters.organizationId,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        outlet_name: filters.outletName,
        media_type: filters.mediaType,
        keyword: filters.keyword,
        sentiment: filters.sentiment,
        search: filters.search,
        page: filters.page,
        page_size: filters.pageSize,
      })}`
    ),

  getItem: (itemId: string) => apiFetch<MediaItem>(`/api/items/${itemId}`),

  correctAnalysis: (
    itemId: string,
    payload: { relevance?: string; sentiment?: string; coverage_style?: string; correction_notes?: string }
  ) =>
    apiFetch<MediaItem>(`/api/items/${itemId}/analysis`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  refreshInsights: (filters: DashboardFilters) =>
    apiFetch<Insight[]>(
      `/api/insights/refresh?${buildQuery({
        organization_id: filters.organizationId,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
      })}`,
      { method: "POST" }
    ),

  seedDemo: () => apiFetch<{ organization_id: string }>("/api/demo/seed", { method: "POST" }),
};
