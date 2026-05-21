/**
 * Home data adapter — aggregates frontend API calls into a single decision-
 * oriented view model. Uses Promise.allSettled so one failing source does not
 * blank the entire homepage.
 *
 * No new backend endpoints are added; this module only re-shapes existing
 * data and labels honestly what is unavailable.
 */

import {
  fetchActivity,
  fetchCurrentPaper,
  fetchCurrentRecommendation,
  fetchCurrentRisk,
  fetchDisagreement,
  fetchEngineComparison,
  fetchEvidence,
  fetchNews,
  fetchOps,
  fetchOverview,
  fetchRegime,
  type ActivityFeedData,
  type DisagreementData,
  type EngineComparisonData,
  type EvidenceNarrativeData,
  type NewsBundle,
  type OpsData,
  type OverviewData,
  type PaperPortfolioData,
  type RecommendationDetail,
  type RegimeData,
  type RiskBundle,
} from "@/services/api";

import type {
  GovernanceStatus,
  HomeDecisionAction,
  HomeDecisionItem,
  HomeSourceState,
  HomeSourceStatus,
  HomeViewModel,
  OpportunityRadarRow,
  OpportunityRiskLevel,
  OpportunitySignalLabel,
  PortfolioImpactSummary,
  RegimeStatus,
  ResearchEventItem,
  SectorTiltRow,
  ShadowResearchSummary,
  SystemHealthRow,
} from "./homeTypes";

interface RawSources {
  overview?: { data: OverviewData; warnings: string[]; freshness: { data_as_of: string | null; is_stale: boolean } | null };
  recommendation?: RecommendationDetail | null;
  regime?: RegimeData;
  activity?: ActivityFeedData;
  ops?: OpsData;
  paper?: PaperPortfolioData | null;
  risk?: RiskBundle | null;
  news?: NewsBundle;
  comparison?: EngineComparisonData | null;
  disagreement?: DisagreementData | null;
  evidence?: EvidenceNarrativeData | null;
}

type SourceFailures = Record<string, string>;

export interface HomeDataResult {
  view: HomeViewModel;
  failures: SourceFailures;
}

const ACTION_LABELS: Record<HomeDecisionAction, string> = {
  "review-evidence": "Review evidence",
  "open-decision": "Open decision",
  "compare-engines": "Compare engines",
  "view-risk": "View risk",
  monitor: "Monitor",
  "open-ops": "Open ops",
  defer: "Defer",
};

function firstNameFromEmail(email: string | undefined | null): string {
  if (!email) return "there";
  const local = email.split("@")[0] || "there";
  const first = local.split(/[._-]/)[0] || "there";
  return first.charAt(0).toUpperCase() + first.slice(1);
}

function statusFromFreshness(
  asOf: string | null | undefined,
  isStale: boolean | undefined,
): HomeSourceState {
  if (!asOf) return "unavailable";
  if (isStale) return "stale";
  return "ok";
}

function severityFromOpsFlag(flag: string): "info" | "warning" | "critical" {
  const f = flag.toLowerCase();
  if (f.includes("breach") || f.includes("critical")) return "critical";
  if (f.includes("stale") || f.includes("warn") || f.includes("caveat") || f.includes("limit")) {
    return "warning";
  }
  return "info";
}

function safeIso(value: unknown): string | null {
  if (typeof value !== "string") return null;
  return value || null;
}

function buildSourceStatuses(raw: RawSources, failures: SourceFailures): HomeSourceStatus[] {
  const out: HomeSourceStatus[] = [];

  const overviewFreshness = raw.overview?.freshness ?? null;
  out.push({
    source: "pipeline",
    status: failures.overview
      ? "unavailable"
      : statusFromFreshness(overviewFreshness?.data_as_of, overviewFreshness?.is_stale),
    label: "Pipeline data",
    asOf: overviewFreshness?.data_as_of ?? null,
    warning: failures.overview ?? null,
  });

  out.push({
    source: "recommendation",
    status: failures.recommendation
      ? "unavailable"
      : raw.recommendation
        ? "ok"
        : "warning",
    label: "Current recommendation",
    asOf: raw.recommendation?.data_as_of ?? null,
    warning: failures.recommendation ?? (raw.recommendation ? null : "No current recommendation"),
  });

  out.push({
    source: "regime",
    status: failures.regime ? "unavailable" : raw.regime ? "ok" : "warning",
    label: "Regime",
    asOf: raw.regime?.as_of ?? null,
    warning: failures.regime ?? null,
  });

  out.push({
    source: "ops",
    status: failures.ops ? "unavailable" : raw.ops ? "ok" : "warning",
    label: "Operations",
    asOf: null,
    warning: failures.ops ?? null,
  });

  out.push({
    source: "risk",
    status: failures.risk
      ? "unavailable"
      : raw.risk
        ? "ok"
        : "warning",
    label: "Risk",
    asOf: null,
    warning: failures.risk ?? (raw.risk ? null : "No portfolio risk snapshot"),
  });

  return out;
}

