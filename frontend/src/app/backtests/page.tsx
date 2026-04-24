"use client";

import { useEffect, useState } from "react";
import {
  fetchBacktestList, fetchBacktest,
  BacktestListData, BacktestDetail,
} from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { fmtDate } from "@/lib/format";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";

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
  const [list, setList] = useState<BacktestListData | null>(null);
  const [detail, setDetail] = useState<BacktestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
  }, []);

  if (loading) return <PageLoading label="Loading backtests..." />;
  if (error) return <PageError title="Backtest Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!list || list.total === 0) return <PageEmpty title="No Backtests" message="No backtest experiments available. Run the seed script to create demo data." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Backtests</h1>
        <p className="text-[11px] text-ink-4 mt-1">
          {list.total} experiment{list.total !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Experiment list */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <h3 className="text-[13px] font-semibold text-ink mb-3">Experiments</h3>
        {list.items.map((item) => (
          <div
            key={item.id}
            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
              detail?.id === item.id
                ? "bg-primary-soft border border-primary"
                : "hover:bg-surface-3"
            }`}
            onClick={async () => {
              const res = await fetchBacktest(item.id);
              setDetail(res.data);
            }}
          >
            <div>
              <span className="text-[13px] font-medium">{item.name}</span>
              {item.start_date && item.end_date && (
                <span className="text-[11px] text-ink-4 ml-2">
                  {fmtDate(item.start_date)} — {fmtDate(item.end_date)}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              {item.total_return != null && (
                <span className={`font-mono text-[13px] ${item.total_return >= 0 ? "text-pos" : "text-breach"}`}>
                  {pct(item.total_return)}
                </span>
              )}
              <StatusBadge status={item.status} />
              {item.is_promoted && (
                <span className="px-2 py-0.5 bg-primary-soft text-primary rounded-md text-[11px] font-medium">
                  promoted
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {detail && (
        <>
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
            <MetricCard label="Volatility" value={pct(detail.results.volatility)} />
            <MetricCard label="Total Trades" value={String(detail.results.total_trades ?? "—")} />
            <MetricCard label="Avg Turnover" value={pct(detail.results.avg_turnover)} />
          </div>

          {/* Equity curve */}
          <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
            <h3 className="text-[13px] font-semibold text-ink mb-4">Equity Curve (base 100)</h3>
            <EquityCurveChart data={detail.equity_curve} />
          </div>

          {/* Config table */}
          <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
            <h3 className="text-[13px] font-semibold text-ink mb-3">Experiment Configuration</h3>
            <div className="space-y-1">
              {Object.entries(detail.config).map(([key, val]) => (
                <div key={key} className="flex gap-3 text-[13px]">
                  <span className="text-ink-3 w-40 shrink-0">{key.replace(/_/g, " ")}</span>
                  <span className="text-ink-2">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Warnings */}
          {detail.warnings.length > 0 && <WarningsBlock warnings={detail.warnings} />}
        </>
      )}
    </div>
  );
}
