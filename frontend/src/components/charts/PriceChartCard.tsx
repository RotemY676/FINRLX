"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, CartesianGrid,
} from "recharts";
import { fetchPriceChart, PriceChartDataType } from "@/services/api";
import { Icon } from "@/components/icons/Icon";

const EVENT_COLOR: Record<string, string> = {
  pos: "oklch(0.58 0.13 155)", neg: "oklch(0.58 0.18 25)", neutral: "oklch(0.58 0.01 250)",
};

export function PriceChartCard({ ticker = "NVDA" }: { ticker?: string }) {
  const [data, setData] = useState<PriceChartDataType | null>(null);

  useEffect(() => {
    fetchPriceChart(ticker).then((r) => setData(r.data)).catch(() => {});
  }, [ticker]);

  if (!data) {
    return (
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="h-56 flex items-center justify-center text-[12px] text-ink-4">Loading chart...</div>
      </div>
    );
  }

  const points = data.points.map((p) => ({
    ...p,
    dateLabel: p.date.slice(5), // MM-DD
  }));

  return (
    <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <h3 className="text-[13px] font-semibold text-ink">Price · {data.ticker}</h3>
        <span className={`text-[12px] font-mono font-medium ${data.price_return_pct >= 0 ? "text-pos" : "text-breach"}`}>
          {data.price_return_pct > 0 ? "+" : ""}{data.price_return_pct}%
        </span>
        {data.benchmark_return_pct != null && (
          <span className="text-[11px] text-ink-4">
            vs {data.benchmark_name} {data.benchmark_return_pct > 0 ? "+" : ""}{data.benchmark_return_pct}%
          </span>
        )}
        <span className="text-[11px] text-ink-4 ml-auto">{data.events.length} events</span>
      </div>

      {/* Chart */}
      <div
        role="img"
        aria-label={`${data.ticker} price chart over ${data.points.length} bars. ${data.ticker} return ${data.price_return_pct}%${data.benchmark_return_pct != null ? `, ${data.benchmark_name} return ${data.benchmark_return_pct}%` : ""}. ${data.events.length} annotated events.`}
        className="h-56"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart accessibilityLayer data={points} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="oklch(0.94 0.005 240)" strokeDasharray="3 3" vertical={false} />

            {/* Confidence band (area between upper and lower) */}
            <Area
              type="monotone" dataKey="band_upper" stroke="none"
              fill="oklch(0.55 0.15 250)" fillOpacity={0.08}
              isAnimationActive={false}
            />
            <Area
              type="monotone" dataKey="band_lower" stroke="none"
              fill="white" fillOpacity={1}
              isAnimationActive={false}
            />

            <XAxis
              dataKey="dateLabel" tick={{ fontSize: 10, fill: "oklch(0.58 0.01 250)" }}
              tickLine={false} axisLine={false}
              interval={3}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "oklch(0.58 0.01 250)" }}
              tickLine={false} axisLine={false}
              width={40}
              domain={["auto", "auto"]}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                const pt = payload[0]?.payload;
                return (
                  <div className="bg-surface border border-line rounded-lg p-2 shadow-md text-[11px]">
                    <p className="font-mono text-ink-4">{pt?.date}</p>
                    <p className="text-ink font-medium">{data.ticker}: {pt?.price}</p>
                    {pt?.benchmark != null && <p className="text-ink-3">{data.benchmark_name}: {pt.benchmark}</p>}
                  </div>
                );
              }}
            />

            {/* Event markers as reference lines */}
            {data.events.map((ev, i) => (
              <ReferenceLine
                key={i}
                x={ev.date.slice(5)}
                stroke={EVENT_COLOR[ev.kind] || EVENT_COLOR.neutral}
                strokeDasharray="4 3"
                strokeWidth={1.5}
                label={{
                  value: ev.label,
                  position: "top",
                  style: { fontSize: 9, fill: EVENT_COLOR[ev.kind] || EVENT_COLOR.neutral },
                }}
              />
            ))}

            {/* Benchmark line */}
            <Line
              type="monotone" dataKey="benchmark" stroke="oklch(0.72 0.01 250)"
              strokeDasharray="5 3" dot={false} strokeWidth={1.5}
              isAnimationActive={false}
            />

            {/* Price line */}
            <Line
              type="monotone" dataKey="price" stroke="oklch(0.55 0.15 250)"
              dot={false} strokeWidth={2} activeDot={{ r: 4, stroke: "oklch(0.55 0.15 250)", strokeWidth: 2, fill: "white" }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-2 text-[10px] text-ink-3">
        <span className="flex items-center gap-1">
          <span className="w-4 h-0.5 rounded" style={{ background: "oklch(0.55 0.15 250)" }} />
          {data.ticker}
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-0.5 rounded border-t border-dashed" style={{ borderColor: "oklch(0.72 0.01 250)" }} />
          {data.benchmark_name}
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded opacity-20" style={{ background: "oklch(0.55 0.15 250)" }} />
          Confidence band
        </span>
      </div>
    </section>
  );
}
