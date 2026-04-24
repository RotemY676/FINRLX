"use client";

import { useEffect, useState } from "react";
import {
  fetchBacktestList, fetchBacktest,
  BacktestListData, BacktestDetail,
} from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
      <p className="text-qp-small text-qp-text-muted">{label}</p>
      <p className="text-qp-h2 font-mono mt-1">{value}</p>
      {sub && <p className="text-qp-small text-qp-text-muted mt-1">{sub}</p>}
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
    <div className="space-y-qp-6">
      <div>
        <h1 className="text-qp-h1">Backtests</h1>
        <p className="text-qp-small text-qp-text-muted mt-1">
          {list.total} experiment{list.total !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Experiment list */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-3">Experiments</h3>
        {list.items.map((item) => (
          <div
            key={item.id}
            className={`flex items-center justify-between p-qp-3 rounded-qp cursor-pointer transition-colors duration-qp ${
              detail?.id === item.id
                ? "bg-qp-blue-50 border border-qp-blue-200"
                : "hover:bg-qp-bg-hover"
            }`}
            onClick={async () => {
              const res = await fetchBacktest(item.id);
              setDetail(res.data);
            }}
          >
            <div>
              <span className="text-qp-body font-medium">{item.name}</span>
              {item.start_date && item.end_date && (
                <span className="text-qp-small text-qp-text-muted ml-qp-2">
                  {new Date(item.start_date).toLocaleDateString()} — {new Date(item.end_date).toLocaleDateString()}
                </span>
              )}
            </div>
            <div className="flex items-center gap-qp-3">
              {item.total_return != null && (
                <span className={`font-mono text-qp-body ${item.total_return >= 0 ? "text-qp-green-600" : "text-qp-red-600"}`}>
                  {pct(item.total_return)}
                </span>
              )}
              <StatusBadge status={item.status} />
              {item.is_promoted && (
                <span className="px-qp-2 py-0.5 bg-qp-blue-100 text-qp-blue-700 rounded-qp-sm text-qp-small font-medium">
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
              <h2 className="text-qp-h2">{detail.name}</h2>
              <p className="text-qp-small text-qp-text-muted mt-1">
                {detail.universe_name || "Unknown universe"}
                {detail.start_date && ` · ${new Date(detail.start_date).toLocaleDateString()}`}
                {detail.end_date && ` — ${new Date(detail.end_date).toLocaleDateString()}`}
              </p>
            </div>
            <div className="flex items-center gap-qp-2">
              <StatusBadge status={detail.status} />
              {detail.is_promoted && (
                <span className="px-qp-2 py-0.5 bg-qp-blue-100 text-qp-blue-700 rounded-qp-sm text-qp-small font-medium">
                  promoted
                </span>
              )}
            </div>
          </div>

          {/* Result summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-qp-4">
            <MetricCard label="Total Return" value={pct(detail.results.total_return)} />
            <MetricCard label="Annualized Return" value={pct(detail.results.annualized_return)} />
            <MetricCard label="Max Drawdown" value={pct(detail.results.max_drawdown)} />
            <MetricCard label="Sharpe Ratio" value={detail.results.sharpe_ratio?.toFixed(2) ?? "—"} />
            <MetricCard label="Volatility" value={pct(detail.results.volatility)} />
            <MetricCard label="Total Trades" value={String(detail.results.total_trades ?? "—")} />
            <MetricCard label="Avg Turnover" value={pct(detail.results.avg_turnover)} />
          </div>

          {/* Equity curve */}
          <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
            <h3 className="text-qp-h3 mb-qp-4">Equity Curve (base 100)</h3>
            <EquityCurveChart data={detail.equity_curve} />
          </div>

          {/* Config table */}
          <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
            <h3 className="text-qp-h3 mb-qp-3">Experiment Configuration</h3>
            <div className="space-y-qp-1">
              {Object.entries(detail.config).map(([key, val]) => (
                <div key={key} className="flex gap-qp-3 text-qp-body">
                  <span className="text-qp-text-muted w-40 shrink-0">{key.replace(/_/g, " ")}</span>
                  <span className="text-qp-text-secondary">{String(val)}</span>
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
