"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import { PaperHolding } from "@/services/api";

export function DriftBarChart({ holdings }: { holdings: PaperHolding[] }) {
  if (holdings.length === 0) {
    return <div className="h-48 flex items-center justify-center text-[13px] text-ink-3">No holdings data.</div>;
  }
  const data = [...holdings].sort((a, b) => Math.abs(b.drift) - Math.abs(a.drift))
    .map((h) => ({ ticker: h.ticker, drift: Math.round(h.drift * 1000) / 10 }));
  return (
    <div className="h-52">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
          <XAxis dataKey="ticker" tick={{ fontSize: 11, fontFamily: "var(--font-mono)", fill: "oklch(0.42 0.012 250)" }} tickLine={false} axisLine={{ stroke: "oklch(0.92 0.008 240)" }} />
          <YAxis tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} width={36} />
          <ReferenceLine y={0} stroke="oklch(0.92 0.008 240)" />
          <Tooltip formatter={(value: number) => [`${value}%`, "Drift"]} contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid oklch(0.92 0.008 240)" }} />
          <Bar dataKey="drift" radius={[4, 4, 0, 0]} maxBarSize={32}>
            {data.map((d, i) => (<Cell key={i} fill={d.drift > 0 ? "oklch(0.58 0.13 155)" : d.drift < 0 ? "oklch(0.58 0.18 25)" : "oklch(0.58 0.01 250)"} />))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
