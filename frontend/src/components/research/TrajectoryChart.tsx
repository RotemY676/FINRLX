"use client";

/**
 * Phase 18.6.1 — Trajectory chart for the cross-quarter insights panel.
 *
 * Visualizes the structured `metrics` block emitted by the LLM as one
 * small line chart per metric, stacked vertically. Each metric carries
 * its own unit (USD millions, %, etc.) which becomes the Y-axis label,
 * so we don't need a shared scale across metrics — each chart is
 * independent and readable.
 *
 * Visual language matches PriceChartCard:
 *   - Same rounded-lg / border-line / bg-surface card frame
 *   - Same axis tick font and color (oklch values)
 *   - Same CartesianGrid stroke pattern
 *
 * Falls back to nothing (returns null) when `metrics` is null or
 * empty. The InsightsPanel renders narrative-only mode in that case.
 */
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface MetricQuarter {
  period_end: string;
  label: string;
  value: number;
}

interface Metric {
  name: string;
  unit: string;
  quarters: MetricQuarter[];
}

export interface TrajectoryMetricsData {
  metrics: Metric[];
}

interface Props {
  data: TrajectoryMetricsData;
}

// Color rotation — cycled across metrics. oklch values match the
// FINRLX palette used elsewhere on the dashboard.
const METRIC_COLORS = [
  "oklch(0.55 0.18 250)", // blue
  "oklch(0.58 0.13 155)", // green
  "oklch(0.65 0.16 70)",  // amber
  "oklch(0.58 0.18 25)",  // red
];

/** Compact number formatter — drops trailing zeros, picks a sensible
 *  precision based on magnitude. Used both on the Y-axis ticks and in
 *  the tooltip. */
function formatNumber(value: number, unit: string): string {
  if (!Number.isFinite(value)) return "—";
  const isPercent = unit.includes("%");
  if (isPercent) {
    return `${value.toFixed(1)}%`;
  }
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  if (abs >= 100) return value.toFixed(0);
  if (abs >= 10) return value.toFixed(1);
  return value.toFixed(2);
}

export function TrajectoryChart({ data }: Props) {
  const metrics = data?.metrics ?? [];
  if (metrics.length === 0) return null;

  return (
    <div className="space-y-4">
      {metrics.map((metric, idx) => {
        const color = METRIC_COLORS[idx % METRIC_COLORS.length];
        // Recharts wants an array of points; our shape already matches
        // except for the dataKey naming — we just point Line at "value".
        const points = metric.quarters;

        return (
          <div
            key={metric.name}
            className="rounded-md border border-line bg-surface-2 p-3"
          >
            <div className="flex items-baseline gap-2 mb-2">
              <h4 className="text-[13px] font-semibold text-ink">
                {metric.name}
              </h4>
              <span className="text-[11px] text-ink-4 font-mono">
                {metric.unit}
              </span>
              {points.length > 1 && (
                <span
                  className={`text-[11px] font-mono font-medium ml-auto ${
                    points[points.length - 1].value >= points[0].value
                      ? "text-pos"
                      : "text-breach"
                  }`}
                  aria-label="Period-over-period change"
                >
                  {points[points.length - 1].value >= points[0].value ? "▲" : "▼"}{" "}
                  {formatNumber(
                    Math.abs(
                      points[points.length - 1].value - points[0].value,
                    ),
                    metric.unit,
                  )}{" "}
                  over {points.length} quarters
                </span>
              )}
            </div>

            <div
              role="img"
              aria-label={`${metric.name} trajectory: ${points
                .map((p) => `${p.label} ${formatNumber(p.value, metric.unit)}`)
                .join(", ")}`}
              className="h-32"
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={points}
                  margin={{ top: 8, right: 12, bottom: 4, left: 0 }}
                >
                  <CartesianGrid
                    stroke="oklch(0.94 0.005 240)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 10, fill: "oklch(0.58 0.01 250)" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "oklch(0.58 0.01 250)" }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => formatNumber(v, metric.unit)}
                    width={48}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--surface, #fff)",
                      border: "1px solid oklch(0.88 0.01 250)",
                      borderRadius: 6,
                      fontSize: 12,
                      padding: "6px 8px",
                    }}
                    labelStyle={{ color: "oklch(0.45 0.02 250)", fontSize: 11 }}
                    formatter={(value: number) => [
                      formatNumber(value, metric.unit),
                      metric.name,
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={color}
                    strokeWidth={2}
                    dot={{ r: 3, fill: color, strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: color, strokeWidth: 0 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      })}
    </div>
  );
}
