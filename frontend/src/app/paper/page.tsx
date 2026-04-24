"use client";

import { useEffect, useState } from "react";
import { fetchCurrentPaper, PaperPortfolioData } from "@/services/api";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { WarningsBlock } from "@/components/recommendation/WarningsBlock";
import { DriftBarChart } from "@/components/charts/DriftBarChart";
import { usePaneContext } from "@/components/shell/ContextPane";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";

function driftColor(d: number): string {
  if (Math.abs(d) > 0.01) return d > 0 ? "text-qp-green-600" : "text-qp-red-600";
  return "text-qp-text-secondary";
}

export default function PaperPage() {
  const [data, setData] = useState<PaperPortfolioData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { openPane } = usePaneContext();

  useEffect(() => {
    fetchCurrentPaper()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading paper portfolio..." />;
  if (error) return <PageError title="Paper Portfolio Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!data) return <PageEmpty title="No Paper Portfolio" message="No active paper portfolio found. Run the seed script to create one." />;

  const maxDrift = Math.max(...data.holdings.map((h) => Math.abs(h.drift)));

  return (
    <div className="space-y-qp-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-qp-h1">Paper Portfolio</h1>
          <p className="text-qp-small text-qp-text-muted mt-1">{data.name}</p>
        </div>
        <StatusBadge status={data.is_active ? "published" : "stale"} />
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-qp-4">
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <p className="text-qp-small text-qp-text-muted">Invested</p>
          <p className="text-qp-h2 font-mono">{(data.invested_weight * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <p className="text-qp-small text-qp-text-muted">Cash</p>
          <p className="text-qp-h2 font-mono">{(data.cash_weight * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <p className="text-qp-small text-qp-text-muted">Rebalances</p>
          <p className="text-qp-h2 font-mono">{data.total_rebalances}</p>
          {data.last_rebalance_at && (
            <p className="text-qp-small text-qp-text-muted mt-1">
              Last: {new Date(data.last_rebalance_at).toLocaleDateString()}
            </p>
          )}
        </div>
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <p className="text-qp-small text-qp-text-muted">Max Drift</p>
          <p className={`text-qp-h2 font-mono ${maxDrift > 0.01 ? "text-qp-amber-600" : "text-qp-green-600"}`}>
            {(maxDrift * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Drift chart */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-4">Drift from Target</h3>
        <DriftBarChart holdings={data.holdings} />
      </div>

      {/* Holdings table */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-3">
          Holdings
          <span className="text-qp-small text-qp-text-muted font-normal ml-qp-2">
            Click a row to inspect
          </span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-qp-body">
            <thead>
              <tr className="border-b border-qp-border text-qp-small text-qp-text-muted">
                <th className="text-left py-qp-2 pr-qp-3">Ticker</th>
                <th className="text-left py-qp-2 pr-qp-3">Name</th>
                <th className="text-right py-qp-2 pr-qp-3">Target</th>
                <th className="text-right py-qp-2 pr-qp-3">Current</th>
                <th className="text-right py-qp-2">Drift</th>
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((h) => (
                <tr
                  key={h.asset_id}
                  className="border-b border-qp-border/50 hover:bg-qp-bg-hover cursor-pointer transition-colors duration-qp"
                  onClick={() =>
                    openPane(`${h.ticker} Paper Detail`, (
                      <div className="space-y-qp-4">
                        <div>
                          <p className="text-qp-small text-qp-text-muted">Asset</p>
                          <p className="text-qp-body font-medium">{h.name} ({h.ticker})</p>
                        </div>
                        <div className="grid grid-cols-2 gap-qp-3">
                          <div>
                            <p className="text-qp-small text-qp-text-muted">Target Weight</p>
                            <p className="text-qp-h2 font-mono">{(h.target_weight * 100).toFixed(1)}%</p>
                          </div>
                          <div>
                            <p className="text-qp-small text-qp-text-muted">Current Weight</p>
                            <p className="text-qp-h2 font-mono">{(h.current_weight * 100).toFixed(1)}%</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-qp-small text-qp-text-muted">Drift</p>
                          <p className={`text-qp-h2 font-mono ${driftColor(h.drift)}`}>
                            {h.drift > 0 ? "+" : ""}{(h.drift * 100).toFixed(1)}%
                          </p>
                          {Math.abs(h.drift) > 0.01 && (
                            <p className="text-qp-small text-qp-amber-600 mt-1">
                              Exceeds 1% drift threshold
                            </p>
                          )}
                        </div>
                      </div>
                    ))
                  }
                >
                  <td className="py-qp-2 pr-qp-3 font-mono font-medium">{h.ticker}</td>
                  <td className="py-qp-2 pr-qp-3 text-qp-text-secondary">{h.name}</td>
                  <td className="py-qp-2 pr-qp-3 text-right font-mono">{(h.target_weight * 100).toFixed(1)}%</td>
                  <td className="py-qp-2 pr-qp-3 text-right font-mono">{(h.current_weight * 100).toFixed(1)}%</td>
                  <td className={`py-qp-2 text-right font-mono ${driftColor(h.drift)}`}>
                    {h.drift > 0 ? "+" : ""}{(h.drift * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warnings */}
      {data.warnings.length > 0 && <WarningsBlock warnings={data.warnings} />}

      {/* Event log */}
      {data.events.length > 0 && (
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <h3 className="text-qp-h3 mb-qp-3">Event Log</h3>
          <div className="space-y-qp-2">
            {data.events.map((ev, i) => (
              <div key={i} className="flex items-start gap-qp-3 text-qp-body">
                <span className={`px-qp-2 py-0.5 rounded-qp-sm text-qp-small font-medium shrink-0 ${
                  ev.event_type === "rebalance" ? "bg-qp-blue-50 text-qp-blue-700" :
                  ev.event_type === "drift_alert" ? "bg-qp-amber-400/10 text-qp-amber-600" :
                  "bg-qp-border text-qp-text-secondary"
                }`}>
                  {ev.event_type.replace(/_/g, " ")}
                </span>
                <div className="flex-1">
                  <p className="text-qp-text-secondary">{ev.description}</p>
                  <p className="text-qp-small text-qp-text-muted">
                    {new Date(ev.timestamp).toLocaleString()}
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
