"use client";

import { useEffect, useState } from "react";

import { fetchCurrentRisk, RiskBundle } from "@/services/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { useAuth } from "@/contexts/AuthContext";
import { SignInRequired } from "@/components/feedback/SignInRequired";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";
import { HelpLink } from "@/components/help/HelpLink";

function pct(v: number, digits = 1): string {
  return `${(v * 100).toFixed(digits)}%`;
}

function signedPct(v: number, digits = 1): string {
  const s = pct(v, digits);
  return v > 0 ? `+${s}` : s;
}

export default function RiskPage() {
  const { flags, isLoading: flagsLoading } = useFeatureFlags();
  const { user, isLoading: authLoading } = useAuth();
  const [data, setData] = useState<RiskBundle | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (flagsLoading || authLoading || !flags.risk_ui) return;
    if (!user) return;
    fetchCurrentRisk()
      .then((res) => setData(res.data))
      .catch((e) => setError(e.message));
  }, [flagsLoading, flags.risk_ui, authLoading, user]);

  if (flagsLoading || authLoading) return <PageLoading label="Loading risk..." />;
  if (!user) return <SignInRequired feature="the risk workspace" />;
  if (data === undefined) return <PageLoading label="Loading risk..." />;
  if (!flags.risk_ui) {
    return (
      <PageError
        title="Surface not enabled"
        message="The Risk workspace is not enabled for this environment."
        hint="Set FEATURE_RISK_UI=true in the backend environment."
      />
    );
  }
  if (error) return <PageError title="Risk Error" message={error} hint="Ensure the backend is running." />;
  if (data === null) {
    return (
      <PageEmpty
        title="No paper portfolio"
        message="Risk metrics need an active paper portfolio with valuation history. Promote a recommendation to paper to bootstrap the data."
        action={{ label: "Open Paper portfolio", href: "/pro/paper" }}
      />
    );
  }

  const r = data;
  const concentrationCaution = r.concentration.top5_weight > 0.6;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div>
        <h1 className="text-page-title text-ink flex items-center gap-2">
          Risk workspace
          <HelpLink anchor="reference/pages/risk" label="Open Risk help" />
        </h1>
        <p className="text-body-sm text-ink-2 mt-0.5">
          {r.portfolio_name} · {r.snapshot_count} daily snapshots
        </p>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-gap">
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <p className="text-[11px] text-ink-4">VaR 95% (daily)</p>
          <p className="text-[20px] font-display font-semibold text-ink mt-0.5">
            {pct(r.var.var_95, 2)}
          </p>
          <p className="text-[11px] text-ink-4 mt-0.5">{r.var.sample_size} returns</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <p className="text-[11px] text-ink-4">VaR 99% (daily)</p>
          <p className="text-[20px] font-display font-semibold text-ink mt-0.5">
            {pct(r.var.var_99, 2)}
          </p>
          <p className="text-[11px] text-ink-4 mt-0.5">parametric, normal</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <p className="text-[11px] text-ink-4">Current drawdown</p>
          <p className={`text-[20px] font-display font-semibold mt-0.5 ${r.drawdown.current_drawdown < -0.05 ? "text-caution" : "text-ink"}`}>
            {signedPct(r.drawdown.current_drawdown)}
          </p>
          <p className="text-[11px] text-ink-4 mt-0.5">peak {r.drawdown.peak_value?.toFixed(0) ?? "—"}</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <p className="text-[11px] text-ink-4">Max drawdown</p>
          <p className={`text-[20px] font-display font-semibold mt-0.5 ${r.drawdown.max_drawdown < -0.1 ? "text-breach" : "text-caution"}`}>
            {signedPct(r.drawdown.max_drawdown)}
          </p>
          <p className="text-[11px] text-ink-4 mt-0.5">since inception</p>
        </div>
      </div>

      {/* Exposure */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h2 className="text-[13px] font-semibold text-ink mb-3 flex items-center gap-2">Exposure <HelpLink anchor="reference/policy-controls#exposure_single" label="What are exposure caps?" /></h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-gap text-[12.5px]">
          <div><p className="text-[11px] text-ink-4">Long</p><p className="text-ink font-mono mt-0.5">{pct(r.exposure.long_weight)}</p></div>
          <div><p className="text-[11px] text-ink-4">Short</p><p className="text-ink font-mono mt-0.5">{pct(r.exposure.short_weight)}</p></div>
          <div><p className="text-[11px] text-ink-4">Gross</p><p className="text-ink font-mono mt-0.5">{pct(r.exposure.gross_exposure)}</p></div>
          <div><p className="text-[11px] text-ink-4">Net</p><p className="text-ink font-mono mt-0.5">{pct(r.exposure.net_exposure)}</p></div>
          <div><p className="text-[11px] text-ink-4">Cash</p><p className="text-ink font-mono mt-0.5">{pct(r.exposure.cash_weight)}</p></div>
        </div>
      </section>

      {/* Concentration */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-baseline justify-between gap-2 mb-3">
          <h2 className="text-[13px] font-semibold text-ink">Concentration</h2>
          <span className="text-[11px] text-ink-4">{r.concentration.total_positions} positions</span>
        </div>
        <div className="grid grid-cols-3 gap-gap mb-4 text-[12.5px]">
          <div><p className="text-[11px] text-ink-4">Top 1</p><p className="text-ink font-mono mt-0.5">{pct(r.concentration.top1_weight)}</p></div>
          <div><p className="text-[11px] text-ink-4">Top 3</p><p className="text-ink font-mono mt-0.5">{pct(r.concentration.top3_weight)}</p></div>
          <div>
            <p className="text-[11px] text-ink-4">Top 5</p>
            <p className={`font-mono mt-0.5 ${concentrationCaution ? "text-caution" : "text-ink"}`}>
              {pct(r.concentration.top5_weight)}
            </p>
          </div>
        </div>
        <div>
          <p className="text-[11px] text-ink-4 mb-2">Sector breakdown</p>
          {r.concentration.sectors.length === 0 ? (
            <p className="text-[12.5px] text-ink-3">No sector data.</p>
          ) : (
            <ul className="space-y-1.5" role="list">
              {r.concentration.sectors.map((s) => (
                <li key={s.sector} className="flex items-center gap-3 text-[12px]">
                  <span className="text-ink-2 w-32 md:w-40 truncate">{s.sector}</span>
                  <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${Math.min(100, s.weight * 100)}%` }}
                    />
                  </div>
                  <span className="font-mono text-[11px] text-ink-3 w-12 text-right shrink-0">
                    {pct(s.weight)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <p className="text-[11px] text-ink-4">
        Volatility (daily, sample stddev): <span className="font-mono">{pct(r.var.volatility_daily, 2)}</span>.
        VaR uses parametric normal assumption (1.6449·σ for 95%, 2.3263·σ for 99%).
      </p>
    </div>
  );
}
