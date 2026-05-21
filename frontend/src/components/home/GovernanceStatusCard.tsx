import { Icon } from "@/components/icons/Icon";
import { fmtDateTime } from "@/lib/format";

import { PanelShell } from "./HomePanelStates";

import type { GovernanceStatus } from "./homeTypes";

interface Props {
  governance: GovernanceStatus;
}

/**
 * Governance card — always visible, always honest. Encodes the
 * fintech-disclaimer-and-marketing-guard contract directly on the home page:
 * research-only, no broker execution, RL/ML shadow-only when applicable, and
 * a loud warning if any model reports live pipeline influence.
 */
export function GovernanceStatusCard({ governance }: Props) {
  const items: Array<{ label: string; value: string; tone: "pos" | "caution" | "breach" }> = [
    { label: "Research only", value: "Yes", tone: "pos" },
    { label: "No broker execution", value: "Yes", tone: "pos" },
    {
      label: "RL shadow only",
      value: governance.rlShadowOnly ? "Yes" : "No",
      tone: governance.rlShadowOnly ? "pos" : "breach",
    },
    {
      label: "ML shadow only",
      value: governance.mlShadowOnly ? "Yes" : "No",
      tone: governance.mlShadowOnly ? "pos" : "breach",
    },
    {
      label: "Live pipeline influence",
      value: governance.livePipelineInfluence ? "Detected" : "None",
      tone: governance.livePipelineInfluence ? "breach" : "pos",
    },
    {
      label: "Data freshness",
      value: governance.dataFreshnessWarning ? "Warning" : "OK",
      tone: governance.dataFreshnessWarning ? "caution" : "pos",
    },
  ];

  return (
    <PanelShell
      icon="check"
      title="Governance"
      subtitle="Decision-support tool. Not investment advice."
    >
      <div
        data-governance="true"
        className="space-y-1.5"
        aria-label="Governance status"
      >
        {items.map((it) => (
          <div
            key={it.label}
            className="flex items-center justify-between gap-2 text-[12.5px]"
          >
            <span className="text-ink-2">{it.label}</span>
            <span
              className={`inline-flex items-center gap-1.5 text-[12px] font-medium ${
                it.tone === "pos"
                  ? "text-pos"
                  : it.tone === "caution"
                    ? "text-caution"
                    : "text-breach"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  it.tone === "pos"
                    ? "bg-pos"
                    : it.tone === "caution"
                      ? "bg-caution"
                      : "bg-breach"
                }`}
                aria-hidden="true"
              />
              {it.value}
            </span>
          </div>
        ))}
        {governance.lastPipelineRun && (
          <div className="mt-2 pt-2 border-t border-line text-[11px] text-ink-4 flex items-center gap-1.5">
            <Icon name="clock" size={11} />
            Last pipeline run · {fmtDateTime(governance.lastPipelineRun)}
          </div>
        )}
        {governance.warnings.length > 0 && (
          <div className="mt-2 rounded-md border border-breach/30 bg-breach-soft p-2.5">
            {governance.warnings.map((w, i) => (
              <p
                key={i}
                className="text-[11.5px] text-breach-soft-ink flex items-start gap-1.5"
              >
                <Icon name="alert-triangle" size={11} className="mt-0.5 shrink-0" />
                {w}
              </p>
            ))}
          </div>
        )}
        <p className="mt-3 text-[10.5px] text-ink-4 leading-snug">
          FINRLX produces decision-support output from historical data. It does
          not place orders, connect to brokers, or guarantee outcomes.
        </p>
      </div>
    </PanelShell>
  );
}
