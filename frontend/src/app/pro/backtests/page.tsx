"use client";

import { useEffect, useState } from "react";
import {
  fetchBacktestList, fetchBacktest,
  BacktestListData, BacktestDetail,
  BacktestResultSummary, BenchmarkMetricBlock,
} from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { fmtDate } from "@/lib/format";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";
import { SignInRequired } from "@/components/feedback/SignInRequired";
import { HelpLink } from "@/components/help/HelpLink";
import { useAuth } from "@/contexts/AuthContext";

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
      <p className="text-[11px] text-ink-3">{label}</p>
      <p className="text-[15px] font-semibold text-ink font-mono mt-1">{value}</p>
      {sub && <p className="text-[11px] text-ink-4 mt-1">{sub}</p>}
    </div>
  );
}

function pct(v: number | null): string {
  return v != null ? `${(v * 100).toFixed(1)}%` : "—";
}

export default function BacktestsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [list, setList] = useState<BacktestListData | null>(null);
  const [detail, setDetail] = useState<BacktestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Don't fire the authed fetch for a logged-out visitor — it only 401s and
    // shows a false "error". Render the sign-in prompt instead (see below).
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    fetchBacktestList()
      .then(async (res) => {
        setList(res.data);
        if (res.data.items.length > 0) {
          const detailRes = await fetchBacktest(res.data.items[0].id);
          setDetail(detailRes.data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [authLoading, user]);

  if (authLoading || loading) return <PageLoading label="Loading backtests..." />;
  if (!user) return <SignInRequired feature="backtests" />;
  if (error) return <PageError title="Backtest Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!list || list.total === 0) return <PageEmpty title="No Backtests" message="No backtest experiments available. Run the seed script to create demo data." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-ink flex items-center gap-2">
            Backtests
            <HelpLink anchor="reference/pages/backtests" label="Open Backtests help" />
          </h1>
          <p className="text-[11px] text-ink-4 mt-1">
            {list.total} experiment{list.total !== 1 ? "s" : ""}
          </p>
        </div>
        <HelpLink
          anchor="guides/run-a-backtest"
          label="How to run a backtest"
          variant="inline"
        />
      </div>

      {/* Experiment list */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <h3 className="text-[13px] font-semibold text-ink mb-3">Experiments</h3>
        <ul className="space-y-1" role="list">
          {list.items.map((item) => {
            const isSelected = detail?.id === item.id;
            const onSelect = async () => {
              const res = await fetchBacktest(item.id);
              setDetail(res.data);
            };
            return (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={onSelect}
                  aria-pressed={isSelected}
                  aria-label={`${item.name} — open backtest detail`}
                  className={`w-full flex flex-col md:flex-row md:items-center md:justify-between gap-1.5 md:gap-3 p-3 min-h-11 rounded-lg text-left transition-colors ${
                    isSelected
                      ? "bg-surface border-2 border-primary"
                      : "border-2 border-transparent hover:bg-surface-3 focus-visible:bg-surface-3"
                  }`}
                >
                  <div className="min-w-0">
                    <span className="text-[13px] font-medium text-ink">{item.name}</span>
                    {item.start_date && item.end_date && (
                      <span className="block md:inline text-[11px] text-ink-4 md:ml-2 mt-0.5 md:mt-0">
                        {fmtDate(item.start_date)} — {fmtDate(item.end_date)}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center flex-wrap gap-2 md:gap-3 shrink-0">
                    {item.total_return != null && (
                      <span className={`font-mono text-[13px] ${item.total_return >= 0 ? "text-pos" : "text-breach"}`}>
                        {pct(item.total_return)}
                      </span>
                    )}
                    <StatusBadge status={item.status} />
                    {item.source_type === "pipeline_backtest" && (
                      <span className="px-2 py-0.5 bg-pos-soft text-pos-soft-ink rounded-md text-[10px] font-medium">Pipeline</span>
                    )}
                    {(item.source_type === "seed_demo" || item.source_type === "unknown") && (
                      <span className="px-2 py-0.5 bg-caution-soft text-caution-soft-ink rounded-md text-[10px] font-medium">
                        {item.source_type === "seed_demo" ? "Seed / Demo" : "Unverified"}
                      </span>
                    )}
                    {item.is_promoted && (
                      <span className="px-2 py-0.5 bg-primary-soft text-primary rounded-md text-[11px] font-medium">
                        promoted
                      </span>
                    )}
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {detail && (
        <>
          {/* Demo/unverified warning */}
          {(detail.is_demo || detail.source_type === "unknown" || detail.source_type === "seed_demo") && (
            <div className="rounded-lg border border-caution bg-caution-soft p-3 text-[12.5px] text-caution-soft-ink">
              This backtest has no pipeline lineage and should be treated as seed/demo or unverified data.
            </div>
          )}

          {/* Experiment header */}
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-[15px] font-semibold text-ink">{detail.name}</h2>
              <p className="text-[11px] text-ink-4 mt-1">
                {detail.universe_name || "Unknown universe"}
                {detail.start_date && ` · ${fmtDate(detail.start_date)}`}
                {detail.end_date && ` — ${fmtDate(detail.end_date)}`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={detail.status} />
              {detail.is_promoted && (
                <span className="px-2 py-0.5 bg-primary-soft text-primary rounded-md text-[11px] font-medium">
                  promoted
                </span>
              )}
            </div>
          </div>

          {/* Result summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-gap">
            <MetricCard label="Total Return" value={pct(detail.results.total_return)} />
            <MetricCard label="Annualized Return" value={pct(detail.results.annualized_return)} />
            <MetricCard label="Max Drawdown" value={pct(detail.results.max_drawdown)} />
            <MetricCard label="Sharpe Ratio" value={detail.results.sharpe_ratio?.toFixed(2) ?? "—"} />
            <MetricCard label="Calmar Ratio" value={detail.results.calmar_ratio?.toFixed(2) ?? "—"} />
            <MetricCard label="Volatility" value={pct(detail.results.volatility)} />
            <MetricCard label="Total Trades" value={String(detail.results.total_trades ?? "—")} />
            <MetricCard label="Avg Turnover" value={pct(detail.results.avg_turnover)} />
          </div>

          {/* Phase 19D: benchmark comparison table. Hidden when neither
              benchmark has data (legacy backtests with null benchmark_metrics). */}
          {detail.results.benchmark_metrics &&
            Object.values(detail.results.benchmark_metrics).some((v) => v != null) && (
              <div className="bg-surface border border-line rounded-lg shadow-sm p-pad overflow-x-auto">
                <h3 className="text-[13px] font-semibold text-ink mb-3">
                  Strategy vs benchmarks
                </h3>
                <table className="w-full text-[13px] border-collapse min-w-[480px]">
                  <thead>
                    <tr className="text-left text-ink-3 border-b border-line">
                      <th className="py-2 pr-3 font-medium">Metric</th>
                      <th className="py-2 px-3 font-medium">Strategy</th>
                      {Object.keys(detail.results.benchmark_metrics).map((sym) => (
                        <th key={sym} className="py-2 px-3 font-medium">{sym}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="font-mono">
                    {((): React.ReactNode => {
                      const rows: { label: string; key: keyof BacktestResultSummary & keyof BenchmarkMetricBlock; fmt: (v: number | null | undefined) => string }[] = [
                        { label: "Total Return", key: "total_return", fmt: (v) => pct(v ?? null) },
                        { label: "Annualized Return", key: "annualized_return", fmt: (v) => pct(v ?? null) },
                        { label: "Max Drawdown", key: "max_drawdown", fmt: (v) => pct(v ?? null) },
                        { label: "Sharpe Ratio", key: "sharpe_ratio", fmt: (v) => v?.toFixed(2) ?? "—" },
                        { label: "Calmar Ratio", key: "calmar_ratio", fmt: (v) => v?.toFixed(2) ?? "—" },
                        { label: "Volatility", key: "volatility", fmt: (v) => pct(v ?? null) },
                      ];
                      return rows.map(({ label, key, fmt }) => (
                        <tr key={key} className="border-b border-line/60 last:border-0">
                          <td className="py-2 pr-3 text-ink-2 font-sans">{label}</td>
                          <td className="py-2 px-3 text-ink">{fmt(detail.results[key])}</td>
                          {Object.entries(detail.results.benchmark_metrics ?? {}).map(([sym, block]) => (
                            <td key={sym} className="py-2 px-3 text-ink-2">
                              {block ? fmt(block[key]) : "—"}
                            </td>
                          ))}
                        </tr>
                      ));
                    })()}
                  </tbody>
                </table>
              </div>
            )}

          {/* Equity curve */}
          <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
            <h3 className="text-[13px] font-semibold text-ink mb-4">Equity Curve (base 100)</h3>
            <EquityCurveChart data={detail.equity_curve} />
          </div>

          {/* Config table */}
          <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
            <h3 className="text-[13px] font-semibold text-ink mb-3">Experiment Configuration</h3>
            <dl className="space-y-2 md:space-y-1 text-[13px]">
              {Object.entries(detail.config).map(([key, val]) => (
                <div key={key} className="flex flex-col md:flex-row md:gap-3">
                  <dt className="text-ink-3 md:w-40 md:shrink-0">{key.replace(/_/g, " ")}</dt>
                  <dd className="text-ink-2 break-words md:flex-1">{String(val)}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Provenance */}
          {detail.source_type === "pipeline_backtest" && (
            <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
              <h3 className="text-[13px] font-semibold text-ink mb-3">Provenance</h3>
              <dl className="space-y-2 md:space-y-1 text-[13px]">
                <div className="flex flex-col md:flex-row md:gap-3">
                  <dt className="text-ink-3 md:w-40 md:shrink-0">Source type</dt>
                  <dd><span className="px-2 py-0.5 bg-pos-soft text-pos-soft-ink rounded-md text-[10px] font-medium">Pipeline</span></dd>
                </div>
                {detail.decision_count != null && (
                  <div className="flex flex-col md:flex-row md:gap-3">
                    <dt className="text-ink-3 md:w-40 md:shrink-0">Decision points</dt>
                    <dd className="text-ink-2 font-mono">{detail.decision_count}</dd>
                  </div>
                )}
                {detail.market_bar_window && (
                  <div className="flex flex-col md:flex-row md:gap-3">
                    <dt className="text-ink-3 md:w-40 md:shrink-0">Market bar window</dt>
                    <dd className="text-ink-2 font-mono break-words">{detail.market_bar_window.start} — {detail.market_bar_window.end}</dd>
                  </div>
                )}
                <div className="flex flex-col md:flex-row md:gap-3">
                  <dt className="text-ink-3 md:w-40 md:shrink-0">Lineage</dt>
                  <dd className={`text-[11px] font-medium ${detail.lineage_available ? "text-pos" : "text-ink-3"}`}>
                    {detail.lineage_available ? "Available" : "Not available"}
                  </dd>
                </div>
              </dl>
            </div>
          )}

          {/* Warnings */}
          {detail.warnings.length > 0 && <WarningsBlock warnings={detail.warnings} />}
        </>
      )}
    </div>
  );
}
