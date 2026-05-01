export const STANCE_STYLE: Record<string, string> = {
  LONG: "text-pos-soft-ink bg-pos-soft", SHORT: "text-breach-soft-ink bg-breach-soft",
  TRIM: "text-caution-soft-ink bg-caution-soft", HOLD: "text-ink-3 bg-surface-3",
};
export const PRIORITY_STYLE: Record<string, string> = {
  high: "text-breach", mid: "text-caution", low: "text-ink-3",
};
export const FEED_STATUS: Record<string, string> = {
  ok: "bg-pos", degraded: "bg-caution", stale: "bg-breach",
};
export const SEVERITY_STYLE: Record<string, string> = {
  "sev-1": "text-breach font-semibold", "sev-2": "text-caution font-semibold",
  "sev-3": "text-ink-2", "sev-4": "text-ink-3",
};
export const KPI_TONE: Record<string, string> = {
  pos: "text-pos", caution: "text-caution", breach: "text-breach", neutral: "text-ink",
};
export const QUEUE_FILTERS = [
  { key: "all", label: "All" },
  { key: "high", label: "High priority" },
];
export const AUDIT_SCOPES = [
  { key: "all", label: "All" },
  { key: "recommendation", label: "Queue" },
  { key: "breach", label: "Policy" },
  { key: "engine", label: "Engine" },
  { key: "incident", label: "Ops" },
];

export const PIPELINE_STEPS = [
  { key: "research-data", label: "Research Data", icon: "sparkle" as const, description: "Export shadow datasets for local offline research. The system scans your asset universe, extracts features, targets and signals, then packages them into a governed dataset for analysis." },
  { key: "experiments", label: "Experiments", icon: "sparkle" as const, description: "Track offline research experiments linked to governed dataset exports. Define hypotheses, configure parameters, run local analysis, and import result metadata." },
  { key: "comparisons", label: "Comparisons", icon: "compare" as const, description: "Compare experiments side-by-side using imported metrics. The system ranks experiments by Sharpe ratio, drawdown, return, and other metrics to identify the strongest research candidates." },
  { key: "readiness", label: "Readiness", icon: "shield" as const, description: "Final readiness assessment before deeper review. The system runs evidence checks across metric coverage, safety flags, warnings, and limitations to determine research completeness." },
  { key: "safety", label: "Safety / Ops", icon: "risk" as const, description: "System health monitoring, publication queue management, benchmark forensics, incident tracking, and audit trail. The operational command center for your research platform." },
] as const;

export type PipelineStepKey = typeof PIPELINE_STEPS[number]["key"];
