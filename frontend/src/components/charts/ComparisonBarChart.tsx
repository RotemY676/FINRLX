"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { ComparisonWeightRow } from "@/services/api";

interface Props {
  rows: ComparisonWeightRow[];
}

export function ComparisonBarChart({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-qp-body text-qp-text-muted">
        No comparison data available for chart.
      </div>
    );
  }

  const data = [...rows]
    .sort((a, b) => b.recommendation_weight - a.recommendation_weight)
    .map((r) => ({
      ticker: r.ticker,
      recommendation: Math.round(r.recommendation_weight * 1000) / 10,
      benchmark: Math.round(r.benchmark_weight * 1000) / 10,
    }));

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
          <XAxis
            dataKey="ticker"
            tick={{ fontSize: 11, fontFamily: "monospace", fill: "#475569" }}
            tickLine={false}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}%`}
            width={40}
          />
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value}%`,
              name === "recommendation" ? "Recommendation" : "Benchmark",
            ]}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e2e8f0",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            }}
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            formatter={(value) => (
              <span className="text-qp-text-secondary">
                {value === "recommendation" ? "Recommendation" : "Benchmark"}
              </span>
            )}
          />
          <Bar
            dataKey="recommendation"
            fill="#2563eb"
            radius={[4, 4, 0, 0]}
            maxBarSize={36}
            name="recommendation"
          />
          <Bar
            dataKey="benchmark"
            fill="#cbd5e1"
            radius={[4, 4, 0, 0]}
            maxBarSize={36}
            name="benchmark"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
