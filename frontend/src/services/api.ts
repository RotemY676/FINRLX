/**
 * API client for FINRLX backend.
 * Uses Next.js rewrite proxy (/api/* -> backend:8000/api/*).
 */

export interface ApiResponse<T> {
  meta: {
    trace_id: string | null;
    api_version: string;
    generated_at: string;
    warnings: string[];
    freshness: {
      data_as_of: string | null;
      is_stale: boolean;
      staleness_reason: string | null;
    } | null;
  };
  data: T;
}

export interface ConfidenceTriplet {
  model_confidence: number | null;
  data_confidence: number | null;
  operational_confidence: number | null;
}

export interface WeightEntry {
  asset_id: string;
  ticker: string;
  name: string;
  target_weight: number;
  previous_weight: number | null;
  delta: number | null;
  stance: string | null;
  rationale: string | null;
}

export interface RecommendationSummary {
  id: string;
  status: string;
  confidence: ConfidenceTriplet;
  total_positions: number;
  top_overweight: string | null;
  top_underweight: string | null;
  published_at: string | null;
  valid_from: string | null;
  valid_to: string | null;
  data_as_of: string | null;
  rationale_summary: string | null;
  warning_count: number;
}

export interface HealthSummary {
  source_freshness_ok: boolean;
  feature_health_ok: boolean;
  model_health_ok: boolean;
  publication_health_ok: boolean;
  open_incidents: number;
  last_checked_at: string | null;
}

export interface OverviewData {
  current_recommendation: RecommendationSummary | null;
  health: HealthSummary;
  recent_recommendation_count: number;
  last_published_at: string | null;
}

export interface RecommendationDetail {
  id: string;
  status: string;
  confidence: ConfidenceTriplet;
  weights: WeightEntry[];
  published_at: string | null;
  valid_from: string | null;
  valid_to: string | null;
  data_as_of: string | null;
  rationale_summary: string | null;
  warnings: string[];
  policy_version_id: string | null;
  created_at: string;
}

async function apiFetch<T>(path: string): Promise<ApiResponse<T>> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchOverview(): Promise<ApiResponse<OverviewData>> {
  return apiFetch<OverviewData>("/api/v1/overview");
}

export async function fetchCurrentRecommendation(): Promise<
  ApiResponse<RecommendationDetail | null>
> {
  return apiFetch<RecommendationDetail | null>("/api/v1/recommendations/current");
}