function buildGovernance(raw: RawSources): GovernanceStatus {
  const ops = raw.ops;
  const ml = ops?.ml_ops ?? null;
  const rl = ops?.rl ?? null;

  // Live pipeline influence: pessimistic OR — if ANY surface reports influence, warn.
  const livePipelineInfluence =
    Boolean(ml?.any_model_influences_live_pipeline) || Boolean(rl?.live_pipeline_influence);

  const rlShadowOnly = rl ? Boolean(rl.is_shadow_only) : true;
  const mlShadowOnly = ml ? Boolean(ml.ml_is_shadow_only) : true;

  const overviewFreshness = raw.overview?.freshness ?? null;
  const dataFreshnessWarning =
    Boolean(overviewFreshness?.is_stale) ||
    raw.recommendation?.warnings?.some((w) => /stale|freshness/i.test(w)) ||
    false;

  const warnings: string[] = [];
  if (livePipelineInfluence) {
    warnings.push(
      "A model or RL agent is reporting live pipeline influence — review Ops before publishing.",
    );
  }
  if (!rlShadowOnly) {
    warnings.push("RL agents are not flagged shadow-only.");
  }
  if (!mlShadowOnly) {
    warnings.push("ML models are not flagged shadow-only.");
  }

  const lastPipelineRun =
    raw.recommendation?.created_at ?? raw.overview?.data.last_published_at ?? null;

  return {
    researchOnly: true,
    noBrokerExecution: true,
    rlShadowOnly,
    mlShadowOnly,
    livePipelineInfluence,
    dataFreshnessWarning,
    lastPipelineRun,
    warnings,
  };
}

function buildRegime(raw: RawSources): RegimeStatus | null {
  if (!raw.regime) return null;
  return {
    label: raw.regime.regime_label,
    confidence: raw.regime.regime_confidence,
    persistenceDays: raw.regime.persistence_days,
    asOf: raw.regime.as_of,
  };
}

