"use client";

import { useEffect, useState } from "react";
import {
  fetchCurrentComparison, fetchEngineComparison,
  ComparisonData, EngineComparisonData,
} from "@/services/api";
import { Icon } from "@/components/icons/Icon";
import { ConfidenceBlock } from "@/components/recommendation/ConfidenceBlock";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { ComparisonBarChart } from "@/components/charts/ComparisonBarChart";
import { AlignmentChart } from "@/components/charts/AlignmentChart";
import { usePaneContext } from "@/components/shell/ContextPane";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";
import { SourceBadge } from "@/components/recommendation/SourceBadge";

const STANCE_STYLE: Record<string, string> = {
  buy: "text-pos-soft-ink bg-pos-soft", sell: "text-breach-soft-ink bg-breach-soft",
  hold: "text-ink-3 bg-surface-3", trim: "text-caution-soft-ink bg-caution-soft",
  overweight: "text-pos-soft-ink bg-pos-soft", underweight: "text-breach-soft-ink bg-breach-soft",
  neutral: "text-ink-3 bg-surface-3",
};

export default function ComparisonPage() {
  const [data, setData] = useState<ComparisonData | null>(null);
  const [engines, setEngines] = useState<EngineComparisonData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { openPane } = usePaneContext();

  useEffect(() => {
    Promise.all([fetchCurrentComparison(), fetchEngineComparison()])
      .then(([comp, eng]) => { setData(comp.data); setEngines(eng.data); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading comparison..." />;
  if (error) return <PageError title="Comparison Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!data) return <PageEmpty title="No Recommendation to Compare" message="Publish a recommendation first." />;

  return (
    <div className="space-y-gap max-w-[1200px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Engine Comparison</h1>
        <p className="text-[12px] text-ink-3 mt-0.5">
          {engines ? `${engines.engines.length} engines · synthesis: ${engines.synthesis_stance}` : `Recommendation vs ${data.benchmark_name}`}
        </p>
      </div>

      {/* Summary metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-gap">
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <p className="text-[11px] text-ink-4">Total Active Weight</p>
          <p className="text-[24px] font-display font-semibold text-ink">{(data.total_active_weight * 100).toFixed(1)}%</p>
        </div>
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <p className="text-[11px] text-ink-4">Top 3 Concentration</p>
          <div className="flex items-baseline gap-3 mt-1">
            <div>
              <p className="text-[18px] font-display font-semibold text-ink">{(data.concentration_top3_rec * 100).toFixed(0)}%</p>
              <p className="text-[11px] text-ink-4">Rec</p>
            </div>
            <span className="text-ink-4">vs</span>
            <div>
              <p className="text-[18px] font-display font-semibold text-ink">{(data.concentration_top3_bench * 100).toFixed(0)}%</p>
              <p className="text-[11px] text-ink-4">{data.benchmark_name}</p>
            </div>
          </div>
        </div>
        {engines && (
          <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
            <p className="text-[11px] text-ink-4">Engine Dispersion</p>
            <p className="text-[24px] font-display font-semibold text-caution">{(engines.dispersion * 100).toFixed(0)}%</p>
            <p className="text-[11px] text-ink-4">{engines.engines.filter(e => e.stance === "buy").length} buy · {engines.engines.filter(e => e.stance !== "buy").length} other</p>
          </div>
        )}
        <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <ConfidenceBlock confidence={data.recommendation_confidence} />
        </div>
      </div>

      {/* ── Multi-engine comparison matrix — now from real backend ── */}
      {engines && engines.engines.length > 0 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-baseline justify-between mb-3">
            <h3 className="text-[13px] font-semibold text-ink">Engine Matrix</h3>
            <span className="md:hidden text-[11px] text-ink-4">Tap a row for detail</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="border-b border-line text-[11px] text-ink-4 uppercase tracking-wider">
                  <th className="text-left py-2 pr-3 font-medium">Engine</th>
                  <th className="text-left py-2 pr-3 font-medium">Stance</th>
                  <th className="text-left py-2 pr-3 font-medium">Confidence</th>
                  <th className="hidden md:table-cell text-right py-2 pr-3 font-medium">Weight</th>
                  <th className="hidden md:table-cell text-left py-2 pr-3 font-medium">Horizon</th>
                  <th className="hidden md:table-cell text-left py-2 pr-3 font-medium">Risk</th>
                  <th className="hidden lg:table-cell text-left py-2 font-medium">Top Drivers</th>
                </tr>
              </thead>
              <tbody>
                {engines.engines.map((eng) => {
                  const openDetail = () =>
                    openPane(`${eng.engine_name} · Methodology`, (
                      <div className="space-y-4">
                        <div>
                          <p className="text-[11px] text-ink-4">Engine</p>
                          <p className="text-[14px] font-semibold text-ink">{eng.engine_name}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-[11px] text-ink-4">Stance</p>
                            <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-medium ${STANCE_STYLE[eng.stance] || ""}`}>{eng.stance}</span>
                          </div>
                          <div>
                            <p className="text-[11px] text-ink-4">Confidence</p>
                            <p className="text-[14px] font-mono text-ink">{(eng.confidence * 100).toFixed(0)}%</p>
                          </div>
                          <div>
                            <p className="text-[11px] text-ink-4">Weight</p>
                            <p className="text-[14px] font-mono text-ink">{(eng.weight * 100).toFixed(0)}%</p>
                          </div>
                          <div>
                            <p className="text-[11px] text-ink-4">Horizon</p>
                            <p className="text-[14px] text-ink">{eng.horizon}</p>
                          </div>
                          <div>
                            <p className="text-[11px] text-ink-4">Risk</p>
                            <p className="text-[14px] text-ink">{eng.risk_read}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-[11px] text-ink-4 mb-1">What it sees (drivers)</p>
                          <ul className="space-y-1">
                            {eng.drivers.map((d, i) => <li key={i} className="text-[12px] text-ink-2">• {d}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="text-[11px] text-ink-4 mb-1">What it ignores</p>
                          <ul className="space-y-1">
                            {eng.ignores.map((d, i) => <li key={i} className="text-[12px] text-ink-3">• {d}</li>)}
                          </ul>
                        </div>
                        {eng.note && (
                          <div className="pt-3 border-t border-line">
                            <p className="text-[11px] text-ink-4 mb-1">Note</p>
                            <p className="text-[12px] text-ink-2">{eng.note}</p>
                          </div>
                        )}
                      </div>
                    ));
                  return (
                    <tr
                      key={eng.engine_key}
                      role="button"
                      tabIndex={0}
                      aria-label={`${eng.engine_name} — open methodology detail`}
                      className="border-b border-line/50 hover:bg-surface-3 focus-visible:bg-surface-3 cursor-pointer transition-colors"
                      onClick={openDetail}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          openDetail();
                        }
                      }}
                    >
                      <td className="py-3 md:py-2 pr-3 font-medium text-ink">
                        {eng.engine_name}
                        {eng.engine_key === "ml_return_forecaster" && (
                          <span className="ml-2"><SourceBadge source="shadow" label="Shadow / experimental" /></span>
                        )}
                        {/* Mobile-only context line: weight + risk shown inline since their columns are hidden. */}
                        <div className="md:hidden text-[11px] text-ink-4 mt-0.5">
                          {(eng.weight * 100).toFixed(0)}% · {eng.horizon} · {eng.risk_read}
                        </div>
                      </td>
                      <td className="py-3 md:py-2 pr-3">
                        <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-medium ${STANCE_STYLE[eng.stance] || ""}`}>{eng.stance}</span>
                      </td>
                      <td className="py-3 md:py-2 pr-3">
                        <div className="flex items-center gap-2">
                          <div className="w-10 sm:w-14 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${eng.confidence >= 0.7 ? "bg-pos" : eng.confidence >= 0.55 ? "bg-caution" : "bg-breach"}`} style={{ width: `${eng.confidence * 100}%` }} />
                          </div>
                          <span className="text-[11px] font-mono text-ink-2">{eng.confidence.toFixed(2)}</span>
                        </div>
                      </td>
                      <td className="hidden md:table-cell py-2 pr-3 text-right font-mono text-ink-2">{(eng.weight * 100).toFixed(0)}%</td>
                      <td className="hidden md:table-cell py-2 pr-3 text-ink-2">{eng.horizon}</td>
                      <td className="hidden md:table-cell py-2 pr-3">
                        <span className={`text-[11px] ${eng.risk_read === "Low" ? "text-pos" : eng.risk_read === "Moderate" ? "text-ink-2" : eng.risk_read === "Elevated" ? "text-caution" : "text-breach"}`}>{eng.risk_read}</span>
                      </td>
                      <td className="hidden lg:table-cell py-2 text-ink-3 text-[11px]">{eng.drivers.slice(0, 2).join("; ")}</td>
                    </tr>
                  );
                })}
                {/* Synthesis row */}
                <tr className="bg-primary-soft">
                  <td className="py-3 md:py-2 pr-3 font-semibold text-primary-soft-ink">
                    Synthesis
                    <div className="md:hidden text-[11px] text-primary-soft-ink/80 mt-0.5">
                      100% · Weighted across all engines
                    </div>
                  </td>
                  <td className="py-3 md:py-2 pr-3">
                    <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-medium ${STANCE_STYLE[engines.synthesis_stance] || ""}`}>{engines.synthesis_stance}</span>
                  </td>
                  <td className="py-3 md:py-2 pr-3">
                    <span className="text-[11px] font-mono text-primary-soft-ink">{engines.synthesis_confidence.toFixed(2)}</span>
                  </td>
                  <td className="hidden md:table-cell py-2 pr-3 text-right font-mono text-primary-soft-ink">100%</td>
                  <td className="hidden md:table-cell py-2 pr-3 text-primary-soft-ink">—</td>
                  <td className="hidden md:table-cell py-2 pr-3 text-primary-soft-ink">—</td>
                  <td className="hidden lg:table-cell py-2 text-primary-soft-ink text-[11px]">Weighted across all engines</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Alignment chart */}
      {engines && engines.engines.length > 0 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <h3 className="text-[13px] font-semibold text-ink mb-4">Engine Alignment</h3>
          <p className="text-[11px] text-ink-4 mb-3">Bubble size = engine portfolio weight. X = stance direction. Y = confidence.</p>
          <AlignmentChart engines={engines.engines} synthesisStance={engines.synthesis_stance} synthesisConfidence={engines.synthesis_confidence} />
        </section>
      )}

      {/* Weight comparison chart */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h3 className="text-[13px] font-semibold text-ink mb-4">Weight Comparison (Rec vs {data.benchmark_name})</h3>
        <ComparisonBarChart rows={data.weights} />
      </section>

      {/* Position detail table */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center justify-between gap-2 mb-3">
          <h3 className="text-[13px] font-semibold text-ink">Position Detail</h3>
          <span className="text-[11px] text-ink-4">Tap a row to inspect</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-line text-[11px] text-ink-4 uppercase tracking-wider">
                <th className="text-left py-2 pr-3 font-medium">Ticker</th>
                <th className="hidden md:table-cell text-left py-2 pr-3 font-medium">Name</th>
                <th className="hidden md:table-cell text-right py-2 pr-3 font-medium">Rec</th>
                <th className="hidden md:table-cell text-right py-2 pr-3 font-medium">Bench</th>
                <th className="text-right py-2 pr-3 font-medium">Active</th>
                <th className="text-left py-2 font-medium">Stance</th>
              </tr>
            </thead>
            <tbody>
              {data.weights.map((row) => {
                const openDetail = () =>
                  openPane(`${row.ticker} · Comparison`, (
                    <div className="space-y-4">
                      <p className="text-[13px] font-medium text-ink">{row.name}</p>
                      <div className="grid grid-cols-2 gap-3">
                        <div><p className="text-[11px] text-ink-4">Recommendation</p><p className="text-[18px] font-mono font-semibold text-ink">{(row.recommendation_weight * 100).toFixed(1)}%</p></div>
                        <div><p className="text-[11px] text-ink-4">{data.benchmark_name}</p><p className="text-[18px] font-mono font-semibold text-ink">{(row.benchmark_weight * 100).toFixed(1)}%</p></div>
                      </div>
                      <div><p className="text-[11px] text-ink-4">Active Weight</p>
                        <p className={`text-[18px] font-mono font-semibold ${row.delta > 0.005 ? "text-pos" : row.delta < -0.005 ? "text-breach" : "text-ink-3"}`}>{row.delta > 0 ? "+" : ""}{(row.delta * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  ));
                return (
                  <tr
                    key={row.asset_id}
                    role="button"
                    tabIndex={0}
                    aria-label={`${row.ticker} — open position detail`}
                    className="border-b border-line/50 hover:bg-surface-3 focus-visible:bg-surface-3 cursor-pointer transition-colors"
                    onClick={openDetail}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openDetail();
                      }
                    }}
                  >
                    <td className="py-3 md:py-2 pr-3 font-mono font-semibold text-ink">
                      {row.ticker}
                      {/* Mobile-only: show name + rec/bench inline, since their columns hide below md. */}
                      <div className="md:hidden text-[11px] text-ink-3 mt-0.5 font-sans font-normal">
                        {row.name}
                      </div>
                      <div className="md:hidden text-[11px] text-ink-4 mt-0.5 font-sans font-normal">
                        Rec {(row.recommendation_weight * 100).toFixed(1)}% · Bench {(row.benchmark_weight * 100).toFixed(1)}%
                      </div>
                    </td>
                    <td className="hidden md:table-cell py-2 pr-3 text-ink-2">{row.name}</td>
                    <td className="hidden md:table-cell py-2 pr-3 text-right font-mono">{(row.recommendation_weight * 100).toFixed(1)}%</td>
                    <td className="hidden md:table-cell py-2 pr-3 text-right font-mono text-ink-3">{(row.benchmark_weight * 100).toFixed(1)}%</td>
                    <td className={`py-3 md:py-2 pr-3 text-right font-mono ${row.delta > 0.005 ? "text-pos" : row.delta < -0.005 ? "text-breach" : "text-ink-3"}`}>
                      {row.delta > 0 ? "+" : ""}{(row.delta * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 md:py-2">
                      <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-medium ${STANCE_STYLE[row.recommendation_stance || "neutral"] || ""}`}>{row.recommendation_stance || "neutral"}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {data.recommendation_rationale && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <h3 className="text-[13px] font-semibold text-ink mb-2">Recommendation Rationale</h3>
          <p className="text-[12.5px] text-ink-2 leading-relaxed">{data.recommendation_rationale}</p>
        </section>
      )}
    </div>
  );
}
