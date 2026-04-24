"use client";

import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, ZAxis, Cell } from "recharts";
import { EngineSignal } from "@/services/api";

const STANCE_X: Record<string, number> = { sell: -1, hold: 0, buy: 1, trim: -0.5 };
const COLOR: Record<string, string> = {
  sell: "oklch(0.58 0.18 25)", hold: "oklch(0.58 0.01 250)", buy: "oklch(0.58 0.13 155)", trim: "oklch(0.72 0.14 75)",
};

export function AlignmentChart({ engines }: { engines: EngineSignal[] }) {
  if (engines.length === 0) {
    return <div className="h-48 flex items-center justify-center text-[13px] text-ink-3">No engine data.</div>;
  }

  const data = engines.map((e) => ({
    name: e.engine_name,
    x: STANCE_X[e.stance] ?? 0,
    y: Math.round(e.confidence * 100),
    z: Math.round(e.weight * 100),
    stance: e.stance,
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
          <XAxis
            type="number" dataKey="x" domain={[-1.3, 1.3]}
            tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }}
            tickLine={false}
            ticks={[-1, 0, 1]}
            tickFormatter={(v) => v === -1 ? "Sell" : v === 0 ? "Hold" : "Buy"}
            axisLine={{ stroke: "oklch(0.92 0.008 240)" }}
            label={{ value: "Stance", position: "bottom", offset: 8, style: { fontSize: 11, fill: "oklch(0.58 0.01 250)" } }}
          />
          <YAxis
            type="number" dataKey="y" domain={[30, 100]}
            tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }}
            tickLine={false} axisLine={false}
            tickFormatter={(v) => `${v}%`}
            width={36}
            label={{ value: "Confidence", angle: -90, position: "insideLeft", offset: 4, style: { fontSize: 11, fill: "oklch(0.58 0.01 250)" } }}
          />
          <ZAxis type="number" dataKey="z" range={[80, 400]} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null;
              const d = payload[0].payload;
              return (
                <div className="bg-surface border border-line rounded-lg p-2 shadow-md text-[12px]">
                  <p className="font-semibold text-ink">{d.name}</p>
                  <p className="text-ink-2">Stance: {d.stance} · Confidence: {d.y}% · Weight: {d.z}%</p>
                </div>
              );
            }}
          />
          <Scatter data={data}>
            {data.map((d, i) => (
              <Cell key={i} fill={COLOR[d.stance] || COLOR.hold} fillOpacity={0.8} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
