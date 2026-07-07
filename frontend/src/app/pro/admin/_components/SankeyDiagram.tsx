"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface SankeyDiagramProps {
  counts: {
    universe?: number;
    exports: number;
    experiments: number;
    comparisons: number;
    readiness: number;
  };
  className?: string;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const NODE_HEIGHT = 48;
const NODE_WIDTH = 130;
const NODE_RX = 10;
const MIN_PATH_WIDTH = 4;
const MAX_PATH_WIDTH = 28;

const STAGES: {
  key: keyof SankeyDiagramProps["counts"];
  label: string;
  color: string;
  fillOpacity: number;
}[] = [
  { key: "universe", label: "Universe", color: "var(--ink-3, #94a3b8)", fillOpacity: 1 },
  { key: "exports", label: "Exports", color: "var(--primary, #6366f1)", fillOpacity: 0.6 },
  { key: "experiments", label: "Experiments", color: "var(--primary, #6366f1)", fillOpacity: 0.7 },
  { key: "comparisons", label: "Comparisons", color: "var(--primary, #6366f1)", fillOpacity: 0.8 },
  { key: "readiness", label: "Readiness", color: "var(--primary, #6366f1)", fillOpacity: 0.9 },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function cubicBezierPath(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): string {
  const cx = (x1 + x2) / 2;
  return `M ${x1},${y1} C ${cx},${y1} ${cx},${y2} ${x2},${y2}`;
}

/* ------------------------------------------------------------------ */
/*  Animated counter                                                   */
/* ------------------------------------------------------------------ */

function AnimatedCount({ value }: { value: number }) {
  return (
    <motion.tspan
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      {value.toLocaleString()}
    </motion.tspan>
  );
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function SankeyDiagram({ counts, className = "" }: SankeyDiagramProps) {
  const stages = useMemo(() => {
    return STAGES.map((s) => ({
      ...s,
      count: counts[s.key] ?? 0,
    }));
  }, [counts]);

  const maxCount = Math.max(...stages.map((s) => s.count), 1);

  /* Responsive SVG layout */
  const gap = 60;
  const padding = 16;
  const totalWidth =
    padding * 2 + STAGES.length * NODE_WIDTH + (STAGES.length - 1) * gap;
  const totalHeight = NODE_HEIGHT + 60; // room for labels above

  const nodeY = 36; // vertical offset for the nodes

  return (
    <div className={`w-full overflow-x-auto ${className}`}>
      <svg
        viewBox={`0 0 ${totalWidth} ${totalHeight}`}
        className="w-full"
        style={{ minWidth: 520, maxHeight: 120 }}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* ── Connecting paths ── */}
        {stages.map((stage, i) => {
          if (i === 0) return null;
          const prev = stages[i - 1];
          const x1 = padding + i * (NODE_WIDTH + gap) - gap;
          const x2 = padding + i * (NODE_WIDTH + gap);
          const cy = nodeY + NODE_HEIGHT / 2;

          const ratio = Math.max(stage.count / maxCount, 0.08);
          const pathWidth =
            MIN_PATH_WIDTH + (MAX_PATH_WIDTH - MIN_PATH_WIDTH) * ratio;
          const opacity = 0.15 + 0.45 * ratio;

          return (
            <motion.path
              key={`path-${i}`}
              d={cubicBezierPath(x1, cy, x2, cy)}
              fill="none"
              stroke={stage.color}
              strokeWidth={pathWidth}
              strokeOpacity={opacity}
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{
                duration: 0.8,
                delay: i * 0.15,
                ease: "easeInOut",
              }}
            />
          );
        })}

        {/* ── Nodes ── */}
        {stages.map((stage, i) => {
          const x = padding + i * (NODE_WIDTH + gap);
          const y = nodeY;

          return (
            <motion.g
              key={stage.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
            >
              {/* Node rect */}
              <rect
                x={x}
                y={y}
                width={NODE_WIDTH}
                height={NODE_HEIGHT}
                rx={NODE_RX}
                fill={stage.color}
                fillOpacity={stage.fillOpacity}
                stroke={stage.color}
                strokeWidth={1.5}
                strokeOpacity={0.3}
              />

              {/* Label */}
              <text
                x={x + NODE_WIDTH / 2}
                y={y + 19}
                textAnchor="middle"
                className="fill-current"
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  fill: "#fff",
                }}
              >
                {stage.label}
              </text>

              {/* Count */}
              <text
                x={x + NODE_WIDTH / 2}
                y={y + 36}
                textAnchor="middle"
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  fill: "#fff",
                }}
              >
                <AnimatedCount value={stage.count} />
              </text>
            </motion.g>
          );
        })}
      </svg>
    </div>
  );
}
