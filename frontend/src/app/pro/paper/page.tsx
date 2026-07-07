"use client";

import { useEffect, useState } from "react";
import { fetchCurrentPaper, fetchPaperPerformance, PaperPortfolioData, PaperPerformanceSummary } from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { fmtDateTime, fmtDate } from "@/lib/format";
import { DriftBarChart } from "@/components/charts/DriftBarChart";
import { usePaneContext } from "@/components/shell/ContextPane";
import { SourceBadge } from "@/components/recommendation/SourceBadge";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";
import { track } from "@/lib/analytics";
import { useAuth } from "@/contexts/AuthContext";
import CurrencyValuation from "@/features/wizard/CurrencyValuation";

function driftColor(d: number): string {
  if (Math.abs(d) > 0.01) return d > 0 ? "text-pos" : "text-breach";
  return "text-ink-2";
}

export default function PaperPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [data, setData] = useState<PaperPortfolioData | null>(null);
  const [perf, setPerf] = useState<PaperPerformanceSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { openPane } = usePaneContext();

  useEffect(() => {
    // Phase 19A.3: don't fire the authenticated fetch when the visitor has
    // no session — it just produces a console 401 and an unhelpful error UI.
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    void track("paper_trade", { view: "portfolio_summary" });
    fetchCurrentPaper()
      .then(async (res) => {
        setData(res.data);
        if (res.data?.id) {
          try {
            const perfRes = await fetchPaperPerformance(res.data.id);
            if (perfRes.data?.status === "computed") setPerf(perfRes.data);
          } catch { /* performance not available yet */ }
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [authLoading, user]);

  if (authLoading || loading) return <PageLoading label="Loading paper portfolio..." />;
  if (!user) return <PageEmpty title="Sign in required" message="Sign in to view your paper portfolio." />;
  if (error) return <PageError title="Paper Portfolio Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!data) return <PageEmpty title="No Paper Portfolio" message="No active paper portfolio found. Run the seed script to create one." />;

  const maxDrift = Math.max(...data.holdings.map((h) => Math.abs(h.drift)));

  return (
    <div className="space-y-gap max-w-[1200px]">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-page-title text-ink">Paper Portfolio</h1>
          <p className="text-body-sm text-ink-2 mt-1">{data.name}</p>
          {data.source_recommendation_id && (
            <p className="text-meta text-ink-4 font-mono mt-0.5">
              Source: {data.source_recommendation_id.slice(0, 8)}…
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={data.is_active ? "published" : "stale"} />
          {data.source_type && <SourceBadge source={data.source_type} />}
        </div>
      </div>

      {/* Test paper warning */}
      {data.source_type === "test_paper" && (
        <div className="rounded-lg border border-caution bg-caution-soft p-3 text-caption text-caution-soft-ink">
          This is a test paper portfolio created from an unpublished recommendation (allow_unpublished=true). Treat as experimental.
        </div>
      )}
      {data.is_demo && (
        <div className="rounded-lg border border-caution bg-caution-soft p-3 text-caption text-caution-soft-ink">
          This portfolio is from seeded/demo data and may not reflect real market conditions.
        </div>
      )}

      {/* Phase FX-3 — base-currency valuation card */}
      <CurrencyValuation />

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-gap">
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
          <p className="text-[11px] text-ink-3">Invested</p>
          <p className="text-[15px] font-semibold text-ink font-mono">{(data.invested_weight * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
          <p className="text-[11px] text-ink-3">Cash</p>
          <p className="text-[15px] font-semibold text-ink font-mono">{(data.cash_weight * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
          <p className="text-[11px] text-ink-3">Rebalances</p>
          <p className="text-[15px] font-semibold text-ink font-mono">{data.total_rebalances}</p>
          {data.last_rebalance_at && (
            <p className="text-[11px] text-ink-4 mt-1">
              Last: {fmtDate(data.last_rebalance_at)}
            </p>
          )}
        </div>
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
          <p className="text-[11px] text-ink-3">Max Drift</p>
          <p className={`text-[15px] font-semibold font-mono ${maxDrift > 0.01 ? "text-caution" : "text-pos"}`}>
            {(maxDrift * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Performance summary */}
      {perf && (
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
          <h3 className="text-[13px] font-semibold text-ink mb-3">Performance Summary</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { k: "Total Return", v: perf.total_return != null ? `${(perf.total_return * 100).toFixed(1)}%` : "—" },
              { k: "Sharpe", v: perf.sharpe_ratio?.toFixed(2) ?? "—" },
              { k: "Max Drawdown", v: perf.max_drawdown != null ? `${(perf.max_drawdown * 100).toFixed(1)}%` : "—" },
              { k: "Volatility", v: perf.volatility != null ? `${(perf.volatility * 100).toFixed(1)}%` : "—" },
              { k: "Trades", v: String(perf.trade_count ?? "—") },
              { k: "Days", v: String(perf.days ?? "—") },
            ].map((m) => (
              <div key={m.k} className="text-center">
                <p className="text-[11px] text-ink-4">{m.k}</p>
                <p className="text-[14px] font-semibold text-ink font-mono mt-0.5">{m.v}</p>
              </div>
            ))}
          </div>
          {perf.warnings.length > 0 && (
            <div className="mt-3 pt-3 border-t border-line space-y-1">
              {perf.warnings.map((w, i) => (
                <p key={i} className="text-[11px] text-caution">{w}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Portfolio value */}
      {data.portfolio_value != null && (
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad flex items-center justify-between">
          <span className="text-[13px] text-ink-3">Portfolio Value</span>
          <span className="text-[18px] font-display font-semibold text-ink font-mono">${data.portfolio_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
        </div>
      )}

      {/* Drift chart */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <h3 className="text-[13px] font-semibold text-ink mb-4">Drift from Target</h3>
        <DriftBarChart holdings={data.holdings} />
      </div>

      {/* Holdings table */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <div className="flex items-baseline justify-between mb-3 gap-2">
          <h3 className="text-[13px] font-semibold text-ink">Holdings</h3>
          <span className="text-[11px] text-ink-4">Tap a row to inspect</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-line text-[11px] text-ink-3">
                <th className="text-left py-2 pr-3">Ticker</th>
                <th className="hidden md:table-cell text-left py-2 pr-3">Name</th>
                <th className="hidden md:table-cell text-right py-2 pr-3">Target</th>
                <th className="hidden md:table-cell text-right py-2 pr-3">Current</th>
                <th className="text-right py-2">Drift</th>
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((h) => {
                const openDetail = () =>
                  openPane(`${h.ticker} Paper Detail`, (
                    <div className="space-y-4">
                      <div>
                        <p className="text-[11px] text-ink-3">Asset</p>
                        <p className="text-[13px] font-medium">{h.name} ({h.ticker})</p>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-[11px] text-ink-3">Target Weight</p>
                          <p className="text-[15px] font-semibold text-ink font-mono">{(h.target_weight * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                          <p className="text-[11px] text-ink-3">Current Weight</p>
                          <p className="text-[15px] font-semibold text-ink font-mono">{(h.current_weight * 100).toFixed(1)}%</p>
                        </div>
                      </div>
                      <div>
                        <p className="text-[11px] text-ink-3">Drift</p>
                        <p className={`text-[15px] font-semibold font-mono ${driftColor(h.drift)}`}>
                          {h.drift > 0 ? "+" : ""}{(h.drift * 100).toFixed(1)}%
                        </p>
                        {Math.abs(h.drift) > 0.01 && (
                          <p className="text-[11px] text-caution mt-1">
                            Exceeds 1% drift threshold
                          </p>
                        )}
                      </div>
                    </div>
                  ));
                return (
                  <tr
                    key={h.asset_id}
                    role="button"
                    tabIndex={0}
                    aria-label={`${h.ticker} — open paper detail`}
                    className="border-b border-line/50 hover:bg-surface-3 focus-visible:bg-surface-3 cursor-pointer transition-colors"
                    onClick={openDetail}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openDetail();
                      }
                    }}
                  >
                    <td className="py-3 md:py-2 pr-3 font-mono font-medium text-ink">
                      {h.ticker}
                      {/* Mobile: inline name + target/current since their columns hide below md. */}
                      <div className="md:hidden text-[11px] text-ink-3 mt-0.5 font-sans font-normal">
                        {h.name}
                      </div>
                      <div className="md:hidden text-[11px] text-ink-4 mt-0.5 font-sans font-normal">
                        Target {(h.target_weight * 100).toFixed(1)}% · Current {(h.current_weight * 100).toFixed(1)}%
                      </div>
                    </td>
                    <td className="hidden md:table-cell py-2 pr-3 text-ink-2">{h.name}</td>
                    <td className="hidden md:table-cell py-2 pr-3 text-right font-mono">{(h.target_weight * 100).toFixed(1)}%</td>
                    <td className="hidden md:table-cell py-2 pr-3 text-right font-mono">{(h.current_weight * 100).toFixed(1)}%</td>
                    <td className={`py-3 md:py-2 text-right font-mono ${driftColor(h.drift)}`}>
                      {h.drift > 0 ? "+" : ""}{(h.drift * 100).toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warnings */}
      {data.warnings.length > 0 && <WarningsBlock warnings={data.warnings} />}

      {/* Event log */}
      {data.events.length > 0 && (
        <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
          <h3 className="text-[13px] font-semibold text-ink mb-3">Event Log</h3>
          <div className="space-y-2">
            {data.events.map((ev, i) => (
              <div key={i} className="flex items-start gap-3 text-[13px]">
                <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium shrink-0 ${
                  ev.event_type === "rebalance" ? "bg-primary-soft text-primary" :
                  ev.event_type === "drift_alert" ? "bg-caution-soft text-caution" :
                  "bg-line text-ink-2"
                }`}>
                  {ev.event_type.replace(/_/g, " ")}
                </span>
                <div className="flex-1">
                  <p className="text-ink-2">{ev.description}</p>
                  <p className="text-[11px] text-ink-4">
                    {fmtDateTime(ev.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
