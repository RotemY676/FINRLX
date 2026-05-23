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

export interface BenchmarkMetricBlock {
  total_return: number | null;
  annualized_return: number | null;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  calmar_ratio: number | null;
  volatility: number | null;
}

export interface BacktestResultSummary {
  total_return: number | null;
  annualized_return: number | null;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  calmar_ratio: number | null;
  volatility: number | null;
  total_trades: number | null;
  avg_turnover: number | null;
  // Phase 19D: keyed by ticker (SPY, QQQ, …). Value is null when the
  // benchmark had no bars in the requested window.
  benchmark_metrics?: Record<string, BenchmarkMetricBlock | null> | null;
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

export async function apiFetch<T>(
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

// RL Benchmark types

export interface RLBenchmarkSafetyFlags {
  offline_only: boolean;
  shadow_only: boolean;
  live_pipeline_influence: boolean;
  no_broker_execution: boolean;
  no_publication_influence: boolean;
  no_recommendation_pollution: boolean;
}

export interface RLSkippedAgent {
  agent_key: string;
  reason: string;
}

export interface RLAgentMetrics {
  total_return: number | null;
  total_reward: number | null;
  max_drawdown: number | null;
  total_turnover: number | null;
  step_count: number | null;
  violation_count: number | null;
  status: string | null;
}

export interface RLRewardBreakdown {
  portfolio_return_component: number | null;
  drawdown_penalty_component: number | null;
  turnover_penalty_component: number | null;
}

export interface RLForensicStep {
  step_index: number;
  as_of_date: string | null;
  agent_key: string;
  action_type: string | null;
  reward: number | null;
  portfolio_value: number | null;
  turnover: number | null;
  violations: string[] | null;
}

export interface RLBenchmarkReport {
  id: string;
  name: string;
  environment_key: string;
  universe_id: string | null;
  status: string;
  start_date: string | null;
  end_date: string | null;
  compared_agents: string[];
  requested_agents: string[];
  executed_agents: string[];
  skipped_agents: RLSkippedAgent[];
  is_complete_comparison: boolean;
  metrics_by_agent: Record<string, RLAgentMetrics>;
  reward_breakdown_by_agent: Record<string, RLRewardBreakdown>;
  violations_by_agent: Record<string, string[]>;
  forensic_summary: RLForensicStep[];
  forensic_summary_by_agent?: Record<string, RLForensicStep[]> | null;
  result_fingerprint?: string | null;
  invariant_check_results?: Record<string, boolean> | null;
  safety_flags: RLBenchmarkSafetyFlags;
  warnings: string[] | null;
  created_at: string | null;
  completed_at: string | null;
}

export async function fetchRLBenchmarks(): Promise<ApiResponse<RLBenchmarkReport[]>> {
  return apiFetch<RLBenchmarkReport[]>("/api/v1/rl/benchmarks");
}

export async function fetchRLBenchmark(id: string): Promise<ApiResponse<RLBenchmarkReport>> {
  return apiFetch<RLBenchmarkReport>(`/api/v1/rl/benchmarks/${id}`);
}

export interface RunRLBenchmarkRequest {
  name: string;
  environment_key?: string;
  start_date: string;
  end_date: string;
  agent_keys?: string[];
}

export interface RLBenchmarkAuditEvent {
  id: string;
  created_at: string | null;
  event_type: string;
  actor_type: string;
  source: string;
  benchmark_report_id: string | null;
  status: string | null;
  requested_agents: string[] | null;
  executed_agents: string[] | null;
  skipped_agents: unknown[] | null;
  is_complete_comparison: boolean | null;
  safety_flags: RLBenchmarkSafetyFlags | null;
  result_fingerprint: string | null;
  invariant_check_results: Record<string, boolean> | null;
  warnings: string[] | null;
}

export async function fetchRLBenchmarkAudit(): Promise<ApiResponse<RLBenchmarkAuditEvent[]>> {
  return apiFetch<RLBenchmarkAuditEvent[]>("/api/v1/rl/benchmarks/audit");
}

export async function fetchRLBenchmarkAuditForReport(reportId: string): Promise<ApiResponse<RLBenchmarkAuditEvent[]>> {
  return apiFetch<RLBenchmarkAuditEvent[]>(`/api/v1/rl/benchmarks/${reportId}/audit`);
}

// FinRL-X Research types

export interface FinRLXAdapterStatus {
  adapter_type: string;
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  live_pipeline_influence: boolean;
  no_broker_execution: boolean;
  finrlx_available: boolean;
  gpu_required: boolean;
  training_mode: string;
  missing_for_real_training: string[];
  notes: string;
}

export interface FinRLXCandidateIsolation {
  candidate_id: string;
  isolated: boolean;
  checks: Record<string, boolean>;
  all_blocked: boolean;
  safety_flags: Record<string, boolean>;
  reasons: string[];
}

export interface FinRLXDependencyStatus {
  numpy_available: boolean;
  gymnasium_available: boolean;
  stable_baselines3_available: boolean;
  torch_available: boolean;
  torch_cuda_available: boolean | null;
  cpu_only_mode: boolean;
  neural_training_available: boolean;
  missing_dependencies: string[];
}

export async function fetchFinRLXStatus(): Promise<ApiResponse<FinRLXAdapterStatus>> {
  return apiFetch<FinRLXAdapterStatus>("/api/v1/rl/finrlx/status");
}

export async function fetchFinRLXDependencies(): Promise<ApiResponse<FinRLXDependencyStatus>> {
  return apiFetch<FinRLXDependencyStatus>("/api/v1/rl/finrlx/dependencies");
}

export interface FinRLXCandidate {
  id: string;
  training_run_id: string | null;
  agent_key: string;
  policy_type: string;
  training_mode: string;
  real_neural_training: boolean;
  imported_from_artifact: boolean;
  artifact_hash: string | null;
  artifact_summary: Record<string, unknown> | null;
  source: string | null;
  notes: string | null;
  not_eligible_for_promotion: boolean;
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  safety_flags: Record<string, boolean>;
  metrics: Record<string, unknown> | null;
  created_at: string | null;
}

export interface FinRLXBenchmarkEligibility {
  eligible: boolean;
  reasons: string[];
  candidate_summary: Record<string, unknown> | null;
  safety_flags: Record<string, boolean>;
  isolation_checks: Record<string, boolean> | null;
}

export interface FinRLXCandidateBenchmarkContext {
  candidate_id: string;
  policy_type: string;
  training_mode: string;
  imported_from_artifact: boolean;
  artifact_hash: string;
  inference_mode: string;
  real_neural_inference: boolean;
  artifact_metadata_used_for_inference: boolean;
  surrogate_description: string;
  not_eligible_for_promotion: boolean;
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  surrogate_agent_key: string;
}

export interface FinRLXCandidateBenchmarkResponse {
  status: string;
  benchmark_report_id: string;
  is_complete_comparison: boolean;
  requested_agents: string[];
  executed_agents: string[];
  skipped_agents: string[];
  metrics_by_agent: Record<string, Record<string, number>>;
  reward_breakdown_by_agent: Record<string, Record<string, number>>;
  forensic_summary_by_agent: Record<string, unknown[]> | null;
  safety_flags: Record<string, boolean>;
  result_fingerprint: string | null;
  invariant_check_results: Record<string, boolean> | null;
  candidate_benchmark_context: FinRLXCandidateBenchmarkContext;
  isolation_checks: Record<string, boolean>;
  isolated: boolean;
  all_blocked: boolean;
  production_fingerprints: Record<string, unknown>;
  warnings: string[];
  created_at: string;
}

export interface FinRLXCandidateBenchmarkHistoryItem {
  benchmark_report_id: string;
  candidate_id: string;
  artifact_hash: string;
  inference_mode: string;
  real_neural_inference: boolean;
  executed_agents: string[];
  result_fingerprint: string | null;
  safety_flags: Record<string, boolean> | null;
  occurred_at: string | null;
}

export interface FinRLXArtifactValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  artifact_hash: string;
  normalized_artifact_summary: Record<string, unknown>;
  safety_flags: Record<string, boolean>;
}

export interface FinRLXArtifactImportResponse {
  status: string;
  policy_candidate_id: string | null;
  policy_type: string;
  training_mode: string;
  real_neural_training: boolean;
  imported_from_artifact: boolean;
  artifact_hash: string;
  validation_result: FinRLXArtifactValidationResult;
  safety_flags: Record<string, boolean>;
  not_eligible_for_promotion: boolean;
  isolation_checks: Record<string, boolean>;
  production_fingerprints: Record<string, unknown>;
  warnings: string[];
  created_at: string;
}

export async function validateFinRLXResearchArtifact(artifact: Record<string, unknown>): Promise<ApiResponse<FinRLXArtifactValidationResult>> {
  return apiFetch<FinRLXArtifactValidationResult>("/api/v1/rl/finrlx/validate-research-artifact", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ artifact }),
  });
}

