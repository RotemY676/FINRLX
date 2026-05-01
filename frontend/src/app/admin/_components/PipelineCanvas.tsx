"use client";
import { Fragment } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PipelineStep } from "./PipelineStep";
import { PIPELINE_STEPS } from "./constants";

interface PipelineCanvasProps {
  activeStep: number;
  onStepClick: (idx: number) => void;
  completedSteps: Set<number>;
  counts: number[];
}

function ConnectingLine({ completed }: { completed: boolean }) {
  return (
    <motion.div
      className="hidden md:block flex-1 min-w-[24px] h-[2px] rounded-full relative"
      initial={false}
    >
      {/* Background dashed track */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          backgroundImage: completed
            ? "none"
            : "repeating-linear-gradient(90deg, var(--line) 0, var(--line) 4px, transparent 4px, transparent 8px)",
          backgroundColor: completed ? "transparent" : "transparent",
        }}
      />
      {/* Animated fill */}
      <motion.div
        className="absolute inset-0 rounded-full"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: completed ? 1 : 0 }}
        style={{ originX: 0, backgroundColor: "var(--primary)" }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </motion.div>
  );
}

function ConnectingLineVertical({ completed }: { completed: boolean }) {
  return (
    <motion.div
      className="block md:hidden w-[2px] h-6 mx-auto relative"
      initial={false}
    >
      <div
        className="absolute inset-0 rounded-full"
        style={{
          backgroundImage: completed
            ? "none"
            : "repeating-linear-gradient(180deg, var(--line) 0, var(--line) 4px, transparent 4px, transparent 8px)",
        }}
      />
      <motion.div
        className="absolute inset-0 rounded-full"
        initial={{ scaleY: 0 }}
        animate={{ scaleY: completed ? 1 : 0 }}
        style={{ originY: 0, backgroundColor: "var(--primary)" }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </motion.div>
  );
}

export function PipelineCanvas({
  activeStep,
  onStepClick,
  completedSteps,
  counts,
}: PipelineCanvasProps) {
  return (
    <div className="glass rounded-xl p-4 mb-6">
      {/* Horizontal layout (md+) */}
      <div className="hidden md:flex items-center justify-between gap-2 relative">
        {PIPELINE_STEPS.map((step, i) => (
          <Fragment key={step.key}>
            <PipelineStep
              step={step}
              index={i}
              isActive={activeStep === i}
              isCompleted={completedSteps.has(i)}
              count={counts[i] ?? 0}
              onClick={() => onStepClick(i)}
            />
            {i < PIPELINE_STEPS.length - 1 && (
              <ConnectingLine completed={completedSteps.has(i)} />
            )}
          </Fragment>
        ))}
      </div>

      {/* Vertical layout (below md) */}
      <div className="flex md:hidden flex-col items-center gap-0">
        {PIPELINE_STEPS.map((step, i) => (
          <Fragment key={step.key}>
            <PipelineStep
              step={step}
              index={i}
              isActive={activeStep === i}
              isCompleted={completedSteps.has(i)}
              count={counts[i] ?? 0}
              onClick={() => onStepClick(i)}
            />
            {i < PIPELINE_STEPS.length - 1 && (
              <ConnectingLineVertical completed={completedSteps.has(i)} />
            )}
          </Fragment>
        ))}
      </div>
    </div>
  );
}
