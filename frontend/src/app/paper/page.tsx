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
  if (Math.abs(d) > 0.01) return d > 0 ? "text-pos" : "text-breach";
  return "text-ink-2";
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
    <div className="space-y-gap max-w-[1200px]">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[20px] font-semibold text-ink">Paper Portfolio</h1>
          <p className="text-[11px] text-ink-4 mt-1">{data.name}</p>
        </div>
        <StatusBadge status={data.is_active ? "published" : "stale"} />
      </div>

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
              Last: {new Date(data.last_rebalance_at).toLocaleDateString()}
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

      {/* Drift chart */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <h3 className="text-[13px] font-semibold text-ink mb-4">Drift from Target</h3>
        <DriftBarChart holdings={data.holdings} />
      </div>

      {/* Holdings table */}
      <div className="bg-surface border border-line rounded-lg shadow-sm p-pad">
        <h3 className="text-[13px] font-semibold text-ink mb-3">
          Holdings
          <span className="text-[11px] text-ink-4 font-normal ml-2">
            Click a row to inspect
          </span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-line text-[11px] text-ink-3">
                <th className="text-left py-2 pr-3">Ticker</th>
                <th className="text-left py-2 pr-3">Name</th>
                <th className="text-right py-2 pr-3">Target</th>
                <th className="text-right py-2 pr-3">Current</th>
                <th className="text-right py-2">Drift</th>
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((h) => (
                <tr
                  key={h.asset_id}
                  className="border-b border-line/50 hover:bg-surface-3 cursor-pointer transition-colors"
                  onClick={() =>
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
                    ))
                  }
                >
                  <td className="py-2 pr-3 font-mono font-medium">{h.ticker}</td>
                  <td className="py-2 pr-3 text-ink-2">{h.name}</td>
                  <td className="py-2 pr-3 text-right font-mono">{(h.target_weight * 100).toFixed(1)}%</td>
                  <td className="py-2 pr-3 text-right font-mono">{(h.current_weight * 100).toFixed(1)}%</td>
                  <td className={`py-2 text-right font-mono ${driftColor(h.drift)}`}>
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
