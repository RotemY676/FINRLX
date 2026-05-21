import Link from "next/link";

import { Icon } from "@/components/icons/Icon";
import { fmtDateTime } from "@/lib/format";

import { PanelEmpty, PanelShell } from "./HomePanelStates";

import type { PortfolioImpactSummary } from "./homeTypes";

interface Props {
  portfolio: PortfolioImpactSummary;
}

function pct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

export function PortfolioImpactCard({ portfolio }: Props) {
  if (!portfolio.hasPortfolio) {
    return (
      <PanelShell icon="paper" title="Paper portfolio" subtitle="Tracked in your base currency">
        <PanelEmpty
          message="No active paper portfolio yet."
          hint="Apply a template or open a paper portfolio from your profile."
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Link
            href="/templates"
            className="inline-flex items-center justify-center min-h-11 md:min-h-0 md:py-2 px-3 rounded-md bg-primary text-primary-ink text-[12px] font-medium"
          >
            Try a template
          </Link>
          <Link
            href="/profile"
            className="inline-flex items-center justify-center min-h-11 md:min-h-0 md:py-2 px-3 rounded-md border border-line text-[12px] font-medium text-ink-2"
          >
            Configure profile
          </Link>
        </div>
      </PanelShell>
    );
  }

  return (
    <PanelShell
      icon="paper"
      title="Paper portfolio"
      subtitle={portfolio.portfolioName ?? "Paper portfolio"}
      right={
        <Link
          href="/paper"
          className="inline-flex items-center text-[11.5px] text-primary hover:underline"
        >
          Open paper portfolio
          <Icon name="chevron-right" size={11} className="ml-0.5" />
        </Link>
      }
    >
      <div className="grid grid-cols-2 gap-3 text-[12px]">
        <div>
          <p className="text-[10.5px] text-ink-4 uppercase tracking-wide">Invested</p>
          <p className="text-[16px] font-display font-semibold text-ink">
            {pct(portfolio.invested)}
          </p>
        </div>
        <div>
          <p className="text-[10.5px] text-ink-4 uppercase tracking-wide">Cash</p>
          <p className="text-[16px] font-display font-semibold text-ink">
            {pct(portfolio.cash)}
          </p>
        </div>
      </div>
      {portfolio.topHoldings && portfolio.topHoldings.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <p className="text-[10.5px] text-ink-4 uppercase tracking-wide">Top holdings</p>
          {portfolio.topHoldings.map((h) => (
            <div
              key={h.ticker}
              className="flex items-center justify-between text-[12px]"
            >
              <span className="text-ink">{h.ticker}</span>
              <span className="text-ink-3 font-mono">
                {pct(h.weight)} · drift {pct(h.drift)}
              </span>
            </div>
          ))}
        </div>
      )}
      <div className="mt-3 pt-3 border-t border-line text-[11px] text-ink-4 flex items-center gap-1.5">
        <Icon name="clock" size={11} />
        {portfolio.lastRebalanceAt
          ? `Last rebalance · ${fmtDateTime(portfolio.lastRebalanceAt)}`
          : "No rebalance recorded yet"}
      </div>
      {portfolio.riskWarning && (
        <div className="mt-2 rounded-md bg-caution-soft text-caution-soft-ink p-2 text-[11.5px] flex items-start gap-1.5">
          <Icon name="alert-triangle" size={12} className="mt-0.5 shrink-0" />
          {portfolio.riskWarning}
        </div>
      )}
    </PanelShell>
  );
}
