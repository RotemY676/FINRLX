"use client";
import { motion, AnimatePresence } from "framer-motion";
import { Icon } from "@/components/icons/Icon";

interface StepDef {
  key: string;
  label: string;
  icon: string;
  description: string;
}

interface StepExplainerProps {
  step: StepDef;
  stepIndex: number;
}

/* ---------- Animated SVG visuals per step ---------- */

function DataFlowVisual() {
  // Dots flowing into a grid pattern
  const dots = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    cx: 20 + (i % 4) * 24,
    cy: 16 + Math.floor(i / 4) * 24,
  }));

  return (
    <svg viewBox="0 0 120 90" className="w-full h-full" fill="none">
      {dots.map((dot, i) => (
        <motion.circle
          key={dot.id}
          cx={dot.cx}
          cy={dot.cy}
          r={3}
          fill="var(--primary)"
          initial={{ opacity: 0, cx: 0, cy: 45 }}
          animate={{ opacity: [0, 1, 1], cx: dot.cx, cy: dot.cy }}
          transition={{
            duration: 1.2,
            delay: i * 0.1,
            repeat: Infinity,
            repeatDelay: 2,
            ease: "easeOut",
          }}
        />
      ))}
      {/* Grid lines */}
      {[0, 1, 2].map((r) => (
        <motion.line
          key={`h${r}`}
          x1={14}
          y1={16 + r * 24}
          x2={110}
          y2={16 + r * 24}
          stroke="var(--line)"
          strokeWidth={0.5}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
        />
      ))}
      {[0, 1, 2, 3].map((c) => (
        <motion.line
          key={`v${c}`}
          x1={20 + c * 24}
          y1={10}
          x2={20 + c * 24}
          y2={70}
          stroke="var(--line)"
          strokeWidth={0.5}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
        />
      ))}
    </svg>
  );
}

function SineWaveVisual() {
  // Animated sine wave representing model training
  const points = Array.from({ length: 50 }, (_, i) => {
    const x = (i / 49) * 140;
    const y = 45 + Math.sin((i / 49) * Math.PI * 4) * 20;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg viewBox="0 0 140 90" className="w-full h-full" fill="none">
      <motion.polyline
        points={points}
        stroke="var(--primary)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 2, repeat: Infinity, repeatDelay: 1, ease: "easeInOut" }}
      />
      <motion.polyline
        points={points}
        stroke="var(--primary)"
        strokeWidth={2}
        strokeLinecap="round"
        fill="none"
        opacity={0.2}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, delay: 0.3, repeat: Infinity, repeatDelay: 1, ease: "easeInOut" }}
        transform="translate(0, 6)"
      />
    </svg>
  );
}

function CompareVisual() {
  // Two bar charts side by side
  const barsA = [30, 55, 40, 65, 50];
  const barsB = [45, 35, 60, 40, 55];

  return (
    <svg viewBox="0 0 140 90" className="w-full h-full" fill="none">
      {barsA.map((h, i) => (
        <motion.rect
          key={`a${i}`}
          x={8 + i * 14}
          y={80 - h}
          width={5}
          height={h}
          rx={1}
          fill="var(--primary)"
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.6, delay: i * 0.1, repeat: Infinity, repeatDelay: 3, ease: "backOut" }}
          style={{ originY: "100%" }}
        />
      ))}
      {barsB.map((h, i) => (
        <motion.rect
          key={`b${i}`}
          x={78 + i * 14}
          y={80 - h}
          width={5}
          height={h}
          rx={1}
          fill="var(--accent)"
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.6, delay: 0.3 + i * 0.1, repeat: Infinity, repeatDelay: 3, ease: "backOut" }}
          style={{ originY: "100%" }}
        />
      ))}
      {/* Divider line */}
      <line x1={70} y1={10} x2={70} y2={85} stroke="var(--line)" strokeWidth={0.5} strokeDasharray="3 3" />
    </svg>
  );
}

function ReadinessVisual() {
  // Circular progress ring filling up
  const radius = 30;
  const circumference = 2 * Math.PI * radius;

  return (
    <svg viewBox="0 0 90 90" className="w-full h-full" fill="none">
      {/* Track */}
      <circle cx={45} cy={45} r={radius} stroke="var(--line)" strokeWidth={4} fill="none" />
      {/* Progress */}
      <motion.circle
        cx={45}
        cy={45}
        r={radius}
        stroke="var(--pos)"
        strokeWidth={4}
        fill="none"
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: circumference * 0.15 }}
        transition={{ duration: 2.5, repeat: Infinity, repeatDelay: 1, ease: "easeInOut" }}
        transform="rotate(-90 45 45)"
      />
      {/* Percentage text */}
      <motion.text
        x={45}
        y={48}
        textAnchor="middle"
        fill="var(--ink)"
        fontSize={14}
        fontWeight={600}
        fontFamily="var(--font-mono)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <motion.tspan
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 1] }}
          transition={{ duration: 2.5, repeat: Infinity, repeatDelay: 1 }}
        >
          85%
        </motion.tspan>
      </motion.text>
    </svg>
  );
}

function HeartbeatVisual() {
  // Heartbeat-like pulse line
  const path =
    "M 0,45 L 20,45 L 28,45 L 32,20 L 36,65 L 40,30 L 44,55 L 48,45 L 60,45 L 68,45 L 72,20 L 76,65 L 80,30 L 84,55 L 88,45 L 140,45";

  return (
    <svg viewBox="0 0 140 90" className="w-full h-full" fill="none">
      <motion.path
        d={path}
        stroke="var(--breach)"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1.5, repeat: Infinity, repeatDelay: 0.5, ease: "linear" }}
      />
      {/* Fading trail */}
      <motion.path
        d={path}
        stroke="var(--breach)"
        strokeWidth={1.5}
        strokeLinecap="round"
        fill="none"
        opacity={0.15}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.5, delay: 0.2, repeat: Infinity, repeatDelay: 0.5, ease: "linear" }}
      />
    </svg>
  );
}

const STEP_VISUALS: Record<string, () => JSX.Element> = {
  "research-data": DataFlowVisual,
  experiments: SineWaveVisual,
  comparisons: CompareVisual,
  readiness: ReadinessVisual,
  safety: HeartbeatVisual,
};

/* ---------- Stagger text animation ---------- */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.03 },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

const charVariants = {
  hidden: { opacity: 0, y: 4 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.05 } },
};

function TypewriterText({ text }: { text: string }) {
  return (
    <motion.span
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="inline"
    >
      {text.split("").map((char, i) => (
        <motion.span key={i} variants={charVariants}>
          {char}
        </motion.span>
      ))}
    </motion.span>
  );
}

/* ---------- Main component ---------- */

export function StepExplainer({ step, stepIndex }: StepExplainerProps) {
  const Visual = STEP_VISUALS[step.key] ?? DataFlowVisual;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step.key}
        className="glass rounded-xl p-5 mb-6 overflow-hidden"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <div className="flex flex-col md:flex-row items-start gap-6">
          {/* Left: text content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              {/* Large semi-transparent step number */}
              <span className="text-4xl font-display font-bold text-ink/10 leading-none select-none">
                {stepIndex + 1}
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <Icon name={step.icon} size={16} className="text-primary" />
                  <h3 className="text-sm font-semibold text-ink">{step.label}</h3>
                </div>
              </div>
            </div>
            <p className="text-sm text-ink-3 leading-relaxed mt-1">
              <TypewriterText text={step.description} />
            </p>
          </div>

          {/* Right: animated visual */}
          <div className="w-full md:w-40 h-24 flex-shrink-0 flex items-center justify-center">
            <Visual />
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
