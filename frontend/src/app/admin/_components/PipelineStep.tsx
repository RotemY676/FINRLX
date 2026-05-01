"use client";
import { motion } from "framer-motion";
import { Icon } from "@/components/icons/Icon";

interface StepDef {
  key: string;
  label: string;
  icon: string;
  description: string;
}

interface PipelineStepProps {
  step: StepDef;
  index: number;
  isActive: boolean;
  isCompleted: boolean;
  count: number;
  onClick: () => void;
}

const pulseGlow = {
  initial: { boxShadow: "0 0 0 0 rgba(var(--primary-rgb, 99 102 241), 0)" },
  animate: {
    boxShadow: [
      "0 0 0 0 rgba(var(--primary-rgb, 99 102 241), 0.4)",
      "0 0 12px 4px rgba(var(--primary-rgb, 99 102 241), 0.15)",
      "0 0 0 0 rgba(var(--primary-rgb, 99 102 241), 0)",
    ],
    transition: { duration: 2, repeat: Infinity, ease: "easeInOut" as const },
  },
};

export function PipelineStep({
  step,
  index,
  isActive,
  isCompleted,
  count,
  onClick,
}: PipelineStepProps) {
  const borderColor = isCompleted
    ? "border-pos"
    : isActive
      ? "border-primary"
      : "border-line";

  const bgColor = isCompleted
    ? "bg-pos/10"
    : isActive
      ? "bg-primary/10"
      : "bg-surface-2";

  return (
    <motion.button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center gap-1.5 relative z-10 min-w-0 flex-shrink-0"
      whileHover={{ scale: 1.06 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
    >
      {/* Radial glow behind active step */}
      {isActive && (
        <motion.div
          className="absolute -inset-3 rounded-full bg-primary/10 blur-lg pointer-events-none"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.5 }}
          transition={{ duration: 0.3 }}
        />
      )}

      {/* Circle container */}
      <motion.div
        className={`relative w-10 h-10 rounded-full border-2 ${borderColor} ${bgColor} flex items-center justify-center`}
        variants={isActive ? pulseGlow : undefined}
        initial="initial"
        animate={isActive ? "animate" : "initial"}
      >
        <Icon
          name={step.icon}
          size={18}
          className={
            isCompleted
              ? "text-pos"
              : isActive
                ? "text-primary"
                : "text-ink-3"
          }
        />

        {/* Completed checkmark overlay */}
        {isCompleted && (
          <motion.div
            className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-pos flex items-center justify-center"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 25 }}
          >
            <Icon name="check" size={10} className="text-white" strokeWidth={3} />
          </motion.div>
        )}
      </motion.div>

      {/* Label */}
      <span
        className={`text-[11px] leading-tight text-center whitespace-nowrap ${
          isActive ? "text-primary font-semibold" : isCompleted ? "text-pos" : "text-ink-3"
        }`}
      >
        {step.label}
      </span>

      {/* Count badge */}
      {count > 0 && (
        <motion.span
          className="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-surface-3 text-ink-2 leading-none"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, type: "spring", stiffness: 500, damping: 25 }}
        >
          {count}
        </motion.span>
      )}
    </motion.button>
  );
}
