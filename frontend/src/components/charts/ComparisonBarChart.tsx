"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { ComparisonWeightRow } from "@/services/api";

export function ComparisonBarChart({ rows }: { rows: ComparisonWeightRow[] }) {
  if (rows.length === 0) {
    return <div className="h-48 flex items-center justify-center text-[13px] text-ink-3">No comparison data.</div>;
  }
  const data = [...rows].sort((a, b) => b.recommendation_weight - a.recommendation_weight)
    .map((r) => ({ ticker: r.ticker, recommendation: Math.round(r.recommendation_weight * 1000) / 10, benchmark: Math.round(r.benchmark_weight * 1000) / 10 }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
          <XAxis dataKey="ticker" tick={{ fontSize: 11, fontFamily: "var(--font-mono)", fill: "oklch(0.42 0.012 250)" }} tickLine={false} axisLine={{ stroke: "oklch(0.92 0.008 240)" }} />
          <YAxis tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} width={36} />
          <Tooltip formatter={(value: number, name: string) => [`${value}%`, name === "recommendation" ? "Recommendation" : "Benchmark"]}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid oklch(0.92 0.008 240)", boxShadow: "var(--shadow-sm)" }}
            cursor={{ fill: "oklch(0.96 0.007 240)" }} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            formatter={(v) => <span className="text-ink-2">{v === "recommendation" ? "Recommendation" : "Benchmark"}</span>} />
          <Bar dataKey="recommendation" fill="oklch(0.52 0.17 255)" radius={[4, 4, 0, 0]} maxBarSize={32} name="recommendation" />
          <Bar dataKey="benchmark" fill="oklch(0.86 0.01 240)" radius={[4, 4, 0, 0]} maxBarSize={32} name="benchmark" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
