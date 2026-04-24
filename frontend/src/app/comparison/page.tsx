"use client";

import { useEffect, useState } from "react";
import { fetchCurrentComparison, ComparisonData } from "@/services/api";
import { ConfidenceBlock } from "@/components/recommendation/ConfidenceBlock";
import { ComparisonBarChart } from "@/components/charts/ComparisonBarChart";
import { usePaneContext } from "@/components/shell/ContextPane";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { PageEmpty } from "@/components/feedback/PageEmpty";

function stanceColor(stance: string | null): string {
  switch (stance) {
    case "overweight": return "text-qp-green-600";
    case "underweight": return "text-qp-red-600";
    default: return "text-qp-text-secondary";
  }
}

function deltaColor(d: number): string {
  if (d > 0.005) return "text-qp-green-600";
  if (d < -0.005) return "text-qp-red-600";
  return "text-qp-text-secondary";
}

export default function ComparisonPage() {
  const [data, setData] = useState<ComparisonData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { openPane } = usePaneContext();

  useEffect(() => {
    fetchCurrentComparison()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading comparison..." />;

  if (error) {
    return (
      <PageError
        title="Comparison Error"
        message={error}
        hint="Ensure the backend is running and the database is seeded."
      />
    );
  }

  if (!data) {
    return (
      <PageEmpty
        title="No Recommendation to Compare"
        message="The comparison view requires a published recommendation. Run the seed script to create one."
      />
    );
  }

  return (
    <div className="space-y-qp-6">
      <div>
        <h1 className="text-qp-h1">Engine Comparison</h1>
        <p className="text-qp-small text-qp-text-muted mt-1">
          Recommendation vs {data.benchmark_name}
        </p>
      </div>

      {/* Summary metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-qp-4">
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <p className="text-qp-small text-qp-text-muted">Total Active Weight</p>
          <p className="text-qp-hero font-mono">{(data.total_active_weight * 100).toFixed(1)}%</p>
          <p className="text-qp-small text-qp-text-muted">Sum of absolute deviations from benchmark</p>
        </div>
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <p className="text-qp-small text-qp-text-muted">Top 3 Concentration</p>
          <div className="flex items-baseline gap-qp-3 mt-1">
            <div>
              <p className="text-qp-h2 font-mono">{(data.concentration_top3_rec * 100).toFixed(0)}%</p>
              <p className="text-qp-small text-qp-text-muted">Recommendation</p>
            </div>
            <span className="text-qp-text-muted">vs</span>
            <div>
              <p className="text-qp-h2 font-mono">{(data.concentration_top3_bench * 100).toFixed(0)}%</p>
              <p className="text-qp-small text-qp-text-muted">{data.benchmark_name}</p>
            </div>
          </div>
        </div>
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <ConfidenceBlock confidence={data.recommendation_confidence} />
        </div>
      </div>

      {/* Chart */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-4">Weight Comparison</h3>
        <ComparisonBarChart rows={data.weights} />
      </div>

      {/* Detailed table */}
      <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
        <h3 className="text-qp-h3 mb-qp-3">
          Position Detail
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
                <th className="text-right py-qp-2 pr-qp-3">Rec. Wt</th>
                <th className="text-right py-qp-2 pr-qp-3">Bench. Wt</th>
                <th className="text-right py-qp-2 pr-qp-3">Active</th>
                <th className="text-left py-qp-2">Stance</th>
              </tr>
            </thead>
            <tbody>
              {data.weights.map((row) => (
                <tr
                  key={row.asset_id}
                  className="border-b border-qp-border/50 hover:bg-qp-bg-hover cursor-pointer transition-colors duration-qp"
                  onClick={() =>
                    openPane(`${row.ticker} Comparison`, (
                      <div className="space-y-qp-4">
                        <div>
                          <p className="text-qp-small text-qp-text-muted">Asset</p>
                          <p className="text-qp-body font-medium">{row.name}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-qp-3">
                          <div>
                            <p className="text-qp-small text-qp-text-muted">Recommendation</p>
                            <p className="text-qp-h2 font-mono">{(row.recommendation_weight * 100).toFixed(1)}%</p>
                          </div>
                          <div>
                            <p className="text-qp-small text-qp-text-muted">{data.benchmark_name}</p>
                            <p className="text-qp-h2 font-mono">{(row.benchmark_weight * 100).toFixed(1)}%</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-qp-small text-qp-text-muted">Active Weight</p>
                          <p className={`text-qp-h2 font-mono ${deltaColor(row.delta)}`}>
                            {row.delta > 0 ? "+" : ""}{(row.delta * 100).toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-qp-small text-qp-text-muted">Stance</p>
                          <p className={`text-qp-body font-medium ${stanceColor(row.recommendation_stance)}`}>
                            {row.recommendation_stance || "neutral"}
                          </p>
                        </div>
                      </div>
                    ))
                  }
                >
                  <td className="py-qp-2 pr-qp-3 font-mono font-medium">{row.ticker}</td>
                  <td className="py-qp-2 pr-qp-3 text-qp-text-secondary">{row.name}</td>
                  <td className="py-qp-2 pr-qp-3 text-right font-mono">{(row.recommendation_weight * 100).toFixed(1)}%</td>
                  <td className="py-qp-2 pr-qp-3 text-right font-mono">{(row.benchmark_weight * 100).toFixed(1)}%</td>
                  <td className={`py-qp-2 pr-qp-3 text-right font-mono ${deltaColor(row.delta)}`}>
                    {row.delta > 0 ? "+" : ""}{(row.delta * 100).toFixed(1)}%
                  </td>
                  <td className={`py-qp-2 ${stanceColor(row.recommendation_stance)}`}>
                    {row.recommendation_stance || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rationale + Warnings */}
      {data.recommendation_rationale && (
        <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-4">
          <h3 className="text-qp-h3 mb-qp-2">Recommendation Rationale</h3>
          <p className="text-qp-body text-qp-text-secondary">{data.recommendation_rationale}</p>
        </div>
      )}

      {data.recommendation_warning_count > 0 && (
        <div className="p-qp-4 bg-qp-amber-400/10 border border-qp-amber-400 rounded-qp">
          <p className="text-qp-body text-qp-amber-600">
            {data.recommendation_warning_count} active warning{data.recommendation_warning_count > 1 ? "s" : ""}
          </p>
        </div>
      )}
    </div>
  );
}
