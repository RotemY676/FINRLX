/**
 * API client for FINRLX backend.
 *
 * Production:
 *   Uses NEXT_PUBLIC_API_BASE_URL, for example:
 *   https://backend-production-aab8.up.railway.app
 *
 * Important:
 *   Do not call relative /api/v1/* paths directly in production.
 *   Relative paths hit the frontend service itself and may trigger a localhost proxy.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

function buildApiUrl(path: string): string {
  if (!path) {
    throw new Error("API path is missing");
  }

  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedBase = API_BASE_URL.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  return `${normalizedBase}${normalizedPath}`;
}

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
  // Provenance fields
  source_type?: string | null;
  is_demo?: boolean;
  lineage_available?: boolean;
  decision_count?: number | null;
  market_bar_window?: { start: string; end: string } | null;
  recommendation_ids?: string[];
  source_feature_set_ids?: string[];
  source_signal_run_ids?: string[];
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
  // Provenance
  source_type?: string | null;
  is_demo?: boolean;
  lineage_available?: boolean;
  decision_count?: number | null;
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
  // Provenance fields
  source_type?: string | null;
  source_recommendation_id?: string | null;
  portfolio_value?: number | null;
  is_demo?: boolean;
}

// Fetch functions

async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<ApiResponse<T>> {
  const url = buildApiUrl(path);

  const res = await fetch(url, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!res.ok) {
    const responseBody = await res.text().catch(() => "");
    throw new Error(
      `API error: ${res.status} ${res.statusText} for ${url}${
        responseBody ? ` — ${responseBody}` : ""
      }`
    );
  }

  return res.json() as Promise<ApiResponse<T>>;
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

// Paper portfolio performance

export interface PaperPerformanceSummary {
  status: string;
  total_return: number | null;
  annualized_return: number | null;
  max_drawdown: number | null;
  volatility: number | null;
  sharpe_ratio: number | null;
  starting_value: number | null;
  ending_value: number | null;
  trade_count: number | null;
  snapshot_count: number | null;
  days: number | null;
  warnings: string[];
}

export async function fetchPaperPerformance(portfolioId: string): Promise<ApiResponse<PaperPerformanceSummary>> {
  return apiFetch<PaperPerformanceSummary>(`/api/v1/paper/${portfolioId}/performance`);
}

// Engine comparison types

export interface EngineSignal {
  engine_key: string;
  engine_name: string;
  stance: string;
  confidence: number;
  weight: number;
  risk_read: string;
  horizon: string;
  drivers: string[];
  ignores: string[];
  note: string | null;
  data_freshness_min: number | null;
}

export interface EngineComparisonData {
  recommendation_id: string;
  engines: EngineSignal[];
  synthesis_stance: string;
  synthesis_confidence: number;
  dispersion: number;
}

export interface DisagreementData {
  recommendation_id: string;
  total_engines: number;
  agreeing: number;
  dissenting: number;
  dispersion: number;
  dominant_stance: string;
  dissenting_engines: string[];
  summary: string;
}

// Evidence types

export interface EvidenceItem {
  order: number;
  title: string;
  body: string;
  delta_label: string | null;
  delta_direction: string | null;
  caveat: string | null;
  source_engine: string | null;
}

export interface EvidenceNarrativeData {
  recommendation_id: string;
  items: EvidenceItem[];
  caveat: string | null;
  last_refreshed_min: number | null;
}

// Regime types

export interface SignalPosture {
  factor: string;
  direction: string;
  sigma: number;
}

export interface SectorTilt {
  sector: string;
  tilt_pct: number;
}

export interface RegimeData {
  regime_label: string;
  regime_confidence: number;
  persistence_days: number;
  last_switch_date: string;
  alternatives: Array<{ label: string; prob: number }>;
  signal_posture: SignalPosture[];
  sector_tilts: SectorTilt[];
  as_of: string;
}

export interface ActivityEventData {
  kind: string;
  actor: string;
  description: string;
  detail: string | null;
  when_ago: string;
  timestamp: string;
}

export interface ActivityFeedData {
  events: ActivityEventData[];
  total: number;
}

// New fetch functions

export async function fetchEngineComparison(): Promise<
  ApiResponse<EngineComparisonData | null>
> {
  return apiFetch<EngineComparisonData | null>("/api/v1/engines/comparison");
}

export async function fetchDisagreement(): Promise<
  ApiResponse<DisagreementData | null>
> {
  return apiFetch<DisagreementData | null>("/api/v1/engines/disagreement");
}

export async function fetchEvidence(): Promise<
  ApiResponse<EvidenceNarrativeData | null>
> {
  return apiFetch<EvidenceNarrativeData | null>("/api/v1/engines/evidence");
}

export async function fetchRegime(): Promise<ApiResponse<RegimeData>> {
  return apiFetch<RegimeData>("/api/v1/regime");
}

export async function fetchActivity(): Promise<ApiResponse<ActivityFeedData>> {
  return apiFetch<ActivityFeedData>("/api/v1/activity");
}

// Ops Command Center types

export interface OpsQueueItem {
  id?: string;
  recommendation_id: string;
  ticker: string;
  stance: string;
  version: string;
  submitted_ago: string;
  submitter: string;
  weight: string;
  confidence: number;
  flags: string[];
  priority: string;
  status: string;
}

export interface OpsFeed {
  name: string;
  status: string;
  lag: string;
  coverage: string;
  slo: number;
}

export interface OpsEngine {
  name: string;
  latency: string;
  drift: number;
  last_run: string;
  status: string;
}

export interface OpsBreach {
  kind: string;
  label: string;
  utilization: number;
  trend: string;
  severity: string;
  related: string;
}

export interface OpsIncident {
  id: string;
  title: string;
  started: string;
  severity: string;
  owner: string;
  status: string;
  affected_recs: number;
  note: string;
}

export interface OpsAuditEntry {
  when: string;
  actor: string;
  action: string;
  target: string;
  scope: string;
  ok: boolean;
}

export interface OpsSystemKpi {
  key: string;
  value: string;
  sub: string | null;
  tone: string;
}

export interface OpsMLBlock {
  total_models: number;
  active_models: number;
  shadow_models: number;
  latest_validation_status: string | null;
  promotion_readiness: string | null;
  warning_count: number;
  any_model_influences_live_pipeline: boolean;
  ml_is_shadow_only: boolean;
}

export interface OpsPolicyBlock {
  total_rules: number;
  active_rules: number;
  enforced_rules: number;
  active_breaches: number;
}

export interface OpsIntegrationsBlock {
  total_integrations: number;
  healthy: number;
  degraded: number;
  placeholder: number;
  real_providers: number;
}

export interface OpsUniverseBlock {
  total_universes: number;
  total_assets: number;
  default_universe_name: string | null;
  default_readiness: string | null;
}

export interface OpsRLBlock {
  total_environments: number;
  total_runs: number;
  latest_run_status: string | null;
  latest_agent_type: string | null;
  total_agents: number;
  trainable_agents: number;
  latest_training_status: string | null;
  latest_training_agent: string | null;
  total_policy_snapshots: number;
  total_benchmarks: number;
  latest_benchmark_status: string | null;
  is_shadow_only: boolean;
  live_pipeline_influence: boolean;
}

export interface OpsData {
  queue: OpsQueueItem[];
  feeds: OpsFeed[];
  engines: OpsEngine[];
  breaches: OpsBreach[];
  incidents: OpsIncident[];
  audit: OpsAuditEntry[];
  system_kpis: OpsSystemKpi[];
  ml_ops: OpsMLBlock | null;
  policy: OpsPolicyBlock | null;
  integrations_summary: OpsIntegrationsBlock | null;
  universe: OpsUniverseBlock | null;
  rl: OpsRLBlock | null;
}

export interface QueueActionResult {
  id: string;
  new_status: string;
  message: string;
}

export interface WorkspaceCountsData {
  overview: number;
  decisions: number;
  risk: number;
  ops: number;
}

export async function fetchOps(): Promise<ApiResponse<OpsData>> {
  return apiFetch<OpsData>("/api/v1/ops");
}

export async function fetchOpsQueue(filter: string = "all"): Promise<ApiResponse<OpsQueueItem[]>> {
  return apiFetch<OpsQueueItem[]>(`/api/v1/ops/queue?filter=${filter}`);
}

export async function fetchOpsAudit(scope: string = "all"): Promise<ApiResponse<OpsAuditEntry[]>> {
  return apiFetch<OpsAuditEntry[]>(`/api/v1/ops/audit?scope=${scope}`);
}

export async function approveQueueItem(id: string): Promise<ApiResponse<QueueActionResult>> {
  return apiFetch<QueueActionResult>(`/api/v1/ops/queue/${id}/approve`, { method: "POST" });
}

export async function deferQueueItem(id: string): Promise<ApiResponse<QueueActionResult>> {
  return apiFetch<QueueActionResult>(`/api/v1/ops/queue/${id}/defer`, { method: "POST" });
}

export async function challengeQueueItem(id: string): Promise<ApiResponse<QueueActionResult>> {
  return apiFetch<QueueActionResult>(`/api/v1/ops/queue/${id}/challenge`, { method: "POST" });
}

export async function fetchWorkspaceCounts(): Promise<ApiResponse<WorkspaceCountsData>> {
  return apiFetch<WorkspaceCountsData>("/api/v1/workspace-counts");
}

// Scenario simulation types

export interface ScenarioParamsData {
  horizon_days: number;
  rate_shock_bps: number;
  correlation: number;
  earnings_revision_weight: number;
  momentum_engine_on: boolean;
  flow_engine_on: boolean;
  policy_constraints_on: boolean;
}

export interface ScenarioDeltaData {
  metric: string;
  baseline: string;
  modified: string;
  direction: string;
}

export interface ScenarioResultData {
  is_modified: boolean;
  deltas: ScenarioDeltaData[];
  weight_impact: number;
  confidence_impact: number;
  expected_return_impact: number;
  warnings: string[];
}

export async function simulateScenario(params: ScenarioParamsData): Promise<ApiResponse<ScenarioResultData>> {
  return apiFetch<ScenarioResultData>("/api/v1/scenario/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

export async function fetchScenarioBaseline(): Promise<ApiResponse<ScenarioParamsData>> {
  return apiFetch<ScenarioParamsData>("/api/v1/scenario/baseline");
}

// Action bar types

export interface ActionResultData {
  action: string;
  success: boolean;
  new_status: string;
  message: string;
}

export async function actionSaveThesis(): Promise<ApiResponse<ActionResultData>> {
  return apiFetch<ActionResultData>("/api/v1/actions/save-thesis", { method: "POST" });
}

export async function actionPromotePaper(): Promise<ApiResponse<ActionResultData>> {
  return apiFetch<ActionResultData>("/api/v1/actions/promote-paper", { method: "POST" });
}

export async function actionDefer(reason?: string): Promise<ApiResponse<ActionResultData>> {
  return apiFetch<ActionResultData>("/api/v1/actions/defer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason || null }),
  });
}

// Price chart types

export interface PricePointData {
  date: string;
  price: number;
  benchmark: number | null;
  band_upper: number | null;
  band_lower: number | null;
}

export interface ChartEventData {
  date: string;
  label: string;
  kind: string;
}

export interface PriceChartDataType {
  ticker: string;
  current_price: number;
  price_return_pct: number;
  benchmark_return_pct: number | null;
  benchmark_name: string;
  points: PricePointData[];
  events: ChartEventData[];
}

export async function fetchPriceChart(ticker: string = "NVDA"): Promise<ApiResponse<PriceChartDataType>> {
  return apiFetch<PriceChartDataType>(`/api/v1/pricechart?ticker=${ticker}`);
}

// Incident resolve

export async function resolveIncident(id: string): Promise<ApiResponse<{ success: boolean; message: string }>> {
  return apiFetch<{ success: boolean; message: string }>(`/api/v1/ops/incidents/${id}/resolve`, { method: "POST" });
}

// ML Ops Observability types

export interface MLOpsWarning {
  level: string;
  message: string;
}

export interface MLOpsSummary {
  model_key: string;
  model_name: string | null;
  status: string;
  is_shadow: boolean;
  latest_prediction_run_id: string | null;
  latest_prediction_status: string | null;
  prediction_count: number;
  latest_validation_report_id: string | null;
  validation_status: string | null;
  validation_sample_count: number | null;
  directional_accuracy: number | null;
  calibration_error: number | null;
  promotion_readiness: string | null;
  latest_promotion_review_id: string | null;
  promotion_review_recommendation: string | null;
  promotion_review_decision: string | null;
  baseline_total_return: number | null;
  shadow_total_return: number | null;
  total_return_delta: number | null;
  max_drawdown_delta: number | null;
  sharpe_delta: number | null;
  still_shadow: boolean;
  live_pipeline_influence: boolean;
  warnings: MLOpsWarning[];
  recommended_operator_action: string | null;
}

export async function fetchMLOpsSummary(): Promise<ApiResponse<MLOpsSummary>> {
  return apiFetch<MLOpsSummary>("/api/v1/ml-ops/summary");
}