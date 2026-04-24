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

// Decision pipeline stage types

export interface AssetSelection {
  asset_id: string;
  ticker: string;
  reason: string | null;
}

export interface SelectionRunView {
  id: string;
  recommendation_id: string;
  included: AssetSelection[];
  excluded: AssetSelection[];
  rationale: string | null;
  created_at: string;
}

export interface AllocationEntry {
  asset_id: string;
  ticker: string;
  weight: number;
  rationale: string | null;
}

export interface AllocationView {
  id: string;
  recommendation_id: string;
  method: string | null;
  entries: AllocationEntry[];
  rationale: string | null;
  created_at: string;
}

export interface TimingView {
  id: string;
  recommendation_id: string;
  urgency: string | null;
  horizon_days: number | null;
  rationale: string | null;
  created_at: string;
}

export interface RiskAdjustment {
  asset_id: string;
  ticker: string;
  pre_weight: number;
  post_weight: number;
  delta: number;
  reason: string | null;
}

export interface RiskOverlayView {
  id: string;
  recommendation_id: string;
  portfolio_risk_score: number | null;
  adjustments: RiskAdjustment[];
  constraints_applied: string[];
  rationale: string | null;
  created_at: string;
}

export interface DecisionStagesData {
  recommendation_id: string;
  selection: SelectionRunView | null;
  allocation: AllocationView | null;
  timing: TimingView | null;
  risk_overlay: RiskOverlayView | null;
}

// Comparison types

export interface ComparisonWeightRow {
  asset_id: string;
  ticker: string;
  name: string;
  recommendation_weight: number;
  benchmark_weight: number;
  delta: number;
  recommendation_stance: string | null;
}

export interface ComparisonData {
  recommendation_id: string;
  benchmark_name: string;
  recommendation_confidence: ConfidenceTriplet;
  weights: ComparisonWeightRow[];
  recommendation_warning_count: number;
  recommendation_rationale: string | null;
  total_active_weight: number;
  concentration_top3_rec: number;
  concentration_top3_bench: number;
}

// Replay types

export interface ReplayStageSnapshot {
  stage: string;
  snapshot_data: Record<string, unknown>;
  captured_at: string;
}

export interface ReplayDetail {
  id: string;
  recommendation_id: string;
  captured_at: string;
  status: string;
  confidence: ConfidenceTriplet;
  weights: WeightEntry[];
  rationale_summary: string | null;
  warnings: string[];
  data_as_of: string | null;
  stages: ReplayStageSnapshot[];
}

export interface ReplayListItem {
  id: string;
  recommendation_id: string;
  captured_at: string;
  status: string;
  total_positions: number;
  model_confidence: number | null;
}

export interface ReplayListData {
  items: ReplayListItem[];
  total: number;
}

// Backtest types

export interface BacktestResultSummary {
  total_return: number | null;
  annualized_return: number | null;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  volatility: number | null;
  total_trades: number | null;
  avg_turnover: number | null;
}

export interface EquityCurvePoint {
  date: string;
  value: number;
}

export interface BacktestDetail {
  id: string;
  name: string;
  status: string;
  universe_name: string | null;
  policy_version_id: string | null;
  start_date: string | null;
  end_date: string | null;
  is_promoted: boolean;
  config: Record<string, unknown>;
  results: BacktestResultSummary;
  equity_curve: EquityCurvePoint[];
  warnings: string[];
  created_at: string;
}

export interface BacktestListItem {
  id: string;
  name: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  is_promoted: boolean;
  total_return: number | null;
  sharpe_ratio: number | null;
}

export interface BacktestListData {
  items: BacktestListItem[];
  total: number;
}

// Paper portfolio types

export interface PaperHolding {
  asset_id: string;
  ticker: string;
  name: string;
  target_weight: number;
  current_weight: number;
  drift: number;
}

export interface PaperEvent {
  timestamp: string;
  event_type: string;
  description: string;
}

export interface PaperPortfolioData {
  id: string;
  name: string;
  is_active: boolean;
  cash_weight: number;
  invested_weight: number;
  total_rebalances: number;
  last_rebalance_at: string | null;
  holdings: PaperHolding[];
  events: PaperEvent[];
  warnings: string[];
  created_at: string;
}

// Fetch functions

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
  return apiFetch<RecommendationDetail | null>(
    "/api/v1/recommendations/current"
  );
}

export async function fetchDecisionStages(
  recommendationId: string
): Promise<ApiResponse<DecisionStagesData>> {
  return apiFetch<DecisionStagesData>(
    `/api/v1/recommendations/${recommendationId}/stages`
  );
}

export async function fetchCurrentComparison(): Promise<
  ApiResponse<ComparisonData | null>
> {
  return apiFetch<ComparisonData | null>("/api/v1/comparison/current");
}

export async function fetchReplayList(): Promise<ApiResponse<ReplayListData>> {
  return apiFetch<ReplayListData>("/api/v1/replay");
}

export async function fetchReplay(
  recommendationId: string
): Promise<ApiResponse<ReplayDetail | null>> {
  return apiFetch<ReplayDetail | null>(`/api/v1/replay/${recommendationId}`);
}

export async function fetchBacktestList(): Promise<ApiResponse<BacktestListData>> {
  return apiFetch<BacktestListData>("/api/v1/backtests");
}

export async function fetchBacktest(
  id: string
): Promise<ApiResponse<BacktestDetail>> {
  return apiFetch<BacktestDetail>(`/api/v1/backtests/${id}`);
}

export async function fetchCurrentPaper(): Promise<
  ApiResponse<PaperPortfolioData | null>
> {
  return apiFetch<PaperPortfolioData | null>("/api/v1/paper/current");
}
