import Link from "next/link";

import { Icon } from "@/components/icons/Icon";
import { fmtDateTime } from "@/lib/format";

import { PanelEmpty, PanelShell, PanelUnavailable } from "./HomePanelStates";

import type {
  OpportunityRadarRow,
  OpportunityRiskLevel,
  OpportunitySignalLabel,
} from "./homeTypes";

interface Props {
  rows: OpportunityRadarRow[];
  isUnavailable?: boolean;
  unavailableMessage?: string;
  /**
   * Honest source label. The home page does not run a market-wide scanner.
   * Rows come from the current recommendation's top-conviction weights joined
   * with engine dispersion and evidence freshness.
   */
  sourceLabel?: string;
}

const SIGNAL_TONE: Record<OpportunitySignalLabel, { ink: string; bg: string; dot: string }> = {
  bullish: { ink: "text-pos-soft-ink", bg: "bg-pos-soft", dot: "bg-pos" },
  bearish: { ink: "text-breach-soft-ink", bg: "bg-breach-soft", dot: "bg-breach" },
  conflicted: { ink: "text-caution-soft-ink", bg: "bg-caution-soft", dot: "bg-caution" },
  neutral: { ink: "text-ink-2", bg: "bg-surface-3", dot: "bg-ink-4" },
  unknown: { ink: "text-ink-3", bg: "bg-surface-3", dot: "bg-ink-4" },
};

const RISK_TONE: Record<OpportunityRiskLevel, { ink: string; dot: string }> = {
  low: { ink: "text-pos", dot: "bg-pos" },
  medium: { ink: "text-caution", dot: "bg-caution" },
  high: { ink: "text-breach", dot: "bg-breach" },
  blocked: { ink: "text-breach", dot: "bg-breach" },
  unknown: { ink: "text-ink-3", dot: "bg-ink-4" },
};

/**
 * Opportunity Radar. Renders a desktop table at md+ and stacked cards at
 * sub-md. Source data is the current recommendation's top conviction weights
 * — this is honest about not being a market-wide scanner.
 */
export function OpportunityRadarTable({
  rows,
  isUnavailable,
  unavailableMessage,
  sourceLabel,
}: Props) {
  return (
    <PanelShell
      icon="compare"
      title="Opportunity radar"
      subtitle={
        sourceLabel ?? "Top-conviction picks from the current recommendation"
      }
      right={
        <span className="text-[11px] text-ink-3 font-mono">{rows.length} rows</span>
      }
    >
      {isUnavailable ? (
        <PanelUnavailable
          message="Opportunity radar unavailable."
          hint={
            unavailableMessage ?? "No current recommendation or engine data."
          }
        />
      ) : rows.length === 0 ? (
        <PanelEmpty
          message="No active conviction signals."
          hint="When a recommendation publishes, top-conviction picks appear here."
        />
      ) : (
        <>
          {/* Desktop / tablet table */}
          <div className="hidden md:block overflow-x-auto" data-testid="radar-table">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="text-left text-[10.5px] uppercase tracking-wide text-ink-4">
                  <th className="py-2 pr-3 font-semibold">Ticker</th>
                  <th className="py-2 pr-3 font-semibold">Trigger</th>
                  <th className="py-2 pr-3 font-semibold">Signal</th>
                  <th className="py-2 pr-3 font-semibold">Risk</th>
                  <th className="py-2 pr-3 font-semibold">Evidence</th>
                  <th className="py-2 pr-3 font-semibold">Freshness</th>
                  <th className="py-2 pr-3 font-semibold">State</th>
                  <th className="py-2 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <DesktopRow key={`${row.ticker}-${idx}`} row={row} />
                ))}
              </tbody>
            </table>
          </div>
          {/* Mobile cards */}
          <div className="md:hidden space-y-2" data-testid="radar-cards">
            {rows.map((row, idx) => (
              <MobileCard key={`m-${row.ticker}-${idx}`} row={row} />
            ))}
          </div>
        </>
      )}
    </PanelShell>
  );
}

function SignalChip({ signal }: { signal: OpportunitySignalLabel }) {
  const tone = SIGNAL_TONE[signal];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded ${tone.bg} ${tone.ink} px-1.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} aria-hidden="true" />
      {signal}
    </span>
  );
}

function RiskChip({ risk }: { risk: OpportunityRiskLevel }) {
  const tone = RISK_TONE[risk];
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${tone.ink}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${tone.dot}`} aria-hidden="true" />
      {risk}
    </span>
  );
}

function DesktopRow({ row }: { row: OpportunityRadarRow }) {
  return (
    <tr className="border-t border-line">
      <td className="py-2 pr-3">
        <div className="flex flex-col">
          <span className="font-semibold text-ink">{row.ticker}</span>
          {row.companyName && (
            <span className="text-[10.5px] text-ink-4">{row.companyName}</span>
          )}
        </div>
      </td>
      <td className="py-2 pr-3 text-ink-2 max-w-[280px]">
        <span className="line-clamp-2">{row.trigger}</span>
      </td>
      <td className="py-2 pr-3">
        <SignalChip signal={row.signalLabel} />
      </td>
      <td className="py-2 pr-3">
        <RiskChip risk={row.riskLevel} />
      </td>
      <td className="py-2 pr-3 text-ink-3 text-[11px]">
        {row.evidenceSources.length > 0 ? row.evidenceSources.join(" · ") : "—"}
      </td>
      <td className="py-2 pr-3 text-ink-3 text-[11px]">
        {row.dataFreshness ? fmtDateTime(row.dataFreshness) : "unavailable"}
      </td>
      <td className="py-2 pr-3 text-ink-3 text-[11px] uppercase tracking-wide">
        {row.recommendationState}
      </td>
      <td className="py-2">
        <Link
          href={row.href}
          className="inline-flex items-center text-[12px] text-primary hover:underline"
        >
          Review evidence
          <Icon name="chevron-right" size={12} className="ml-0.5" />
        </Link>
      </td>
    </tr>
  );
}

function MobileCard({ row }: { row: OpportunityRadarRow }) {
  return (
    <div className="rounded-md border border-line bg-surface-2 p-3">
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div>
          <div className="font-semibold text-ink text-[13.5px]">{row.ticker}</div>
          {row.companyName && (
            <div className="text-[10.5px] text-ink-4">{row.companyName}</div>
          )}
        </div>
        <span className="text-[10px] uppercase tracking-wide text-ink-4">
          {row.recommendationState}
        </span>
      </div>
      <p className="text-[12px] text-ink-2 mb-2 leading-snug line-clamp-3">
        {row.trigger}
      </p>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <SignalChip signal={row.signalLabel} />
        <RiskChip risk={row.riskLevel} />
        {row.evidenceSources.map((src) => (
          <span
            key={src}
            className="rounded bg-surface-3 text-ink-3 px-1.5 py-0.5 text-[10px] font-medium"
          >
            {src}
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between text-[10.5px] text-ink-4">
        <span>
          freshness ·{" "}
          {row.dataFreshness ? fmtDateTime(row.dataFreshness) : "unavailable"}
        </span>
        <Link
          href={row.href}
          className="inline-flex items-center min-h-11 md:min-h-0 px-2 text-primary text-[12px] font-medium"
        >
          Review evidence
          <Icon name="chevron-right" size={12} className="ml-0.5" />
        </Link>
      </div>
    </div>
  );
}
