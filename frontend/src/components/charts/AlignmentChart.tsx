"use client";

import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, ZAxis, Cell, ReferenceLine, Label } from "recharts";
import { EngineSignal } from "@/services/api";

const STANCE_X: Record<string, number> = { sell: -1, hold: 0, buy: 1, trim: -0.5 };
const COLOR: Record<string, string> = {
  sell: "oklch(0.58 0.18 25)", hold: "oklch(0.58 0.01 250)", buy: "oklch(0.58 0.13 155)", trim: "oklch(0.72 0.14 75)",
};

interface AlignmentChartProps {
  engines: EngineSignal[];
  synthesisStance?: string;
  synthesisConfidence?: number;
}

export function AlignmentChart({ engines, synthesisStance, synthesisConfidence }: AlignmentChartProps) {
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

  // Synthesis point
  const synthData = synthesisStance ? [{
    name: "Synthesis",
    x: STANCE_X[synthesisStance] ?? 0,
    y: Math.round((synthesisConfidence ?? 0.74) * 100),
    z: 30,
    stance: "synthesis",
  }] : [];

  const stanceBreakdown = engines.reduce<Record<string, number>>((acc, e) => {
    acc[e.stance] = (acc[e.stance] ?? 0) + 1;
    return acc;
  }, {});
  const stanceList = Object.entries(stanceBreakdown).map(([k, v]) => `${v} ${k}`).join(", ");
  const synthText = synthesisStance ? ` Synthesis stance ${synthesisStance} at ${Math.round((synthesisConfidence ?? 0) * 100)}% confidence.` : "";
  const ariaSummary = `Engine alignment bubble chart, ${engines.length} engines (${stanceList}).${synthText}`;

  return (
    <div role="img" aria-label={ariaSummary} className="h-72 relative">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart accessibilityLayer margin={{ top: 16, right: 24, bottom: 32, left: 16 }}>
          {/* Grid reference lines */}
          <ReferenceLine y={25} stroke="oklch(0.92 0.008 240)" strokeDasharray="3 3" />
          <ReferenceLine y={50} stroke="oklch(0.92 0.008 240)" strokeDasharray="3 3" />
          <ReferenceLine y={75} stroke="oklch(0.92 0.008 240)" strokeDasharray="3 3" />
          <ReferenceLine x={0} stroke="oklch(0.88 0.01 240)" />

          <XAxis
            type="number" dataKey="x" domain={[-1.4, 1.4]}
            tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }}
            tickLine={false}
            ticks={[-1, 0, 1]}
            tickFormatter={(v: number) => v === -1 ? "SELL" : v === 0 ? "HOLD" : "BUY"}
            axisLine={{ stroke: "oklch(0.92 0.008 240)" }}
          />
          <YAxis
            type="number" dataKey="y" domain={[20, 100]}
            tick={{ fontSize: 11, fill: "oklch(0.58 0.01 250)" }}
            tickLine={false} axisLine={false}
            ticks={[25, 50, 75, 100]}
            tickFormatter={(v: number) => `${v}%`}
            width={36}
          >
            <Label value="Confidence" angle={-90} position="insideLeft" offset={-4} style={{ fontSize: 10, fill: "oklch(0.58 0.01 250)" }} />
          </YAxis>
          <ZAxis type="number" dataKey="z" range={[100, 500]} />
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
          {/* Engine bubbles */}
          <Scatter data={data} isAnimationActive={false}>
            {data.map((d, i) => (
              <Cell key={i} fill={COLOR[d.stance] || COLOR.hold} fillOpacity={0.75} stroke={COLOR[d.stance] || COLOR.hold} strokeWidth={1.5} />
            ))}
          </Scatter>
          {/* Synthesis point */}
          {synthData.length > 0 && (
            <Scatter data={synthData} shape="diamond" isAnimationActive={false}>
              <Cell fill="oklch(0.55 0.15 250)" fillOpacity={0.9} stroke="oklch(0.45 0.18 250)" strokeWidth={2} />
            </Scatter>
          )}
        </ScatterChart>
      </ResponsiveContainer>

      {/* Engine name labels overlaid */}
      <div className="absolute bottom-10 left-16 right-6 flex justify-between pointer-events-none">
        {engines.map((e) => (
          <span key={e.engine_key} className="text-[9px] font-mono text-ink-4 bg-surface/80 px-1 rounded">
            {e.engine_name.split(" ")[0]}
          </span>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-1 text-[10px] text-ink-3 justify-center">
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: COLOR.buy }} /> Buy</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: COLOR.hold }} /> Hold</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{ background: COLOR.sell }} /> Sell</span>
        {synthData.length > 0 && (
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rotate-45" style={{ background: "oklch(0.55 0.15 250)" }} /> Synthesis</span>
        )}
      </div>
    </div>
  );
}
