"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from "recharts";
import { PaperHolding } from "@/services/api";

interface Props {
  holdings: PaperHolding[];
}

export function DriftBarChart({ holdings }: Props) {
  if (holdings.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-qp-body text-qp-text-muted">
        No holdings data available.
      </div>
    );
  }

  const data = [...holdings]
    .sort((a, b) => Math.abs(b.drift) - Math.abs(a.drift))
    .map((h) => ({
      ticker: h.ticker,
      drift: Math.round(h.drift * 1000) / 10,
    }));

  return (
    <div className="h-56">
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
          <ReferenceLine y={0} stroke="#e2e8f0" />
          <Tooltip
            formatter={(value: number) => [`${value}%`, "Drift"]}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e2e8f0",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            }}
          />
          <Bar dataKey="drift" radius={[4, 4, 0, 0]} maxBarSize={36}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={d.drift > 0 ? "#22c55e" : d.drift < 0 ? "#ef4444" : "#94a3b8"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