function buildDecisionQueue(raw: RawSources): HomeDecisionItem[] {
  const items: HomeDecisionItem[] = [];
  const ops = raw.ops;

  // 1. Ops queue items first — they are the explicit pending-review surface.
  for (const q of ops?.queue ?? []) {
    const breachFlag = (q.flags || []).find((f) => /breach/i.test(f));
    const severityFlag = breachFlag
      ? "critical"
      : (q.flags || []).some((f) => /stale|caveat|limit|warn/i.test(f))
        ? "warning"
        : "info";
    items.push({
      id: q.id || `ops-${q.recommendation_id}`,
      ticker: q.ticker || null,
      title: `${q.ticker} · ${q.stance.toUpperCase()}`,
      reason:
        (q.flags && q.flags.length > 0)
          ? `${q.flags.join(" · ")} (submitted ${q.submitted_ago} by ${q.submitter})`
          : `Submitted ${q.submitted_ago} by ${q.submitter}`,
      severity: severityFlag as "info" | "warning" | "critical",
      decisionState: q.status || "pending",
      evidenceCount: 0,
      lastUpdated: null,
      nextAction: "review-evidence",
      actionLabel: ACTION_LABELS["review-evidence"],
      href: "/ops",
      source: "ops.queue",
    });
  }

  // 2. Pipeline-level meta warnings from /overview (newer draft, etc.)
  for (const w of raw.overview?.warnings ?? []) {
    items.push({
      id: `pipeline-warning-${items.length}`,
      ticker: null,
      title: "Pipeline notice",
      reason: w,
      severity: /stale|breach|incident/i.test(w) ? "warning" : "info",
      decisionState: "pending",
      evidenceCount: 0,
      lastUpdated: raw.overview?.freshness?.data_as_of ?? null,
      nextAction: "review-evidence",
      actionLabel: ACTION_LABELS["review-evidence"],
      href: "/decision",
      source: "overview.warnings",
    });
  }

  // 3. Active recommendation warnings get surfaced.
  const rec = raw.recommendation;
  if (rec && rec.warnings && rec.warnings.length > 0) {
    for (const w of rec.warnings) {
      items.push({
        id: `rec-warning-${rec.id}-${items.length}`,
        ticker: null,
        title: "Recommendation warning",
        reason: w,
        severity: /breach|stale/i.test(w) ? "warning" : "info",
        decisionState: rec.status,
        evidenceCount: 0,
        lastUpdated: rec.data_as_of,
        nextAction: "review-evidence",
        actionLabel: ACTION_LABELS["review-evidence"],
        href: "/decision",
        source: "recommendation.warnings",
      });
    }
  }

  // 4. Active incidents / breaches from ops.
  for (const incident of ops?.incidents ?? []) {
    items.push({
      id: `incident-${incident.id}`,
      ticker: null,
      title: incident.title,
      reason: `${incident.severity} · owner ${incident.owner} · ${incident.note || incident.status}`,
      severity: incident.severity?.toLowerCase() === "critical" ? "critical" : "warning",
      decisionState: incident.status,
      evidenceCount: 0,
      lastUpdated: incident.started,
      nextAction: "open-ops",
      actionLabel: ACTION_LABELS["open-ops"],
      href: "/ops",
      source: "ops.incidents",
    });
  }

  for (const breach of ops?.breaches ?? []) {
    items.push({
      id: `breach-${breach.kind}-${items.length}`,
      ticker: null,
      title: `Breach · ${breach.label}`,
      reason: `${breach.severity} · utilization ${(breach.utilization * 100).toFixed(0)}% · related ${breach.related}`,
      severity: severityFromOpsFlag(breach.severity),
      decisionState: "active",
      evidenceCount: 0,
      lastUpdated: null,
      nextAction: "view-risk",
      actionLabel: ACTION_LABELS["view-risk"],
      href: "/risk",
      source: "ops.breaches",
    });
  }

  // Rank: critical → warning → info, stable within tier.
  const rank: Record<string, number> = { critical: 0, warning: 1, info: 2 };
  items.sort((a, b) => (rank[a.severity] ?? 9) - (rank[b.severity] ?? 9));

  return items.slice(0, 12);
}

function buildOpportunities(raw: RawSources): OpportunityRadarRow[] {
  const rec = raw.recommendation;
  if (!rec || !rec.weights || rec.weights.length === 0) return [];

  const dispersion = raw.disagreement?.dispersion ?? null;
  const dominantStance = raw.disagreement?.dominant_stance?.toLowerCase() ?? null;
  const dataFreshness =
    rec.data_as_of ??
    raw.overview?.freshness?.data_as_of ??
    null;

  // Take top-conviction picks by absolute weight delta.
  const sorted = [...rec.weights].sort((a, b) => {
    const da = Math.abs(a.delta ?? 0);
    const db = Math.abs(b.delta ?? 0);
    return db - da;
  });

  const top = sorted.slice(0, 8);

  return top.map((w) => {
    const isOver = (w.stance ?? "").toLowerCase().includes("over");
    const isUnder = (w.stance ?? "").toLowerCase().includes("under");
    let signalLabel: OpportunitySignalLabel = "neutral";
    if (dispersion !== null && dispersion > 0.5) {
      signalLabel = "conflicted";
    } else if (isOver) {
      signalLabel = "bullish";
    } else if (isUnder) {
      signalLabel = "bearish";
    } else if (dominantStance === "overweight") {
      signalLabel = "bullish";
    } else if (dominantStance === "underweight") {
      signalLabel = "bearish";
    }

    const riskLevel: OpportunityRiskLevel = (() => {
      const wt = Math.abs(w.target_weight ?? 0);
      if (wt > 0.1) return "high";
      if (wt > 0.04) return "medium";
      return "low";
    })();

    const trigger =
      w.rationale ||
      (w.delta !== null
        ? `${w.delta >= 0 ? "Δ +" : "Δ "}${(w.delta * 100).toFixed(2)}% weight change`
        : "Weight unchanged");

    const evidenceSources: string[] = [];
    if (raw.evidence?.items?.length) evidenceSources.push("evidence");
    if (raw.comparison?.engines?.length) evidenceSources.push("engines");
    if (raw.regime) evidenceSources.push("regime");

    return {
      ticker: w.ticker,
      companyName: w.name,
      trigger,
      compositeSignal: w.delta,
      signalLabel,
      riskLevel,
      dataFreshness,
      evidenceSources,
      recommendationState: rec.status,
      href: "/decision",
    };
  });
}

