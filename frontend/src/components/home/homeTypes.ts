/**
 * Type contract for the FINRLX Home / Decision Command Center.
 *
 * These types are deliberately decision-oriented, not market-oriented: the
 * home page answers "what needs review, what evidence supports it, what is
 * stale/shadow-only/blocked" rather than "what is the market doing right now."
 */

export type HomeSourceState = "ok" | "stale" | "warning" | "unavailable";

export interface HomeSourceStatus {
  source: string;
  status: HomeSourceState;
  label: string;
  asOf?: string | null;
  warning?: string | null;
}

export type HomeDecisionSeverity = "info" | "warning" | "critical";
export type HomeDecisionAction =
  | "review-evidence"
  | "open-decision"
  | "compare-engines"
  | "view-risk"
  | "monitor"
  | "open-ops"
  | "defer";

export interface HomeDecisionItem {
  id: string;
  ticker: string | null;
  title: string;
  reason: string;
  severity: HomeDecisionSeverity;
  decisionState: string;
  evidenceCount: number;
  lastUpdated: string | null;
  nextAction: HomeDecisionAction;
  actionLabel: string;
  href: string;
  source: string;
}

export type OpportunitySignalLabel =
  | "bullish"
  | "neutral"
  | "bearish"
  | "conflicted"
  | "unknown";
export type OpportunityRiskLevel =
  | "low"
  | "medium"
  | "high"
  | "blocked"
  | "unknown";

export interface OpportunityRadarRow {
  ticker: string;
  companyName?: string | null;
  trigger: string;
  compositeSignal?: number | null;
  signalLabel: OpportunitySignalLabel;
  riskLevel: OpportunityRiskLevel;
  dataFreshness?: string | null;
  evidenceSources: string[];
  recommendationState: string;
  href: string;
}

export interface GovernanceStatus {
  researchOnly: true;
  noBrokerExecution: true;
  rlShadowOnly: boolean;
  mlShadowOnly: boolean;
  livePipelineInfluence: boolean;
  dataFreshnessWarning: boolean;
  lastPipelineRun?: string | null;
  warnings: string[];
}

export type RegimeStatus = {
  label: string | null;
  confidence: number | null;
  persistenceDays: number | null;
  asOf: string | null;
};

export interface PortfolioImpactSummary {
  hasPortfolio: boolean;
  portfolioName?: string | null;
  invested?: number | null;
  cash?: number | null;
  totalRebalances?: number | null;
  lastRebalanceAt?: string | null;
  topHoldings?: Array<{ ticker: string; weight: number; drift: number }>;
  riskWarning?: string | null;
}

export interface ResearchEventItem {
  kind: "audit" | "incident" | "news";
  title: string;
  detail?: string | null;
  source: string;
  occurredAt: string | null;
  whenAgo?: string | null;
  tone: "info" | "warning" | "critical" | "muted";
}

export interface ShadowResearchSummary {
  available: boolean;
  rlShadowOnly: boolean;
  mlShadowOnly: boolean;
  livePipelineInfluence: boolean;
  totalAgents: number | null;
  trainableAgents: number | null;
  latestBenchmarkStatus: string | null;
  latestTrainingStatus: string | null;
  warning?: string | null;
}

export interface SectorTiltRow {
  sector: string;
  tiltPct: number;
}

export interface SystemHealthRow {
  label: string;
  state: HomeSourceState;
  detail?: string | null;
}

export interface HomeViewModel {
  greetingName: string;
  generatedAt: string;
  sourceStatuses: HomeSourceStatus[];
  governance: GovernanceStatus;
  regime: RegimeStatus | null;
  decisionQueue: HomeDecisionItem[];
  opportunities: OpportunityRadarRow[];
  portfolio: PortfolioImpactSummary;
  researchEvents: ResearchEventItem[];
  shadowResearch: ShadowResearchSummary;
  sectorTilts: SectorTiltRow[];
  systemHealth: SystemHealthRow[];
  pipelineWarnings: string[];
}
