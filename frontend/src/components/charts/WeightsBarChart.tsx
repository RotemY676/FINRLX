"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { WeightEntry } from "@/services/api";

const STANCE_COLORS: Record<string, string> = {
  overweight: "oklch(0.58 0.13 155)",
  underweight: "oklch(0.58 0.18 25)",
  neutral: "oklch(0.52 0.17 255)",
};

export function WeightsBarChart({ weights }: { weights: WeightEntry[] }) {
  if (weights.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-[13px] text-ink-3">
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
    <div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
            <XAxis dataKey="ticker" tick={{ fontSize: 11, fontFamily: "var(--font-mono)", fill: "oklch(0.42 0.012 250)" }} tickLine={false} axisLine={{ stroke: "oklch(0.92 0.008 240)" }} />
            <YAxis tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} width={36} />
            <Tooltip formatter={(value: number) => [`${value}%`, "Weight"]} contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid oklch(0.92 0.008 240)", boxShadow: "var(--shadow-sm)" }} cursor={{ fill: "oklch(0.96 0.007 240)" }} />
            <Bar dataKey="weight" radius={[4, 4, 0, 0]} maxBarSize={40}>
              {data.map((d, i) => (<Cell key={i} fill={STANCE_COLORS[d.stance || "neutral"] || STANCE_COLORS.neutral} />))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center justify-center gap-5 mt-2">
        {Object.entries({ overweight: "Overweight", neutral: "Neutral", underweight: "Underweight" }).map(([k, label]) => (
          <div key={k} className="flex items-center gap-1.5 text-[11px] text-ink-3">
            <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: STANCE_COLORS[k] }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
