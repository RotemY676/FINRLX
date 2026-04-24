"use client";

import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { EquityCurvePoint } from "@/services/api";

interface Props {
  data: EquityCurvePoint[];
}

export function EquityCurveChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-qp-body text-qp-text-muted">
        No equity curve data available.
      </div>
    );
  }

  const formatted = data.map((p) => ({
    date: p.date.slice(5), // MM-DD
    value: p.value,
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formatted} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
            width={45}
            domain={["auto", "auto"]}
          />
          <ReferenceLine y={100} stroke="#e2e8f0" strokeDasharray="4 4" />
          <Tooltip
            formatter={(value: number) => [value.toFixed(2), "Value"]}
            labelFormatter={(label) => `Date: ${label}`}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e2e8f0",
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#2563eb" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
