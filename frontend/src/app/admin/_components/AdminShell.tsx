"use client";

import { useMemo, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../_context/AdminContext";
import { PipelineCanvas } from "./PipelineCanvas";
import { StepExplainer } from "./StepExplainer";
import { PIPELINE_STEPS } from "./constants";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";

// Lazy import step panels
import { DatasetExportPanel } from "./steps/DatasetExportPanel";
import { ExperimentPanel } from "./steps/ExperimentPanel";
import { ComparisonPanel } from "./steps/ComparisonPanel";
import { ReadinessPanel } from "./steps/ReadinessPanel";
import { PublicationQueuePanel } from "./steps/PublicationQueuePanel";

// Import wizard
import { ResearchWizardModal } from "./wizard/ResearchWizardModal";

import { CommandPalette } from "./CommandPalette";
import { IncidentDrawer } from "@/components/ops/IncidentDrawer";

const STEP_PANELS = [
  DatasetExportPanel,
  ExperimentPanel,
  ComparisonPanel,
  ReadinessPanel,
  PublicationQueuePanel,
];

export function AdminShell() {
  const {
    loading, error, ops, activeStep, setActiveStep,
    pipelineIds, dsExportHistory, expList, cmpList, rdList,
    drawerIncident, setDrawerIncident,
  } = useAdmin();

  /* ── Wizard open callback for CommandPalette ── */
  const [wizardOpenFn, setWizardOpenFn] = useState<(() => void) | null>(null);
  const handleRegisterWizardOpen = useCallback((fn: () => void) => {
    setWizardOpenFn(() => fn);
  }, []);

  // Determine which steps are "completed" (have at least one item)
  const completedSteps = useMemo(() => {
    const set = new Set<number>();
    if (dsExportHistory.length > 0) set.add(0);
    if (expList.length > 0) set.add(1);
    if (cmpList.length > 0) set.add(2);
    if (rdList.length > 0) set.add(3);
    // Safety/Ops is always "available"
    return set;
  }, [dsExportHistory, expList, cmpList, rdList]);

  const counts = [dsExportHistory.length, expList.length, cmpList.length, rdList.length, 0];

  if (loading) return <PageLoading label="Loading Ops Command Center..." />;
  if (error) return <PageError title="Ops Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!ops) return null;

  const ActivePanel = STEP_PANELS[activeStep];
  const activeStepMeta = PIPELINE_STEPS[activeStep];

  return (
    <div className="space-y-4 max-w-[1400px] px-4 md:px-0">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[20px] font-semibold text-ink">Ops Command Center</h1>
          <p className="text-[12px] text-ink-3 mt-0.5">
            Research workflow pipeline with governed data exports, experiments, comparisons, and readiness reviews.
          </p>
        </div>
        <button
          onClick={() => {
            const evt = new KeyboardEvent("keydown", { key: "k", metaKey: true, ctrlKey: true });
            document.dispatchEvent(evt);
          }}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-2 border border-surface-3 text-ink-3 hover:text-ink hover:border-ink-3 transition-colors shrink-0 mt-1"
          title="Open command palette"
        >
          <span className="text-[11px] font-mono font-medium">&#8984;K</span>
        </button>
      </div>

      {/* Pipeline Canvas */}
      <PipelineCanvas
        activeStep={activeStep}
        onStepClick={setActiveStep}
        completedSteps={completedSteps}
        counts={counts}
      />

      {/* Step Explainer */}
      <AnimatePresence mode="wait">
        <StepExplainer
          key={activeStepMeta.key}
          step={activeStepMeta}
          stepIndex={activeStep}
        />
      </AnimatePresence>

      {/* Active Step Panel */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeStepMeta.key}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          <ActivePanel />
        </motion.div>
      </AnimatePresence>

      {/* Wizard Modal - renders when open */}
      <ResearchWizardModal onRegisterOpen={handleRegisterWizardOpen} />

      {/* Command Palette (Cmd+K) */}
      <CommandPalette onOpenWizard={wizardOpenFn ?? (() => {})} />

      {/* Incident Drawer */}
      {drawerIncident && (
        <IncidentDrawer incident={drawerIncident} onClose={() => setDrawerIncident(null)} />
      )}
    </div>
  );
}