function buildPortfolio(raw: RawSources): PortfolioImpactSummary {
  const paper = raw.paper;
  const risk = raw.risk;

  if (!paper) {
    return {
      hasPortfolio: false,
      riskWarning: risk ? null : "No active paper portfolio.",
    };
  }

  const topHoldings = (paper.holdings ?? [])
    .slice()
    .sort((a, b) => (b.target_weight ?? 0) - (a.target_weight ?? 0))
    .slice(0, 3)
    .map((h) => ({ ticker: h.ticker, weight: h.target_weight, drift: h.drift }));

  let riskWarning: string | null = null;
  if (risk) {
    if (risk.drawdown.current_drawdown < -0.1) {
      riskWarning = `Drawdown ${(risk.drawdown.current_drawdown * 100).toFixed(1)}%`;
    } else if (risk.concentration.top1_weight > 0.25) {
      riskWarning = `Top position is ${(risk.concentration.top1_weight * 100).toFixed(0)}% of portfolio`;
    }
  }

  return {
    hasPortfolio: true,
    portfolioName: paper.name,
    invested: paper.invested_weight,
    cash: paper.cash_weight,
    totalRebalances: paper.total_rebalances,
    lastRebalanceAt: paper.last_rebalance_at,
    topHoldings,
    riskWarning,
  };
}

function buildResearchEvents(raw: RawSources): ResearchEventItem[] {
  const out: ResearchEventItem[] = [];

  for (const ev of raw.activity?.events?.slice(0, 6) ?? []) {
    const tone: ResearchEventItem["tone"] =
      ev.kind === "breach" || ev.kind === "incident"
        ? "warning"
        : ev.kind === "publish"
          ? "info"
          : "muted";
    out.push({
      kind: "audit",
      title: `${ev.actor} ${ev.description}`,
      detail: ev.detail,
      source: ev.kind,
      occurredAt: ev.timestamp,
      whenAgo: ev.when_ago,
      tone,
    });
  }

  // News headlines — limited to first few, decision-context only.
  for (const item of raw.news?.items?.slice(0, 4) ?? []) {
    const tone: ResearchEventItem["tone"] =
      item.sentiment_label === "negative"
        ? "warning"
        : item.sentiment_label === "positive"
          ? "info"
          : "muted";
    out.push({
      kind: "news",
      title: item.title,
      detail: item.source,
      source: "news",
      occurredAt: item.published,
      whenAgo: null,
      tone,
    });
  }

  return out.slice(0, 8);
}

function buildShadowResearch(raw: RawSources): ShadowResearchSummary {
  const rl = raw.ops?.rl ?? null;
  const ml = raw.ops?.ml_ops ?? null;

  if (!rl && !ml) {
    return {
      available: false,
      rlShadowOnly: true,
      mlShadowOnly: true,
      livePipelineInfluence: false,
      totalAgents: null,
      trainableAgents: null,
      latestBenchmarkStatus: null,
      latestTrainingStatus: null,
    };
  }

  let warning: string | undefined;
  if (rl?.live_pipeline_influence || ml?.any_model_influences_live_pipeline) {
    warning =
      "A shadow/research surface is reporting live pipeline influence. Verify before publishing.";
  }

  return {
    available: true,
    rlShadowOnly: rl ? Boolean(rl.is_shadow_only) : true,
    mlShadowOnly: ml ? Boolean(ml.ml_is_shadow_only) : true,
    livePipelineInfluence:
      Boolean(rl?.live_pipeline_influence) || Boolean(ml?.any_model_influences_live_pipeline),
    totalAgents: rl?.total_agents ?? null,
    trainableAgents: rl?.trainable_agents ?? null,
    latestBenchmarkStatus: rl?.latest_benchmark_status ?? null,
    latestTrainingStatus: rl?.latest_training_status ?? null,
    warning,
  };
}

function buildSectorTilts(raw: RawSources): SectorTiltRow[] {
  if (!raw.regime) return [];
  return raw.regime.sector_tilts.slice(0, 6).map((s) => ({
    sector: s.sector,
    tiltPct: s.tilt_pct,
  }));
}

