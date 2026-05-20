"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { EquityCurvePoint } from "@/services/api";

export function EquityCurveChart({ data }: { data: EquityCurvePoint[] }) {
  if (data.length === 0) {
    return <div className="h-48 flex items-center justify-center text-[13px] text-ink-3">No equity curve data.</div>;
  }
  const formatted = data.map((p) => ({ date: p.date.slice(5), value: p.value }));
  // Compute a short summary so screen readers don't get just "graphic" —
  // they get the actual range + endpoints, which is the useful bit.
  const first = data[0].value;
  const last = data[data.length - 1].value;
  const min = Math.min(...data.map((p) => p.value));
  const max = Math.max(...data.map((p) => p.value));
  const ariaSummary = `Equity curve from base ${first.toFixed(1)} on ${data[0].date} to ${last.toFixed(1)} on ${data[data.length - 1].date}. Range ${min.toFixed(1)}–${max.toFixed(1)} across ${data.length} data points.`;
  return (
    <div role="img" aria-label={ariaSummary} className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formatted} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: "oklch(0.58 0.01 250)" }} tickLine={false} axisLine={{ stroke: "oklch(0.92 0.008 240)" }} />
          <YAxis tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }} tickLine={false} axisLine={false} width={40} domain={["auto", "auto"]} />
          <ReferenceLine y={100} stroke="oklch(0.92 0.008 240)" strokeDasharray="4 4" />
          <Tooltip formatter={(value: number) => [value.toFixed(2), "Value"]}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid oklch(0.92 0.008 240)", boxShadow: "var(--shadow-sm)" }} />
          <Line type="monotone" dataKey="value" stroke="oklch(0.52 0.17 255)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "oklch(0.52 0.17 255)" }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