export async function importFinRLXResearchArtifact(payload: {
  artifact: Record<string, unknown>;
  import_acknowledgement: boolean;
  source: string;
  notes?: string;
}): Promise<ApiResponse<FinRLXArtifactImportResponse>> {
  return apiFetch<FinRLXArtifactImportResponse>("/api/v1/rl/finrlx/import-research-artifact", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchFinRLXCandidates(): Promise<ApiResponse<FinRLXCandidate[]>> {
  return apiFetch<FinRLXCandidate[]>("/api/v1/rl/finrlx/candidates");
}

export async function fetchFinRLXCandidate(id: string): Promise<ApiResponse<FinRLXCandidate>> {
  return apiFetch<FinRLXCandidate>(`/api/v1/rl/finrlx/candidates/${id}`);
}

export async function fetchFinRLXCandidateIsolation(id: string): Promise<ApiResponse<FinRLXCandidateIsolation>> {
  return apiFetch<FinRLXCandidateIsolation>(`/api/v1/rl/finrlx/candidates/${id}/isolation`);
}

export async function fetchFinRLXBenchmarkEligibility(candidateId: string): Promise<ApiResponse<FinRLXBenchmarkEligibility>> {
  return apiFetch<FinRLXBenchmarkEligibility>(`/api/v1/rl/finrlx/candidates/${candidateId}/benchmark-eligibility`);
}

export async function runFinRLXCandidateBenchmark(candidateId: string, payload: {
  name: string;
  start_date: string;
  end_date: string;
  include_baselines: boolean;
  research_acknowledgement: boolean;
}): Promise<ApiResponse<FinRLXCandidateBenchmarkResponse>> {
  return apiFetch<FinRLXCandidateBenchmarkResponse>(`/api/v1/rl/finrlx/candidates/${candidateId}/benchmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchFinRLXCandidateBenchmarks(candidateId: string): Promise<ApiResponse<FinRLXCandidateBenchmarkHistoryItem[]>> {
  return apiFetch<FinRLXCandidateBenchmarkHistoryItem[]>(`/api/v1/rl/finrlx/candidates/${candidateId}/benchmarks`);
}

export async function runRLBenchmark(payload: RunRLBenchmarkRequest): Promise<ApiResponse<RLBenchmarkReport>> {
  return apiFetch<RLBenchmarkReport>("/api/v1/rl/benchmarks/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ── Dataset Export for Local Research (Phase 8I) ──────────────────

export interface DatasetExportRequest {
  name: string;
  candidate_id?: string | null;
  benchmark_report_id?: string | null;
  start_date: string;
  end_date: string;
  include_features: boolean;
  include_targets: boolean;
  include_warnings: boolean;
  format: "jsonl" | "json";
  research_acknowledgement: boolean;
}

export interface DatasetExportAsset {
  type: string;
  path: string;
}

export interface DatasetExportResponse {
  export_id: string;
  created_at: string;
  updated_at?: string | null;
  status: string;
  lifecycle_state?: string;
  name: string;
  scope: string;
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  no_production_influence: boolean;
  not_eligible_for_promotion: boolean;
  source_candidate_id: string | null;
  source_benchmark_report_id: string | null;
  row_count: number;
  date_range: { start: string; end: string } | null;
  assets: DatasetExportAsset[];
  feature_schema: string[];
  target_schema: string[];
  warning_schema: string[];
  export_format: string;
  export_path: string;
  metadata_path?: string;
  data_path?: string;
  checksum: string;
  fingerprint: string;
  limitations: string[];
  warnings: string[];
  safety_flags: Record<string, boolean>;
  artifact_exists?: boolean;
  metadata_exists?: boolean;
  data_exists?: boolean;
}

export interface DatasetExportRegistryEntry {
  export_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  status: string;
  lifecycle_state: string;
  row_count: number;
  export_format: string;
  export_path: string;
  checksum: string;
  fingerprint: string;
  source_candidate_id: string | null;
  source_benchmark_report_id: string | null;
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  no_production_influence: boolean;
  not_eligible_for_promotion: boolean;
  artifact_exists: boolean;
  metadata_exists: boolean;
  data_exists: boolean;
}

export interface DatasetExportVerifyResult {
  export_id: string;
  export_format: string;
  metadata_path: string;
  data_path: string;
  metadata_exists: boolean;
  data_exists: boolean;
  artifact_exists: boolean;
  lifecycle_state: string;
  warnings: string[];
  safety_flags: Record<string, boolean>;
}

export async function createFinrlxDatasetExport(
  payload: DatasetExportRequest
): Promise<ApiResponse<DatasetExportResponse>> {
  return apiFetch<DatasetExportResponse>("/api/v1/rl/finrlx/dataset-export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listFinrlxDatasetExports(params?: {
  lifecycle_state?: string;
  limit?: number;
}): Promise<ApiResponse<DatasetExportRegistryEntry[]>> {
  const qs = new URLSearchParams();
  if (params?.lifecycle_state) qs.set("lifecycle_state", params.lifecycle_state);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<DatasetExportRegistryEntry[]>(`/api/v1/rl/finrlx/dataset-exports${query ? `?${query}` : ""}`);
}

export async function getFinrlxDatasetExport(
  exportId: string
): Promise<ApiResponse<DatasetExportResponse>> {
  return apiFetch<DatasetExportResponse>(`/api/v1/rl/finrlx/dataset-exports/${exportId}`);
}

export async function markFinrlxDatasetExportStale(
  exportId: string,
  payload: { acknowledgement: boolean; reason?: string }
): Promise<ApiResponse<DatasetExportRegistryEntry>> {
  return apiFetch<DatasetExportRegistryEntry>(`/api/v1/rl/finrlx/dataset-exports/${exportId}/mark-stale`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function verifyFinrlxDatasetExport(
  exportId: string
): Promise<ApiResponse<DatasetExportVerifyResult>> {
  return apiFetch<DatasetExportVerifyResult>(`/api/v1/rl/finrlx/dataset-exports/${exportId}/verify`);
}

export async function rebuildFinrlxDatasetExportRegistry(
  payload: { acknowledgement: boolean }
): Promise<ApiResponse<{ rebuilt: boolean; export_count: number }>> {
  return apiFetch<{ rebuilt: boolean; export_count: number }>("/api/v1/rl/finrlx/dataset-exports/rebuild-registry", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ── Local Research Experiment Tracking (Phase 8J.1) ────────────────

export type ExperimentLifecycleState = "planned" | "running_offline" | "completed" | "failed" | "archived";

export interface ResearchExperiment {
  experiment_id: string;
  created_at: string;
  updated_at: string;
  lifecycle_state: ExperimentLifecycleState;
  name: string;
  linked_export_id: string;
  linked_export_fingerprint: string | null;
  linked_export_checksum: string | null;
  linked_export_row_count: number;
  linked_export_date_range: { start_date?: string; end_date?: string; start?: string; end?: string } | null;
  hypothesis: string;
  method_notes: string;
  parameters: Record<string, unknown>;
  expected_metrics: string[];
  result_summary: string | null;
  result_metrics: Record<string, number | string>;
  result_artifact_path: string | null;
  warnings: string[];
  limitations: string[];
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  no_production_influence: boolean;
  not_eligible_for_promotion: boolean;
  safety_flags?: Record<string, boolean>;
  status?: string;
}

export interface CreateExperimentPayload {
  name: string;
  linked_export_id: string;
  hypothesis?: string;
  method_notes?: string;
  parameters?: Record<string, unknown>;
  expected_metrics?: string[];
  research_acknowledgement: boolean;
}

export interface ExperimentStateUpdatePayload {
  lifecycle_state: ExperimentLifecycleState;
  acknowledgement: boolean;
  reason?: string;
}

export interface ExperimentResultImportPayload {
  acknowledgement: boolean;
  result_summary: string;
  result_metrics: Record<string, number | string>;
  warnings?: string[];
  limitations?: string[];
}

export interface ExperimentVerifyResult {
  experiment_id: string;
  linked_export_id: string;
  linked_export_checksum: string | null;
  linked_export_fingerprint: string | null;
  lifecycle_state: string;
  warnings: string[];
  healthy: boolean;
  safety_flags: Record<string, boolean>;
}

export async function createFinrlxResearchExperiment(
  payload: CreateExperimentPayload
): Promise<ApiResponse<ResearchExperiment>> {
  return apiFetch<ResearchExperiment>("/api/v1/rl/finrlx/research-experiments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listFinrlxResearchExperiments(params?: {
  lifecycle_state?: string;
  limit?: number;
}): Promise<ApiResponse<ResearchExperiment[]>> {
  const qs = new URLSearchParams();
  if (params?.lifecycle_state) qs.set("lifecycle_state", params.lifecycle_state);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<ResearchExperiment[]>(`/api/v1/rl/finrlx/research-experiments${query ? `?${query}` : ""}`);
}

export async function getFinrlxResearchExperiment(
  experimentId: string
): Promise<ApiResponse<ResearchExperiment>> {
  return apiFetch<ResearchExperiment>(`/api/v1/rl/finrlx/research-experiments/${experimentId}`);
}

export async function updateFinrlxResearchExperimentState(
  experimentId: string,
  payload: ExperimentStateUpdatePayload
): Promise<ApiResponse<ResearchExperiment>> {
  return apiFetch<ResearchExperiment>(`/api/v1/rl/finrlx/research-experiments/${experimentId}/state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function importFinrlxResearchExperimentResults(
  experimentId: string,
  payload: ExperimentResultImportPayload
): Promise<ApiResponse<ResearchExperiment>> {
  return apiFetch<ResearchExperiment>(`/api/v1/rl/finrlx/research-experiments/${experimentId}/results`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function verifyFinrlxResearchExperiment(
  experimentId: string
): Promise<ApiResponse<ExperimentVerifyResult>> {
  return apiFetch<ExperimentVerifyResult>(`/api/v1/rl/finrlx/research-experiments/${experimentId}/verify`);
}

export async function rebuildFinrlxResearchExperimentRegistry(
  payload: { acknowledgement: boolean }
): Promise<ApiResponse<{ rebuilt: boolean; experiment_count: number }>> {
  return apiFetch<{ rebuilt: boolean; experiment_count: number }>("/api/v1/rl/finrlx/research-experiments/rebuild-registry", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ── Offline Experiment Comparison Workbench (Phase 8K.1) ───────────

export type ComparisonLifecycleState = "active" | "archived";

export interface MetricCoverage {
  available_count: number;
  missing_count: number;
  coverage_ratio: number;
}

export interface RankedMetricEntry {
  experiment_id: string;
  value: number;
}

export interface ComparisonSummary {
  experiment_count: number;
  metric_names: string[];
  metric_coverage: Record<string, MetricCoverage>;
  missing_metrics: Record<string, string[]>;
  ranked_metrics: Record<string, RankedMetricEntry[]>;
  warnings: string[];
}

export interface ExperimentSnapshot {
  experiment_id: string;
  name: string;
  lifecycle_state: string;
  linked_export_id: string;
  linked_export_checksum: string | null;
  linked_export_fingerprint: string | null;
  linked_export_row_count: number;
  result_summary: string | null;
  result_metrics: Record<string, number | string>;
  warnings: string[];
  limitations: string[];
}

export interface ExperimentComparison {
  comparison_id: string;
  created_at: string;
  updated_at: string;
  lifecycle_state: ComparisonLifecycleState;
  name: string;
  experiment_ids: string[];
  metric_priority: string[];
  notes: string;
  comparison_summary: ComparisonSummary;
  experiment_snapshots: ExperimentSnapshot[];
  warnings: string[];
  limitations: string[];
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  no_production_influence: boolean;
  not_eligible_for_promotion: boolean;
  safety_flags?: Record<string, boolean>;
  status?: string;
}

export interface CreateComparisonPayload {
  name: string;
  experiment_ids: string[];
  metric_priority?: string[];
  notes?: string;
  research_acknowledgement: boolean;
}

export interface ArchiveComparisonPayload {
  acknowledgement: boolean;
  reason?: string;
}

export interface ComparisonVerifyResult {
  comparison_id: string;
  experiment_ids: string[];
  lifecycle_state: string;
  warnings: string[];
  healthy: boolean;
  safety_flags: Record<string, boolean>;
}

export async function createFinrlxExperimentComparison(
  payload: CreateComparisonPayload
): Promise<ApiResponse<ExperimentComparison>> {
  return apiFetch<ExperimentComparison>("/api/v1/rl/finrlx/experiment-comparisons", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listFinrlxExperimentComparisons(params?: {
  lifecycle_state?: string;
  limit?: number;
}): Promise<ApiResponse<ExperimentComparison[]>> {
  const qs = new URLSearchParams();
  if (params?.lifecycle_state) qs.set("lifecycle_state", params.lifecycle_state);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<ExperimentComparison[]>(`/api/v1/rl/finrlx/experiment-comparisons${query ? `?${query}` : ""}`);
}

export async function getFinrlxExperimentComparison(
  comparisonId: string
): Promise<ApiResponse<ExperimentComparison>> {
  return apiFetch<ExperimentComparison>(`/api/v1/rl/finrlx/experiment-comparisons/${comparisonId}`);
}

export async function archiveFinrlxExperimentComparison(
  comparisonId: string,
  payload: ArchiveComparisonPayload
): Promise<ApiResponse<ExperimentComparison>> {
  return apiFetch<ExperimentComparison>(`/api/v1/rl/finrlx/experiment-comparisons/${comparisonId}/archive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function verifyFinrlxExperimentComparison(
  comparisonId: string
): Promise<ApiResponse<ComparisonVerifyResult>> {
  return apiFetch<ComparisonVerifyResult>(`/api/v1/rl/finrlx/experiment-comparisons/${comparisonId}/verify`);
}

export async function rebuildFinrlxExperimentComparisonRegistry(
  payload: { acknowledgement: boolean }
): Promise<ApiResponse<{ rebuilt: boolean; comparison_count: number }>> {
  return apiFetch<{ rebuilt: boolean; comparison_count: number }>("/api/v1/rl/finrlx/experiment-comparisons/rebuild-registry", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ── Research Readiness Review Gates (Phase 8L.1) ───────────────────

export type ReadinessState = "draft" | "needs_more_evidence" | "research_review_ready" | "archived";

export interface ReadinessFinding {
  finding_id: string;
  severity: "info" | "warning" | "blocking";
  message: string;
  operator_action: string;
}

export interface ReadinessChecklist {
  comparison_exists: boolean;
  experiments_exist: boolean;
  exports_exist: boolean;
  result_metadata_present: boolean;
  metric_coverage_reviewed: boolean;
  missing_metrics_reviewed: boolean;
  warnings_reviewed: boolean;
  limitations_reviewed: boolean;
  safety_flags_confirmed: boolean;
}

export interface ReadinessReview {
  readiness_id: string;
  created_at: string;
  updated_at: string;
  readiness_state: ReadinessState;
  name: string;
  linked_comparison_id: string;
  linked_experiment_ids: string[];
  linked_export_ids: string[];
  operator_notes: string;
  checklist: ReadinessChecklist;
  evidence_summary: Record<string, unknown>;
  readiness_findings: ReadinessFinding[];
  suggested_readiness_state: string;
  warnings: string[];
  limitations: string[];
  research_only: boolean;
  offline_only: boolean;
  shadow_only: boolean;
  no_production_influence: boolean;
  not_eligible_for_promotion: boolean;
  safety_flags?: Record<string, boolean>;
  status?: string;
}

export interface CreateReadinessPayload {
  name: string;
  linked_comparison_id: string;
  operator_notes?: string;
  checklist?: Partial<ReadinessChecklist>;
  research_acknowledgement: boolean;
}

export interface ReadinessStatePayload {
  readiness_state: ReadinessState;
  acknowledgement: boolean;
  reason?: string;
}

export interface ReadinessArchivePayload {
  acknowledgement: boolean;
  reason?: string;
}

export interface ReadinessVerifyResult {
  readiness_id: string;
  linked_comparison_id: string;
  linked_experiment_ids: string[];
  readiness_state: string;
  warnings: string[];
  healthy: boolean;
  safety_flags: Record<string, boolean>;
}

export async function createFinrlxResearchReadiness(
  payload: CreateReadinessPayload
): Promise<ApiResponse<ReadinessReview>> {
  return apiFetch<ReadinessReview>("/api/v1/rl/finrlx/research-readiness", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function listFinrlxResearchReadiness(params?: {
  readiness_state?: string; limit?: number;
}): Promise<ApiResponse<ReadinessReview[]>> {
  const qs = new URLSearchParams();
  if (params?.readiness_state) qs.set("readiness_state", params.readiness_state);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return apiFetch<ReadinessReview[]>(`/api/v1/rl/finrlx/research-readiness${query ? `?${query}` : ""}`);
}

export async function getFinrlxResearchReadiness(
  readinessId: string
): Promise<ApiResponse<ReadinessReview>> {
  return apiFetch<ReadinessReview>(`/api/v1/rl/finrlx/research-readiness/${readinessId}`);
}

export async function updateFinrlxResearchReadinessState(
  readinessId: string, payload: ReadinessStatePayload
): Promise<ApiResponse<ReadinessReview>> {
  return apiFetch<ReadinessReview>(`/api/v1/rl/finrlx/research-readiness/${readinessId}/state`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function archiveFinrlxResearchReadiness(
  readinessId: string, payload: ReadinessArchivePayload
): Promise<ApiResponse<ReadinessReview>> {
  return apiFetch<ReadinessReview>(`/api/v1/rl/finrlx/research-readiness/${readinessId}/archive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function verifyFinrlxResearchReadiness(
  readinessId: string
): Promise<ApiResponse<ReadinessVerifyResult>> {
  return apiFetch<ReadinessVerifyResult>(`/api/v1/rl/finrlx/research-readiness/${readinessId}/verify`);
}

// ── Phase 8N.1 — Persistence Status ──

export interface FinrlxRegistryPersistenceStatus {
  registry_name: string;
  registry_kind: string;
  directory_path: string;
  registry_file_path: string;
  directory_exists: boolean;
  registry_file_exists: boolean;
  directory_readable: boolean;
  directory_writable: boolean;
  registry_file_readable: boolean;
  registry_file_writable: boolean;
  item_count: number;
  status: "ok" | "missing" | "degraded" | "unavailable";
  warnings: string[];
}

export interface FinrlxPersistenceStatus {
  storage_mode: string;
  storage_root: string;
  is_local_file_backed: boolean;
  is_database_backed: boolean;
  is_persistent_volume_configured: boolean;
  deployment_environment: string;
  appears_containerized: boolean;
  registry_statuses: FinrlxRegistryPersistenceStatus[];
  warnings: string[];
  limitations: string[];
  recommended_next_action: string | null;
  storage_root_uses_persistent_volume: boolean;
  persistent_volume_mount_path: string | null;
  database_metadata_mirror?: {
    available: boolean;
    artifact_storage_database_backed: boolean;
    local_registries_still_operational_source: boolean;
  };
  research_only: boolean;
  offline_only: boolean;
  no_production_influence: boolean;
}

export async function getFinrlxPersistenceStatus(): Promise<ApiResponse<FinrlxPersistenceStatus>> {
  return apiFetch<FinrlxPersistenceStatus>("/api/v1/rl/finrlx/persistence/status");
}

// ── Phase 8N.2A — Registry Metadata Mirror ──

export interface FinrlxRegistryMetadataMirrorStatus {
  is_database_metadata_mirror_enabled: boolean;
  is_database_backed_artifact_storage: boolean;
  local_registries_still_operational_source: boolean;
  total_mirrored_records: number;
  counts_by_registry_kind: Record<string, number>;
  counts_by_mirror_status: Record<string, number>;
  latest_sync_at: string | null;
  warnings: string[];
  limitations: string[];
  research_only: boolean;
  offline_only: boolean;
  no_production_influence: boolean;
}

export interface FinrlxRegistryMetadataSyncResult {
  dry_run: boolean;
  candidates_seen: number;
  inserted_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  counts_by_registry_kind: Record<string, number>;
  warnings: string[];
  limitations: string[];
  research_only: boolean;
  offline_only: boolean;
  no_production_influence: boolean;
}

export async function getFinrlxRegistryMetadataMirrorStatus(): Promise<ApiResponse<FinrlxRegistryMetadataMirrorStatus>> {
  return apiFetch<FinrlxRegistryMetadataMirrorStatus>("/api/v1/rl/finrlx/registry-metadata/status");
}

export async function syncFinrlxRegistryMetadataMirror(params: { dry_run: boolean }): Promise<ApiResponse<FinrlxRegistryMetadataSyncResult>> {
  return apiFetch<FinrlxRegistryMetadataSyncResult>("/api/v1/rl/finrlx/registry-metadata/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
}

// ── Phase A1 — Universe workspace ──

export interface UniverseListItem {
  universe_id: string;
  name: string;
  description: string | null;
  asset_count: number;
}

export interface UniverseAsset {
  asset_id: string;
  ticker: string;
  name: string;
  sector: string | null;
  is_active: boolean;
}

export interface UniverseDetail {
  universe_id: string;
  name: string;
  description: string | null;
  asset_count: number;
  active_asset_count: number;
  tickers: string[];
  assets: UniverseAsset[];
}

export interface UniverseCoverageDomain {
  covered: number;
  total: number;
  pct: number;
}

export interface UniverseCoverage {
  universe_id: string;
  asset_count: number;
  coverage: {
    market_bars: UniverseCoverageDomain;
    features: UniverseCoverageDomain;
    signals: UniverseCoverageDomain;
    model_predictions: UniverseCoverageDomain;
  };
}

export interface UniverseReadiness extends UniverseCoverage {
  readiness_status: "ready" | "incomplete";
  warnings: string[];
}

export async function fetchUniverses(): Promise<ApiResponse<UniverseListItem[]>> {
  return apiFetch<UniverseListItem[]>("/api/v1/universes");
}

export async function fetchUniverseDetail(universeId: string): Promise<ApiResponse<UniverseDetail>> {
  return apiFetch<UniverseDetail>(`/api/v1/universes/${universeId}`);
}

export async function fetchUniverseCoverage(universeId: string): Promise<ApiResponse<UniverseCoverage>> {
  return apiFetch<UniverseCoverage>(`/api/v1/universes/${universeId}/coverage`);
}

export async function fetchUniverseReadiness(universeId: string): Promise<ApiResponse<UniverseReadiness>> {
  return apiFetch<UniverseReadiness>(`/api/v1/universes/${universeId}/readiness`);
}

// Phase A2 ops types + fetchers are already declared above (OpsData,
// fetchOps, approveQueueItem, deferQueueItem, challengeQueueItem,
// QueueActionResult). The /ops page consumes those directly.

// ── Phase A3 — Policy Editor ──

export interface PolicyRule {
  id: string;
  key: string;
  name: string;
  category: string;
  description: string | null;
  severity: "low" | "mid" | "high" | string;
  threshold_value: number;
  threshold_unit: string;
  applies_to: string;
  is_active: boolean;
  is_enforced: boolean;
  version: number;
}

export interface PolicyHistoryEntry {
  id: string;
  policy_rule_key: string;
  previous_value: number;
  new_value: number;
  actor: string;
  reason: string | null;
  created_at: string | null;
}

export interface PolicyBreach {
  kind: string;
  label: string;
  utilization: number;
  trend: string;
  severity: string;
  related: string;
  is_active: boolean;
}

export async function fetchPolicyRules(): Promise<ApiResponse<PolicyRule[]>> {
  return apiFetch<PolicyRule[]>("/api/v1/policies/rules");
}

export async function fetchPolicyHistory(key: string): Promise<ApiResponse<PolicyHistoryEntry[]>> {
  return apiFetch<PolicyHistoryEntry[]>(`/api/v1/policies/rules/${encodeURIComponent(key)}/history`);
}

export async function fetchPolicyBreaches(): Promise<ApiResponse<PolicyBreach[]>> {
  return apiFetch<PolicyBreach[]>("/api/v1/policies/breaches");
}

export async function updatePolicyRule(
  key: string,
  threshold_value: number,
  actor: string,
  reason?: string,
): Promise<ApiResponse<PolicyRule>> {
  return apiFetch<PolicyRule>(`/api/v1/policies/rules/${encodeURIComponent(key)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ threshold_value, actor, reason }),
  });
}

// ── Phase A4 — Integrations ──

export interface Integration {
  source_key: string;
  name: string;
  category: "market_data" | "news" | "fundamentals" | "sentiment" | string;
  status: "healthy" | "degraded" | "stale" | "placeholder" | string;
  is_real_provider: boolean;
  is_placeholder: boolean;
  last_manifest_id: string | null;
  last_success_at: string | null;
  freshness: string;
  coverage: string;
  warnings: string[];
  next_action: string | null;
}

export interface IntegrationHealth {
  total_integrations: number;
  healthy: number;
  degraded: number;
  placeholder: number;
  real_providers: number;
  all_real_healthy?: boolean;
}

export async function fetchIntegrations(): Promise<ApiResponse<Integration[]>> {
  return apiFetch<Integration[]>("/api/v1/integrations");
}

export async function fetchIntegrationHealth(): Promise<ApiResponse<IntegrationHealth>> {
  return apiFetch<IntegrationHealth>("/api/v1/integrations/health");
}

// ── Phase B1 — Risk workspace ──

export interface RiskSectorWeight {
  sector: string;
  weight: number;
}

export interface RiskConcentration {
  total_positions: number;
  top1_weight: number;
  top3_weight: number;
  top5_weight: number;
  sectors: RiskSectorWeight[];
}

export interface RiskDrawdown {
  current_drawdown: number;
  max_drawdown: number;
  peak_value: number | null;
  current_value: number | null;
}

export interface RiskVaR {
  sample_size: number;
  var_95: number;
  var_99: number;
  volatility_daily: number;
}

export interface RiskExposure {
  long_weight: number;
  short_weight: number;
  gross_exposure: number;
  net_exposure: number;
  cash_weight: number;
}

export interface RiskBundle {
  portfolio_id: string;
  portfolio_name: string;
  concentration: RiskConcentration;
  drawdown: RiskDrawdown;
  var: RiskVaR;
  exposure: RiskExposure;
  snapshot_count: number;
}

export async function fetchCurrentRisk(): Promise<ApiResponse<RiskBundle | null>> {
  return apiFetch<RiskBundle | null>("/api/v1/risk/current");
}

// ── Phase B2 — News intelligence ──

export interface NewsItem {
  source: string;
  title: string;
  link: string;
  summary: string;
  published: string | null;
  sentiment_compound: number;
  sentiment_label: "positive" | "neutral" | "negative" | string;
}

export interface NewsSummary {
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  mean_compound: number;
}

export interface NewsBundle {
  summary: NewsSummary;
  items: NewsItem[];
}

export async function fetchNews(refresh = false): Promise<ApiResponse<NewsBundle>> {
  return apiFetch<NewsBundle>(`/api/v1/news${refresh ? "?refresh=true" : ""}`);
}

// ── Phase B3 — Saved views ──
// These endpoints require an authenticated session. Bearer is injected
// explicitly via the auth helper. The shared apiFetch is anonymous by
// design — changing it project-wide is out of B3's scope, so we wrap here.

import { getAccessToken } from "./auth";

export interface SavedView {
  id: string;
  name: string;
  scope: string;
  filters: Record<string, unknown>;
  tone: string | null;
  created_at: string;
  updated_at: string;
}

function _savedViewsAuthHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const t = getAccessToken();
  const headers: Record<string, string> = { ...extra };
  if (t) headers.Authorization = `Bearer ${t}`;
  return headers;
}

export async function fetchSavedViews(): Promise<ApiResponse<SavedView[]>> {
  return apiFetch<SavedView[]>("/api/v1/saved-views", { headers: _savedViewsAuthHeaders() });
}

export async function createSavedView(payload: {
  name: string;
  scope: string;
  filters?: Record<string, unknown>;
  tone?: string | null;
}): Promise<ApiResponse<SavedView>> {
  return apiFetch<SavedView>("/api/v1/saved-views", {
    method: "POST",
    headers: _savedViewsAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function deleteSavedView(id: string): Promise<ApiResponse<{ id: string; deleted: boolean }>> {
  return apiFetch<{ id: string; deleted: boolean }>(`/api/v1/saved-views/${id}`, {
    method: "DELETE",
    headers: _savedViewsAuthHeaders(),
  });
}

// ── Phase 16 — Research fundamentals + peers ────────────────────────
// Backend contract: app/api/v1/research_fundamentals.py.  Endpoints
// always return 200 with a structurally-complete envelope; when no
// provider is configured the envelope is tagged source="stub" and
// carries a coverage_note.  Frontend never has to handle a 503 here.

export interface FundamentalsData {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  description: string | null;
  market_cap_usd: number | null;
  pe_ratio_ttm: number | null;
  forward_pe: number | null;
  price_to_book: number | null;
  price_to_sales_ttm: number | null;
  ev_to_ebitda: number | null;
  gross_margin_ttm: number | null;
  operating_margin_ttm: number | null;
  net_margin_ttm: number | null;
  revenue_ttm_usd: number | null;
  revenue_growth_yoy: number | null;
  eps_ttm: number | null;
  dividend_yield: number | null;
  "52w_high"?: number | null;
  "52w_low"?: number | null;
  as_of: string | null;
  source: string;
  cached_at: string | null;
  coverage_note: string | null;
}

export interface PeerEntryData {
  ticker: string;
  name: string | null;
  sector: string | null;
  industry: string | null;
  market_cap_usd: number | null;
  last_close_usd: number | null;
  change_pct_1d: number | null;
  change_pct_ytd: number | null;
}

export interface PeersData {
  target_ticker: string;
  target_sector: string | null;
  target_industry: string | null;
  peers: PeerEntryData[];
  as_of: string | null;
  source: string;
  cached_at: string | null;
  coverage_note: string | null;
}

export async function fetchFundamentals(
  ticker: string,
): Promise<ApiResponse<FundamentalsData>> {
  return apiFetch<FundamentalsData>(
    `/api/v1/research/fundamentals/${encodeURIComponent(ticker)}`,
  );
}

export async function fetchPeers(ticker: string): Promise<ApiResponse<PeersData>> {
  return apiFetch<PeersData>(`/api/v1/research/peers/${encodeURIComponent(ticker)}`);
}

// ── Phase 17 — Research documents (PDF uploads + LLM analysis) ──────
// Backend contract: app/api/v1/research_documents.py.  Auth required
// on every endpoint (the frontend injects Bearer via getAccessToken()).

export interface DocumentSummaryData {
  id: string;
  ticker: string;
  filename: string;
  mime_type: string;
  file_size_bytes: number;
  extracted_text_tokens_estimate: number | null;
  extraction_status: "pending" | "extracting" | "ready" | "failed" | string;
  extraction_error: string | null;
  uploaded_by_email: string;
  uploaded_at: string;
}

export interface DocumentDetailData extends DocumentSummaryData {
  extracted_text: string | null;
}

export interface DocumentListData {
  ticker: string;
  documents: DocumentSummaryData[];
  total: number;
}

export interface DocumentAnalysisData {
  id: string;
  document_id: string;
  prompt: string;
  response: string;
  created_by_email: string;
  provider: string;
  model: string;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_estimate_usd: number | null;
  created_at: string;
}

export interface BudgetUsageData {
  year: number;
  month: number;
  cap_tokens: number;
  used_tokens: number;
  remaining_tokens: number;
  cost_estimate_usd: number;
  over_budget: boolean;
  per_provider: Record<string, { input_tokens: number; output_tokens: number; cost_estimate_usd: number }>;
}

function _docsAuthHeaders(extra?: Record<string, string>): Record<string, string> {
  const t = getAccessToken();
  return { ...(t ? { Authorization: `Bearer ${t}` } : {}), ...(extra ?? {}) };
}

export async function fetchDocuments(ticker: string): Promise<ApiResponse<DocumentListData>> {
  return apiFetch<DocumentListData>(
    `/api/v1/research/documents?ticker=${encodeURIComponent(ticker)}`,
    { headers: _docsAuthHeaders() },
  );
}

export async function fetchDocument(documentId: string): Promise<ApiResponse<DocumentDetailData>> {
  return apiFetch<DocumentDetailData>(
    `/api/v1/research/documents/${encodeURIComponent(documentId)}`,
    { headers: _docsAuthHeaders() },
  );
}

export async function uploadDocument(
  ticker: string,
  file: File,
): Promise<ApiResponse<DocumentDetailData>> {
  const form = new FormData();
  form.set("ticker", ticker);
  form.set("file", file);
  return apiFetch<DocumentDetailData>("/api/v1/research/documents", {
    method: "POST",
    body: form,
    // Do NOT set Content-Type explicitly — the browser fills in the
    // multipart boundary. Only inject the auth header.
    headers: _docsAuthHeaders(),
  });
}

export async function deleteDocument(
  documentId: string,
): Promise<ApiResponse<{ id: string; deleted: boolean }>> {
  return apiFetch<{ id: string; deleted: boolean }>(
    `/api/v1/research/documents/${encodeURIComponent(documentId)}`,
    {
      method: "DELETE",
      headers: _docsAuthHeaders(),
    },
  );
}

export async function fetchAnalyses(
  documentId: string,
): Promise<ApiResponse<DocumentAnalysisData[]>> {
  return apiFetch<DocumentAnalysisData[]>(
    `/api/v1/research/documents/${encodeURIComponent(documentId)}/analyses`,
    { headers: _docsAuthHeaders() },
  );
}

export async function analyzeDocument(
  documentId: string,
  prompt: string,
): Promise<ApiResponse<DocumentAnalysisData>> {
  return apiFetch<DocumentAnalysisData>(
    `/api/v1/research/documents/${encodeURIComponent(documentId)}/analyze`,
    {
      method: "POST",
      headers: _docsAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ prompt }),
    },
  );
}

export async function fetchBudgetUsage(): Promise<ApiResponse<BudgetUsageData>> {
  return apiFetch<BudgetUsageData>("/api/v1/research/documents/_usage", {
    headers: _docsAuthHeaders(),
  });
}

// ── Phase 18 — SEC EDGAR auto-ingest + cross-quarter insights ──────

// Phase 18.6.1 — Structured metrics block parsed out of the LLM
// response. The TrajectoryChart component renders this as a per-metric
// line chart. Null when the LLM didn't emit a valid JSON block.
export interface TickerInsightsMetricsData {
  metrics: Array<{
    name: string;
    unit: string;
    quarters: Array<{
      period_end: string;
      label: string;
      value: number;
    }>;
  }>;
}

export interface TickerInsightsData {
  id: string;
  ticker: string;
  summary_text: string;
  metrics: TickerInsightsMetricsData | null;
  quarters_covered: string[];
  provider: string;
  model: string;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_estimate_usd: number | null;
  generated_at: string;
  generated_by_email: string;
}

export interface AutoIngestFailureData {
  accession_no: string;
  form: string;
  reason: string;
}

export interface AutoIngestData {
  ticker: string;
  cik: string;
  ingested: number;
  skipped_existing: number;
  failed: number;
  failures: AutoIngestFailureData[];
  document_ids: string[];
}

// GET — returns null in `data` when no insights have been generated yet.
export async function fetchInsights(
  ticker: string,
): Promise<ApiResponse<TickerInsightsData | null>> {
  return apiFetch<TickerInsightsData | null>(
    `/api/v1/research/${encodeURIComponent(ticker)}/insights`,
    { headers: _docsAuthHeaders() },
  );
}

// POST — generates a NEW TickerInsights row from current sec_auto documents.
// Returns 409 if there are no documents ready; the FE should chain
// triggerAutoIngest() first.
export async function generateInsights(
  ticker: string,
): Promise<ApiResponse<TickerInsightsData>> {
  return apiFetch<TickerInsightsData>(
    `/api/v1/research/${encodeURIComponent(ticker)}/insights`,
    {
      method: "POST",
      headers: _docsAuthHeaders(),
    },
  );
}

// POST — fetches the last `limit` quarterly filings from SEC EDGAR,
// downloads + extracts, persists as research_documents rows. Idempotent
// (dedups via (ticker, sec_accession_no) unique index).
export async function triggerAutoIngest(
  ticker: string,
  limit: number = 6,
): Promise<ApiResponse<AutoIngestData>> {
  return apiFetch<AutoIngestData>(
    `/api/v1/research/${encodeURIComponent(ticker)}/auto-ingest?limit=${limit}`,
    {
      method: "POST",
      headers: _docsAuthHeaders(),
    },
  );
}