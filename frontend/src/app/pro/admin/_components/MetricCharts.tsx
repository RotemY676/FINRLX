"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import {
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

/* ================================================================== */
/*  Shared                                                             */
/* ================================================================== */

const ANIM_WRAPPER = {
  initial: { opacity: 0, scale: 0.92 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.4, ease: "easeOut" as const },
};

function NoData({ message = "No data" }: { message?: string }) {
  return (
    <div className="flex items-center justify-center text-ink-3 text-sm h-full min-h-[80px]">
      {message}
    </div>
  );
}

/* ================================================================== */
/*  1. ExportCoverageChart                                             */
/* ================================================================== */

interface ExportCoverageChartProps {
  features: boolean;
  targets: boolean;
  warnings: boolean;
  rowCount: number;
}

const COVERAGE_COLORS = [
  "var(--primary, #6366f1)",
  "var(--pos, #22c55e)",
  "var(--caution, #eab308)",
  "var(--surface-3, #334155)",
];

export function ExportCoverageChart({
  features,
  targets,
  warnings,
  rowCount,
}: ExportCoverageChartProps) {
  const segments = useMemo(() => {
    const items = [
      { name: "Features", value: features ? 1 : 0 },
      { name: "Targets", value: targets ? 1 : 0 },
      { name: "Warnings", value: warnings ? 1 : 0 },
    ];
    const present = items.filter((i) => i.value > 0);
    const absent = items.filter((i) => i.value === 0);

    if (present.length === 0) {
      return [{ name: "Empty", value: 1, color: COVERAGE_COLORS[3] }];
    }

    const result = present.map((p, i) => ({
      ...p,
      value: 1,
      color: COVERAGE_COLORS[i % COVERAGE_COLORS.length],
    }));
    if (absent.length > 0) {
      result.push({
        name: "Missing",
        value: absent.length,
        color: COVERAGE_COLORS[3],
      });
    }
    return result;
  }, [features, targets, warnings]);

  return (
    <motion.div {...ANIM_WRAPPER} className="relative" style={{ width: 120, height: 120 }}>
      <PieChart width={120} height={120}>
        <Pie
          data={segments}
          cx={55}
          cy={55}
          innerRadius={32}
          outerRadius={50}
          dataKey="value"
          stroke="none"
          isAnimationActive
        >
          {segments.map((s, i) => (
            <Cell key={i} fill={s.color} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number, name: string) =>
            name === "Missing" ? [`${value} missing`, name] : ["Included", name]
          }
        />
      </PieChart>
      {/* Center text */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
        style={{ top: 0, left: 0, width: 120, height: 120 }}
      >
        <span className="text-xs font-bold text-ink">{rowCount.toLocaleString()}</span>
        <span className="text-[9px] text-ink-3">rows</span>
      </div>
    </motion.div>
  );
}

/* ================================================================== */
/*  2. ExperimentMetricsChart                                          */
/* ================================================================== */

interface ExperimentMetricsChartProps {
  experiments: Array<{
    id: string;
    name: string;
    metrics: Record<string, number>;
  }>;
}

const RADAR_COLORS = [
  "var(--primary, #6366f1)",
  "var(--pos, #22c55e)",
  "var(--caution, #eab308)",
  "var(--breach, #ef4444)",
  "#8b5cf6",
  "#06b6d4",
];

export function ExperimentMetricsChart({ experiments }: ExperimentMetricsChartProps) {
  /* Collect all metric keys across experiments */
  const metricKeys = useMemo(() => {
    if (!experiments || experiments.length === 0) return [];
    const keys = new Set<string>();
    experiments.forEach((exp) => {
      Object.keys(exp.metrics).forEach((k) => keys.add(k));
    });
    return Array.from(keys);
  }, [experiments]);

  /* Normalize metrics to 0-1 range for radar */
  const { data, ranges } = useMemo(() => {
    if (!experiments || experiments.length === 0 || metricKeys.length === 0) {
      return { data: [], ranges: { mins: {}, maxs: {} } };
    }
    const mins: Record<string, number> = {};
    const maxs: Record<string, number> = {};

    metricKeys.forEach((k) => {
      const vals = experiments.map((e) => e.metrics[k] ?? 0);
      mins[k] = Math.min(...vals);
      maxs[k] = Math.max(...vals);
    });

    const rows = metricKeys.map((k) => {
      const row: Record<string, string | number> = { metric: k };
      experiments.forEach((exp) => {
        const raw = exp.metrics[k] ?? 0;
        const range = maxs[k] - mins[k];
        row[exp.id] = range > 0 ? ((raw - mins[k]) / range) * 100 : 50;
        row[`${exp.id}_raw`] = raw;
      });
      return row;
    });

    return { data: rows, ranges: { mins, maxs } };
  }, [experiments, metricKeys]);

  if (!experiments || experiments.length === 0) {
    return <NoData message="No experiments to compare" />;
  }

  if (metricKeys.length === 0) {
    return <NoData message="No metrics available" />;
  }

  return (
    <motion.div {...ANIM_WRAPPER} className="w-full">
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data}>
          <PolarGrid stroke="var(--ink-3, #64748b)" strokeOpacity={0.3} />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fontSize: 10, fill: "var(--ink-2, #94a3b8)" }}
          />
          <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
          {experiments.map((exp, i) => (
            <Radar
              key={exp.id}
              name={exp.name}
              dataKey={exp.id}
              stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
              fill={RADAR_COLORS[i % RADAR_COLORS.length]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
          ))}
          <Tooltip
            content={({ payload, label }) => {
              if (!payload || payload.length === 0) return null;
              return (
                <div className="glass rounded-lg p-2 text-xs shadow-lg border border-white/10">
                  <p className="font-semibold text-ink mb-1">{label}</p>
                  {payload.map((p: any) => {
                    const rawKey = `${p.dataKey}_raw`;
                    const rawVal =
                      p.payload[rawKey] !== undefined
                        ? Number(p.payload[rawKey]).toFixed(4)
                        : "N/A";
                    return (
                      <p key={p.dataKey} style={{ color: p.color }}>
                        {p.name}: {rawVal}
                      </p>
                    );
                  })}
                </div>
              );
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11 }}
            iconType="circle"
            iconSize={8}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

/* ================================================================== */
/*  3. ReadinessProgressRing                                           */
/* ================================================================== */

interface ReadinessProgressRingProps {
  completed: number;
  total: number;
  size?: number;
}

export function ReadinessProgressRing({
  completed,
  total,
  size = 100,
}: ReadinessProgressRingProps) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - pct / 100);

  const color =
    pct > 80
      ? "var(--pos, #22c55e)"
      : pct > 50
        ? "var(--caution, #eab308)"
        : "var(--breach, #ef4444)";

  return (
    <motion.div
      {...ANIM_WRAPPER}
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-3, #334155)"
          strokeWidth={6}
          strokeOpacity={0.4}
        />
        {/* Progress ring */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-lg font-bold"
          style={{ color }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {pct}%
        </motion.span>
        <span className="text-[9px] text-ink-3">
          {completed}/{total}
        </span>
      </div>
    </motion.div>
  );
}

/* ================================================================== */
/*  4. BenchmarkComparisonChart                                        */
/* ================================================================== */

interface BenchmarkComparisonChartProps {
  metricsByAgent: Record<
    string,
    {
      total_return?: number;
      total_reward?: number;
      max_drawdown?: number;
    }
  >;
}

export function BenchmarkComparisonChart({
  metricsByAgent,
}: BenchmarkComparisonChartProps) {
  const data = useMemo(() => {
    if (!metricsByAgent || Object.keys(metricsByAgent).length === 0) return [];

    return Object.entries(metricsByAgent)
      .map(([agent, metrics]) => ({
        agent,
        total_return: metrics.total_return ?? 0,
        total_reward: metrics.total_reward ?? 0,
        max_drawdown: metrics.max_drawdown ?? 0,
      }))
      .sort((a, b) => b.total_return - a.total_return);
  }, [metricsByAgent]);

  if (data.length === 0) {
    return <NoData message="No benchmark data" />;
  }

  return (
    <motion.div {...ANIM_WRAPPER} className="w-full">
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 50 + 60)}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--ink-3, #64748b)"
            strokeOpacity={0.15}
          />
          <XAxis type="number" tick={{ fontSize: 10, fill: "var(--ink-2, #94a3b8)" }} />
          <YAxis
            dataKey="agent"
            type="category"
            tick={{ fontSize: 10, fill: "var(--ink-2, #94a3b8)" }}
            width={100}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface-2, #1e293b)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              fontSize: 11,
            }}
            itemStyle={{ color: "var(--ink, #e2e8f0)" }}
            formatter={(value: number) => value.toFixed(4)}
          />
          <Legend
            wrapperStyle={{ fontSize: 11 }}
            iconType="circle"
            iconSize={8}
          />
          <Bar
            dataKey="total_return"
            name="Return"
            fill="var(--primary, #6366f1)"
            radius={[0, 4, 4, 0]}
            barSize={12}
          />
          <Bar
            dataKey="total_reward"
            name="Reward"
            fill="var(--accent, #8b5cf6)"
            radius={[0, 4, 4, 0]}
            barSize={12}
          />
          <Bar
            dataKey="max_drawdown"
            name="Drawdown"
            fill="var(--caution, #eab308)"
            radius={[0, 4, 4, 0]}
            barSize={12}
          />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
