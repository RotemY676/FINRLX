import { Icon } from "@/components/icons/Icon";

import { PanelShell, PanelUnavailable } from "./HomePanelStates";

import type { ShadowResearchSummary } from "./homeTypes";

interface Props {
  summary: ShadowResearchSummary;
}

/**
 * Shadow research snapshot — RL / ML pipeline state. Hard-wired safety copy
 * from backtest-hygiene-gate and recommendation-object-provenance: shadow-only,
 * no broker execution, no implied future performance.
 */
export function ShadowResearchSnapshot({ summary }: Props) {
  if (!summary.available) {
    return (
      <PanelShell
        icon="backtest"
        title="Shadow research"
        subtitle="Research-only. Not used for broker execution."
      >
        <PanelUnavailable
          message="No shadow research data."
          hint="RL/ML benchmark data is not currently exposed via /ops."
        />
      </PanelShell>
    );
  }

  return (
    <PanelShell
      icon="backtest"
      title="Shadow research"
      subtitle="Research-only · backtests are not future performance"
    >
      <div className="space-y-2 text-[12px]">
        <RowChip
          label="RL shadow-only"
          value={summary.rlShadowOnly}
        />
        <RowChip label="ML shadow-only" value={summary.mlShadowOnly} />
        <RowChip
          label="Live pipeline influence"
          value={!summary.livePipelineInfluence}
          okText="None"
          flagText="Detected"
        />
        {summary.totalAgents !== null && (
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-ink-2">Agents</span>
            <span className="text-ink font-mono text-[11.5px]">
              {summary.totalAgents}
              {summary.trainableAgents !== null && (
                <span className="text-ink-4"> · {summary.trainableAgents} trainable</span>
              )}
            </span>
          </div>
        )}
        {summary.latestBenchmarkStatus && (
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-ink-2">Latest benchmark</span>
            <span className="text-ink-3 text-[11.5px]">{summary.latestBenchmarkStatus}</span>
          </div>
        )}
        {summary.latestTrainingStatus && (
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-ink-2">Latest training</span>
            <span className="text-ink-3 text-[11.5px]">{summary.latestTrainingStatus}</span>
          </div>
        )}
      </div>
      {summary.warning && (
        <div className="mt-3 rounded-md border border-breach/30 bg-breach-soft p-2 text-[11.5px] text-breach-soft-ink flex items-start gap-1.5">
          <Icon name="alert-triangle" size={11} className="mt-0.5 shrink-0" />
          {summary.warning}
        </div>
      )}
      <p className="mt-3 text-[10.5px] text-ink-4 leading-snug">
        Shadow research outputs do not feed broker execution. Backtests are
        historical and do not predict future returns.
      </p>
    </PanelShell>
  );
}

function RowChip({
  label,
  value,
  okText = "Yes",
  flagText = "No",
}: {
  label: string;
  value: boolean;
  okText?: string;
  flagText?: string;
}) {
  return (
    <div className="flex items-center justify-between text-[12px]">
      <span className="text-ink-2">{label}</span>
      <span
        className={`inline-flex items-center gap-1.5 text-[11.5px] font-medium ${
          value ? "text-pos" : "text-breach"
        }`}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full ${value ? "bg-pos" : "bg-breach"}`}
          aria-hidden="true"
        />
        {value ? okText : flagText}
      </span>
    </div>
  );
}
