"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { WeightEntry } from "@/services/api";

interface Props {
  weights: WeightEntry[];
}

const STANCE_COLORS: Record<string, string> = {
  overweight: "#22c55e",
  underweight: "#ef4444",
  neutral: "#60a5fa",
};

export function WeightsBarChart({ weights }: Props) {
  if (weights.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-qp-body text-qp-text-muted">
        No weight data available for chart.
      </div>
    );
  }

  const data = [...weights]
    .sort((a, b) => b.target_weight - a.target_weight)
    .map((w) => ({
      ticker: w.ticker,
      weight: Math.round(w.target_weight * 1000) / 10,
      stance: w.stance,
    }));

  return (
    <div className="h-64">
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
            formatter={(value: number) => [`${value}%`, "Weight"]}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e2e8f0",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            }}
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
          />
          <Bar dataKey="weight" radius={[4, 4, 0, 0]} maxBarSize={48}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={STANCE_COLORS[d.stance || "neutral"] || "#60a5fa"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {/* Legend for stance colors */}
      <div className="flex items-center justify-center gap-qp-6 mt-qp-2">
        {Object.entries(STANCE_COLORS).map(([label, color]) => (
          <div key={label} className="flex items-center gap-qp-1">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-qp-small text-qp-text-muted capitalize">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