function stateFromBool(ok: boolean | undefined | null): HomeSourceState {
  if (ok === undefined || ok === null) return "unavailable";
  return ok ? "ok" : "warning";
}

function buildSystemHealth(raw: RawSources, failures: SourceFailures): SystemHealthRow[] {
  const out: SystemHealthRow[] = [];
  const health = raw.overview?.data?.health;

  if (health) {
    out.push({ label: "Source freshness", state: stateFromBool(health.source_freshness_ok) });
    out.push({ label: "Model health", state: stateFromBool(health.model_health_ok) });
    out.push({ label: "Publication health", state: stateFromBool(health.publication_health_ok) });
    out.push({
      label: "Open incidents",
      state: (health.open_incidents ?? 0) === 0 ? "ok" : "warning",
      detail: (health.open_incidents ?? 0) === 0 ? "none" : `${health.open_incidents} open`,
    });
  } else {
    out.push({
      label: "Pipeline health",
      state: failures.overview ? "unavailable" : "unavailable",
      detail: failures.overview ?? "no health summary",
    });
  }

  const integrations = raw.ops?.integrations_summary;
  if (integrations) {
    const ok = integrations.degraded === 0 && integrations.placeholder === 0;
    out.push({
      label: "Integrations",
      state: ok ? "ok" : "warning",
      detail: `${integrations.healthy}/${integrations.total_integrations} healthy`,
    });
  }

  return out;
}

async function callOrFail<T>(
  label: string,
  fn: () => Promise<T>,
  failures: SourceFailures,
): Promise<T | undefined> {
  try {
    return await fn();
  } catch (err) {
    failures[label] = err instanceof Error ? err.message : String(err);
    return undefined;
  }
}

export interface LoadHomeDataArgs {
  userEmail: string | null | undefined;
}

export async function loadHomeData(args: LoadHomeDataArgs): Promise<HomeDataResult> {
  const failures: SourceFailures = {};

  const [
    overviewResp,
    recommendationResp,
    regimeResp,
    activityResp,
    opsResp,
    paperResp,
    riskResp,
    newsResp,
    comparisonResp,
    disagreementResp,
    evidenceResp,
  ] = await Promise.all([
    callOrFail("overview", fetchOverview, failures),
    callOrFail("recommendation", fetchCurrentRecommendation, failures),
    callOrFail("regime", fetchRegime, failures),
    callOrFail("activity", fetchActivity, failures),
    callOrFail("ops", fetchOps, failures),
    callOrFail("paper", fetchCurrentPaper, failures),
    callOrFail("risk", fetchCurrentRisk, failures),
    callOrFail("news", () => fetchNews(false), failures),
    callOrFail("comparison", fetchEngineComparison, failures),
    callOrFail("disagreement", fetchDisagreement, failures),
    callOrFail("evidence", fetchEvidence, failures),
  ]);

  const raw: RawSources = {
    overview: overviewResp
      ? {
          data: overviewResp.data,
          warnings: overviewResp.meta?.warnings ?? [],
          freshness: overviewResp.meta?.freshness ?? null,
        }
      : undefined,
    recommendation: recommendationResp?.data ?? null,
    regime: regimeResp?.data,
    activity: activityResp?.data,
    ops: opsResp?.data,
    paper: paperResp?.data ?? null,
    risk: riskResp?.data ?? null,
    news: newsResp?.data,
    comparison: comparisonResp?.data ?? null,
    disagreement: disagreementResp?.data ?? null,
    evidence: evidenceResp?.data ?? null,
  };

  const view: HomeViewModel = {
    greetingName: firstNameFromEmail(args.userEmail ?? null),
    generatedAt: safeIso(overviewResp?.meta?.generated_at) ?? new Date().toISOString(),
    sourceStatuses: buildSourceStatuses(raw, failures),
    governance: buildGovernance(raw),
    regime: buildRegime(raw),
    decisionQueue: buildDecisionQueue(raw),
    opportunities: buildOpportunities(raw),
    portfolio: buildPortfolio(raw),
    researchEvents: buildResearchEvents(raw),
    shadowResearch: buildShadowResearch(raw),
    sectorTilts: buildSectorTilts(raw),
    systemHealth: buildSystemHealth(raw, failures),
    pipelineWarnings: raw.overview?.warnings ?? [],
  };

  return { view, failures };
}
