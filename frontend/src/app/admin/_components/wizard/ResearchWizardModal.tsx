"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../../_context/AdminContext";
import {
  createFinrlxDatasetExport,
  verifyFinrlxDatasetExport,
  createFinrlxResearchExperiment,
  importFinrlxResearchExperimentResults,
  verifyFinrlxResearchExperiment,
  createFinrlxExperimentComparison,
  verifyFinrlxExperimentComparison,
  createFinrlxResearchReadiness,
  updateFinrlxResearchReadinessState,
  verifyFinrlxResearchReadiness,
  type ReadinessState,
} from "@/services/api";

/* ------------------------------------------------------------------ */
/*  ResearchWizardModal                                                */
/*  Self-contained wizard with trigger button + modal overlay.         */
/*  All wizard state is local; shared data comes from useAdmin().      */
/* ------------------------------------------------------------------ */

interface ResearchWizardModalProps {
  onRegisterOpen?: (openFn: () => void) => void;
}

export function ResearchWizardModal({ onRegisterOpen }: ResearchWizardModalProps = {}) {
  const {
    dsExportHistory,
    expList,
    cmpList,
    rdList,
    refreshExportHistory,
    refreshExperiments,
    refreshComparisons,
    refreshReadiness,
    setPipelineId,
    setActiveStep,
  } = useAdmin();

  /* ── wizard open / step ── */
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);

  /* ── Register open function for external callers (e.g. CommandPalette) ── */
  useEffect(() => {
    if (onRegisterOpen) {
      onRegisterOpen(() => setWizardOpen(true));
    }
  }, [onRegisterOpen]);

  /* ── selected IDs ── */
  const [wzExportId, setWzExportId] = useState("");
  const [wzExpIds, setWzExpIds] = useState<string[]>([]);
  const [wzCmpId, setWzCmpId] = useState("");
  const [wzRdId, setWzRdId] = useState("");

  /* ── Step 1 form: create export ── */
  const [wzNewExpName, setWzNewExpName] = useState("");
  const [wzNewExpFmt, setWzNewExpFmt] = useState<"jsonl" | "json">("jsonl");
  const [wzNewExpStart, setWzNewExpStart] = useState("");
  const [wzNewExpEnd, setWzNewExpEnd] = useState("");
  const [wzNewExpFeat, setWzNewExpFeat] = useState(true);
  const [wzNewExpTgt, setWzNewExpTgt] = useState(true);
  const [wzNewExpWarn, setWzNewExpWarn] = useState(true);
  const [wzNewExpAck, setWzNewExpAck] = useState(false);

  /* ── Step 2 form: create experiment ── */
  const [wzExpName, setWzExpName] = useState("");
  const [wzExpHyp, setWzExpHyp] = useState("");
  const [wzExpAck, setWzExpAck] = useState(false);

  /* ── Step 2 form: import results ── */
  const [wzResExpId, setWzResExpId] = useState("");
  const [wzResSum, setWzResSum] = useState("");
  const [wzResMetrics, setWzResMetrics] = useState("");
  const [wzResWarnings, setWzResWarnings] = useState("");
  const [wzResLimitations, setWzResLimitations] = useState("");
  const [wzResAck, setWzResAck] = useState(false);

  /* ── Step 3 form: comparison ── */
  const [wzCmpName, setWzCmpName] = useState("");
  const [wzCmpAck, setWzCmpAck] = useState(false);

  /* ── Step 4 form: readiness ── */
  const [wzRdName, setWzRdName] = useState("");
  const [wzRdAck, setWzRdAck] = useState(false);
  const [wzRdMetricCoverageReviewed, setWzRdMetricCoverageReviewed] = useState(false);
  const [wzRdMissingMetricsReviewed, setWzRdMissingMetricsReviewed] = useState(false);
  const [wzRdWarningsReviewed, setWzRdWarningsReviewed] = useState(false);
  const [wzRdLimitationsReviewed, setWzRdLimitationsReviewed] = useState(false);
  const [wzRdSafetyFlagsConfirmed, setWzRdSafetyFlagsConfirmed] = useState(false);

  /* ── Step 4 form: state update ── */
  const [wzRdState, setWzRdState] = useState("draft");
  const [wzRdStateReason, setWzRdStateReason] = useState("");
  const [wzRdStateAck, setWzRdStateAck] = useState(false);

  /* ── shared status ── */
  const [wzLoading, setWzLoading] = useState(false);
  const [wzError, setWzError] = useState<string | null>(null);
  const [wzSuccess, setWzSuccess] = useState<string | null>(null);
  const [wzVerifyResult, setWzVerifyResult] = useState<Record<string, unknown> | null>(null);

  /* ── helpers ── */
  const clearMessages = () => {
    setWzError(null);
    setWzSuccess(null);
    setWzVerifyResult(null);
  };

  const goToStep = (i: number) => {
    setWizardStep(i);
    clearMessages();
  };

  /* ================================================================== */
  /*  Render                                                             */
  /* ================================================================== */

  return (
    <>
      {/* ── Trigger Button ── */}
      <button
        onClick={() => setWizardOpen(true)}
        className="px-4 py-2 rounded-lg bg-primary text-primary-ink text-[12px] font-semibold hover:opacity-90 transition-opacity"
      >
        Start Research Workflow
      </button>

      {/* ── Modal Overlay ── */}
      <AnimatePresence>
        {wizardOpen && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <motion.div
              className="glass rounded-xl shadow-xl w-full max-w-[700px] max-h-[90vh] overflow-y-auto p-6 space-y-4"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              {/* ── Header ── */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-[16px] font-semibold text-ink">Guided Research Workflow</h2>
                  <p className="text-[10px] text-ink-4">
                    Research-only, offline-only. Does not imply production suitability.
                  </p>
                </div>
                <button
                  onClick={() => setWizardOpen(false)}
                  className="text-ink-3 hover:text-ink text-[18px] px-2"
                >
                  ×
                </button>
              </div>

              {/* ── Stepper ── */}
              <div className="flex gap-1">
                {["Research Data", "Experiment", "Comparison", "Readiness"].map((label, i) => (
                  <button
                    key={label}
                    onClick={() => goToStep(i)}
                    className={`flex-1 py-1.5 rounded-md text-[10px] font-medium transition-colors ${
                      wizardStep === i
                        ? "bg-primary text-primary-ink"
                        : (i === 0 && wzExportId) ||
                            (i === 1 && wzExpIds.length > 0) ||
                            (i === 2 && wzCmpId) ||
                            (i === 3 && wzRdId)
                          ? "bg-pos/10 text-pos"
                          : "bg-surface-2 text-ink-3"
                    }`}
                  >
                    {i + 1}. {label}
                  </button>
                ))}
              </div>

              {/* ── Status Messages ── */}
              {wzError && (
                <div className="p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">
                  {wzError}
                </div>
              )}
              {wzSuccess && (
                <div className="p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">
                  {wzSuccess}
                </div>
              )}

              {/* ══════════════════════════════════════════════════════ */}
              {/*  Step 1: Research Data                                */}
              {/* ══════════════════════════════════════════════════════ */}
              <AnimatePresence mode="wait">
                {wizardStep === 0 && (
                  <motion.div
                    key="step-0"
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-3"
                  >
                    <h3 className="text-[13px] font-semibold text-ink">
                      Step 1: Select or Create Dataset Export
                    </h3>
                    <p className="text-[10px] text-ink-4">
                      Choose an existing governed dataset export or create a new one.
                    </p>

                    {/* Existing exports list */}
                    {dsExportHistory.length > 0 && (
                      <div className="space-y-1 max-h-[150px] overflow-y-auto">
                        {dsExportHistory.slice(0, 10).map((exp) => (
                          <button
                            key={exp.export_id}
                            onClick={() => {
                              setWzExportId(exp.export_id);
                              setPipelineId("exportId", exp.export_id);
                              setWzSuccess(`Selected export ${exp.export_id.slice(0, 8)}`);
                              setWzError(null);
                              setWzVerifyResult(null);
                            }}
                            className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                              wzExportId === exp.export_id
                                ? "border-primary bg-primary/5"
                                : "border-line/30 hover:bg-surface-2"
                            }`}
                          >
                            <span className="font-mono text-ink-2">
                              {exp.export_id?.slice(0, 8)}
                            </span>
                            <span className="text-ink font-medium truncate max-w-[120px]">
                              {exp.name}
                            </span>
                            <span className="text-ink-3">{exp.row_count} rows</span>
                            <span
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                                exp.lifecycle_state === "active"
                                  ? "bg-pos/10 text-pos"
                                  : "bg-caution/10 text-caution"
                              }`}
                            >
                              {exp.lifecycle_state}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Create new export */}
                    <details className="border border-line/30 rounded-md">
                      <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">
                        Create new dataset export
                      </summary>
                      <div className="p-2 space-y-2">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <input
                            type="text"
                            value={wzNewExpName}
                            onChange={(e) => setWzNewExpName(e.target.value)}
                            placeholder="Export name"
                            className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <select
                            value={wzNewExpFmt}
                            onChange={(e) => setWzNewExpFmt(e.target.value as "jsonl" | "json")}
                            className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          >
                            <option value="jsonl">JSONL</option>
                            <option value="json">JSON</option>
                          </select>
                          <input
                            type="date"
                            value={wzNewExpStart}
                            onChange={(e) => setWzNewExpStart(e.target.value)}
                            className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <input
                            type="date"
                            value={wzNewExpEnd}
                            onChange={(e) => setWzNewExpEnd(e.target.value)}
                            className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                        </div>
                        <div className="flex flex-wrap gap-3 text-[9px] text-ink-3">
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzNewExpFeat}
                              onChange={(e) => setWzNewExpFeat(e.target.checked)}
                              className="rounded"
                            />{" "}
                            Features
                          </label>
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzNewExpTgt}
                              onChange={(e) => setWzNewExpTgt(e.target.checked)}
                              className="rounded"
                            />{" "}
                            Targets
                          </label>
                          <label className="flex items-center gap-1 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzNewExpWarn}
                              onChange={(e) => setWzNewExpWarn(e.target.checked)}
                              className="rounded"
                            />{" "}
                            Warnings
                          </label>
                        </div>
                        <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={wzNewExpAck}
                            onChange={(e) => setWzNewExpAck(e.target.checked)}
                            className="rounded"
                          />
                          Research-only offline export (required)
                        </label>
                        <button
                          disabled={wzLoading || !wzNewExpAck || !wzNewExpName.trim()}
                          onClick={async () => {
                            setWzLoading(true);
                            setWzError(null);
                            setWzSuccess(null);
                            try {
                              const res = await createFinrlxDatasetExport({
                                name: wzNewExpName.trim(),
                                start_date: wzNewExpStart,
                                end_date: wzNewExpEnd,
                                format: wzNewExpFmt,
                                include_features: wzNewExpFeat,
                                include_targets: wzNewExpTgt,
                                include_warnings: wzNewExpWarn,
                                research_acknowledgement: true,
                              });
                              if (res.data?.export_id) {
                                setWzExportId(res.data.export_id);
                                setPipelineId("exportId", res.data.export_id);
                                setWzSuccess(
                                  `Export ${res.data.export_id.slice(0, 8)} created (${res.data.row_count} rows, checksum: ${res.data.checksum?.slice(0, 8)})`,
                                );
                                setWzNewExpAck(false);
                                refreshExportHistory();
                              }
                            } catch (e: unknown) {
                              setWzError(e instanceof Error ? e.message : "Export failed");
                            } finally {
                              setWzLoading(false);
                            }
                          }}
                          className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40"
                        >
                          {wzLoading ? "Exporting..." : "Create Export"}
                        </button>
                      </div>
                    </details>

                    {/* Verify + Expert link */}
                    <div className="flex flex-wrap items-center gap-2">
                      {wzExportId && (
                        <button
                          disabled={wzLoading}
                          onClick={async () => {
                            setWzLoading(true);
                            setWzVerifyResult(null);
                            setWzError(null);
                            try {
                              const res = await verifyFinrlxDatasetExport(wzExportId);
                              setWzVerifyResult(res.data as unknown as Record<string, unknown>);
                            } catch (e: unknown) {
                              setWzError(e instanceof Error ? e.message : "Verify failed");
                            } finally {
                              setWzLoading(false);
                            }
                          }}
                          className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40"
                        >
                          Verify selected export
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setWizardOpen(false);
                          setActiveStep(0);
                        }}
                        className="text-[10px] text-primary hover:underline"
                      >
                        Open in Expert Tab →
                      </button>
                    </div>
                    {wzVerifyResult && (
                      <div className="p-2 rounded-md bg-surface-3 text-[9px] space-y-0.5">
                        <div>
                          Artifact:{" "}
                          <span
                            className={
                              (wzVerifyResult as Record<string, unknown>).artifact_exists
                                ? "text-pos"
                                : "text-breach"
                            }
                          >
                            {(wzVerifyResult as Record<string, unknown>).artifact_exists
                              ? "exists"
                              : "missing"}
                          </span>
                        </div>
                        {Array.isArray(
                          (wzVerifyResult as Record<string, unknown>).warnings,
                        ) &&
                          (
                            (wzVerifyResult as Record<string, unknown>).warnings as string[]
                          ).length > 0 && (
                            <div className="text-caution">
                              {(
                                (wzVerifyResult as Record<string, unknown>).warnings as string[]
                              ).join("; ")}
                            </div>
                          )}
                      </div>
                    )}

                    {wzExportId && (
                      <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">
                        Selected: <span className="font-mono">{wzExportId.slice(0, 16)}</span>
                      </div>
                    )}
                    {!wzExportId && (
                      <p className="text-[9px] text-caution">
                        Select or create an export to proceed.
                      </p>
                    )}
                  </motion.div>
                )}

                {/* ══════════════════════════════════════════════════════ */}
                {/*  Step 2: Experiment                                   */}
                {/* ══════════════════════════════════════════════════════ */}
                {wizardStep === 1 && (
                  <motion.div
                    key="step-1"
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-3"
                  >
                    <h3 className="text-[13px] font-semibold text-ink">
                      Step 2: Select or Create Experiment
                    </h3>
                    <p className="text-[10px] text-ink-4">
                      Select existing experiments or create a new one. For comparison, you need at
                      least 2 experiments with results.
                    </p>
                    {!wzExportId && (
                      <p className="text-[9px] text-caution">
                        Go back to Step 1 and select an export first.
                      </p>
                    )}

                    {/* Existing experiments list */}
                    {expList.length > 0 && (
                      <div className="space-y-1 max-h-[120px] overflow-y-auto">
                        {expList.slice(0, 10).map((exp) => (
                          <button
                            key={exp.experiment_id}
                            onClick={() => {
                              setWzExpIds((prev) =>
                                prev.includes(exp.experiment_id)
                                  ? prev.filter((id) => id !== exp.experiment_id)
                                  : [...prev, exp.experiment_id],
                              );
                              setWzError(null);
                            }}
                            className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                              wzExpIds.includes(exp.experiment_id)
                                ? "border-primary bg-primary/5"
                                : "border-line/30 hover:bg-surface-2"
                            }`}
                          >
                            <span className="font-mono text-ink-2">
                              {exp.experiment_id?.slice(0, 8)}
                            </span>
                            <span className="text-ink font-medium truncate max-w-[120px]">
                              {exp.name}
                            </span>
                            <span
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                                exp.lifecycle_state === "completed"
                                  ? "bg-pos/10 text-pos"
                                  : "bg-surface-3 text-ink-4"
                              }`}
                            >
                              {exp.lifecycle_state}
                            </span>
                            {exp.result_summary && (
                              <span className="text-ink-4">has results</span>
                            )}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Create experiment */}
                    {wzExportId && (
                      <details className="border border-line/30 rounded-md">
                        <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">
                          Create new experiment (export {wzExportId.slice(0, 8)})
                        </summary>
                        <div className="p-2 space-y-2">
                          <input
                            type="text"
                            value={wzExpName}
                            onChange={(e) => setWzExpName(e.target.value)}
                            placeholder="Experiment name"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <input
                            type="text"
                            value={wzExpHyp}
                            onChange={(e) => setWzExpHyp(e.target.value)}
                            placeholder="Hypothesis (optional)"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzExpAck}
                              onChange={(e) => setWzExpAck(e.target.checked)}
                              className="rounded"
                            />
                            Research-only offline experiment (required)
                          </label>
                          <button
                            disabled={wzLoading || !wzExpAck || !wzExpName.trim()}
                            onClick={async () => {
                              setWzLoading(true);
                              setWzError(null);
                              setWzSuccess(null);
                              try {
                                const res = await createFinrlxResearchExperiment({
                                  name: wzExpName.trim(),
                                  linked_export_id: wzExportId,
                                  hypothesis: wzExpHyp,
                                  research_acknowledgement: true,
                                });
                                if (res.data?.experiment_id) {
                                  setWzExpIds((prev) => [...prev, res.data.experiment_id]);
                                  setPipelineId("experimentIds", [
                                    ...wzExpIds,
                                    res.data.experiment_id,
                                  ]);
                                  setWzSuccess(
                                    `Experiment ${res.data.experiment_id.slice(0, 8)} created.`,
                                  );
                                  setWzExpAck(false);
                                  refreshExperiments();
                                }
                              } catch (e: unknown) {
                                setWzError(e instanceof Error ? e.message : "Failed");
                              } finally {
                                setWzLoading(false);
                              }
                            }}
                            className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40"
                          >
                            {wzLoading ? "Creating..." : "Create Experiment"}
                          </button>
                        </div>
                      </details>
                    )}

                    {/* Import results */}
                    {wzExpIds.length > 0 && (
                      <details className="border border-line/30 rounded-md">
                        <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">
                          Import metadata-only results
                        </summary>
                        <div className="p-2 space-y-2">
                          <p className="text-[9px] text-ink-4">
                            Metadata-only — no files, no code, no production influence.
                          </p>
                          <select
                            value={wzResExpId}
                            onChange={(e) => setWzResExpId(e.target.value)}
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink font-mono focus:border-primary focus:outline-none"
                          >
                            <option value="">Select experiment</option>
                            {wzExpIds.map((id) => (
                              <option key={id} value={id}>
                                {id.slice(0, 16)}
                              </option>
                            ))}
                          </select>
                          <input
                            type="text"
                            value={wzResSum}
                            onChange={(e) => setWzResSum(e.target.value)}
                            placeholder="Result summary"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <textarea
                            value={wzResMetrics}
                            onChange={(e) => setWzResMetrics(e.target.value)}
                            rows={2}
                            placeholder='{"sharpe_ratio": 1.2, "max_drawdown": -0.05}'
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink font-mono focus:border-primary focus:outline-none resize-y"
                          />
                          <textarea
                            value={wzResWarnings}
                            onChange={(e) => setWzResWarnings(e.target.value)}
                            rows={1}
                            placeholder="Warnings (one per line, optional)"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none resize-y"
                          />
                          <textarea
                            value={wzResLimitations}
                            onChange={(e) => setWzResLimitations(e.target.value)}
                            rows={1}
                            placeholder="Limitations (one per line, optional)"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none resize-y"
                          />
                          <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzResAck}
                              onChange={(e) => setWzResAck(e.target.checked)}
                              className="rounded"
                            />
                            Metadata-only offline result import (required)
                          </label>
                          <button
                            disabled={wzLoading || !wzResAck || !wzResExpId}
                            onClick={async () => {
                              setWzLoading(true);
                              setWzError(null);
                              setWzSuccess(null);
                              let metrics: Record<string, number | string> = {};
                              try {
                                metrics = JSON.parse(wzResMetrics);
                              } catch {
                                setWzError("Invalid JSON in result metrics.");
                                setWzLoading(false);
                                return;
                              }
                              const warnLines = wzResWarnings
                                .split("\n")
                                .map((s) => s.trim())
                                .filter(Boolean);
                              const limLines = wzResLimitations
                                .split("\n")
                                .map((s) => s.trim())
                                .filter(Boolean);
                              try {
                                const res = await importFinrlxResearchExperimentResults(
                                  wzResExpId,
                                  {
                                    acknowledgement: true,
                                    result_summary: wzResSum,
                                    result_metrics: metrics,
                                    warnings: warnLines.length > 0 ? warnLines : undefined,
                                    limitations: limLines.length > 0 ? limLines : undefined,
                                  },
                                );
                                if (res.data) {
                                  setWzSuccess("Results imported (metadata-only).");
                                  setWzResAck(false);
                                  refreshExperiments();
                                }
                              } catch (e: unknown) {
                                setWzError(e instanceof Error ? e.message : "Import failed");
                              } finally {
                                setWzLoading(false);
                              }
                            }}
                            className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40"
                          >
                            {wzLoading ? "Importing..." : "Import Results"}
                          </button>
                        </div>
                      </details>
                    )}

                    {/* Verify + Expert link */}
                    <div className="flex flex-wrap items-center gap-2">
                      {wzExpIds.length === 1 && (
                        <button
                          disabled={wzLoading}
                          onClick={async () => {
                            setWzLoading(true);
                            setWzVerifyResult(null);
                            setWzError(null);
                            try {
                              const res = await verifyFinrlxResearchExperiment(wzExpIds[0]);
                              setWzVerifyResult(
                                res.data as unknown as Record<string, unknown>,
                              );
                            } catch (e: unknown) {
                              setWzError(e instanceof Error ? e.message : "Verify failed");
                            } finally {
                              setWzLoading(false);
                            }
                          }}
                          className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40"
                        >
                          Verify experiment
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setWizardOpen(false);
                          setActiveStep(1);
                        }}
                        className="text-[10px] text-primary hover:underline"
                      >
                        Open in Expert Tab →
                      </button>
                    </div>
                    {wzVerifyResult && wizardStep === 1 && (
                      <div className="p-2 rounded-md bg-surface-3 text-[9px]">
                        Status:{" "}
                        <span
                          className={
                            (wzVerifyResult as Record<string, unknown>).healthy
                              ? "text-pos"
                              : "text-caution"
                          }
                        >
                          {(wzVerifyResult as Record<string, unknown>).healthy
                            ? "healthy"
                            : "warnings"}
                        </span>
                        {Array.isArray(
                          (wzVerifyResult as Record<string, unknown>).warnings,
                        ) &&
                          (
                            (wzVerifyResult as Record<string, unknown>).warnings as string[]
                          ).length > 0 && (
                            <span className="text-caution ml-1">
                              {(
                                (wzVerifyResult as Record<string, unknown>)
                                  .warnings as string[]
                              ).join("; ")}
                            </span>
                          )}
                      </div>
                    )}

                    {wzExpIds.length > 0 && (
                      <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">
                        Selected: {wzExpIds.length} experiment
                        {wzExpIds.length !== 1 ? "s" : ""} (
                        {wzExpIds.map((id) => id.slice(0, 8)).join(", ")})
                      </div>
                    )}
                    {wzExpIds.length === 1 && (
                      <p className="text-[9px] text-caution">
                        Need at least 2 experiments for comparison in the next step.
                      </p>
                    )}
                  </motion.div>
                )}

                {/* ══════════════════════════════════════════════════════ */}
                {/*  Step 3: Comparison                                   */}
                {/* ══════════════════════════════════════════════════════ */}
                {wizardStep === 2 && (
                  <motion.div
                    key="step-2"
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-3"
                  >
                    <h3 className="text-[13px] font-semibold text-ink">
                      Step 3: Create or Select Comparison
                    </h3>
                    <p className="text-[10px] text-ink-4">
                      Compare experiments using imported result metadata. Numeric metric sorting
                      only — does not imply production suitability.
                    </p>

                    {/* Existing comparisons list */}
                    {cmpList.length > 0 && (
                      <div className="space-y-1 max-h-[120px] overflow-y-auto">
                        {cmpList.slice(0, 8).map((cmp) => (
                          <button
                            key={cmp.comparison_id}
                            onClick={() => {
                              setWzCmpId(cmp.comparison_id);
                              setPipelineId("comparisonId", cmp.comparison_id);
                              setWzSuccess(
                                `Selected comparison ${cmp.comparison_id.slice(0, 8)}`,
                              );
                              setWzError(null);
                              setWzVerifyResult(null);
                            }}
                            className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                              wzCmpId === cmp.comparison_id
                                ? "border-primary bg-primary/5"
                                : "border-line/30 hover:bg-surface-2"
                            }`}
                          >
                            <span className="font-mono text-ink-2">
                              {cmp.comparison_id?.slice(0, 8)}
                            </span>
                            <span className="text-ink font-medium truncate max-w-[120px]">
                              {cmp.name}
                            </span>
                            <span className="text-ink-3">
                              {cmp.experiment_ids?.length} exp
                            </span>
                            <span className="text-ink-4">
                              {cmp.comparison_summary?.metric_names?.length || 0} metrics
                            </span>
                            {(cmp.warnings?.length || 0) > 0 && (
                              <span className="text-caution">
                                {cmp.warnings?.length} warn
                              </span>
                            )}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Create comparison */}
                    {wzExpIds.length >= 2 && (
                      <details
                        className="border border-line/30 rounded-md"
                        open={!wzCmpId}
                      >
                        <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">
                          Create comparison from {wzExpIds.length} experiments
                        </summary>
                        <div className="p-2 space-y-2">
                          <input
                            type="text"
                            value={wzCmpName}
                            onChange={(e) => setWzCmpName(e.target.value)}
                            placeholder="Comparison name"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzCmpAck}
                              onChange={(e) => setWzCmpAck(e.target.checked)}
                              className="rounded"
                            />
                            Research-only offline comparison (required)
                          </label>
                          <button
                            disabled={wzLoading || !wzCmpAck || !wzCmpName.trim()}
                            onClick={async () => {
                              setWzLoading(true);
                              setWzError(null);
                              setWzSuccess(null);
                              try {
                                const res = await createFinrlxExperimentComparison({
                                  name: wzCmpName.trim(),
                                  experiment_ids: wzExpIds,
                                  research_acknowledgement: true,
                                });
                                if (res.data?.comparison_id) {
                                  setWzCmpId(res.data.comparison_id);
                                  setPipelineId("comparisonId", res.data.comparison_id);
                                  setWzSuccess(
                                    `Comparison ${res.data.comparison_id.slice(0, 8)} created.`,
                                  );
                                  setWzCmpAck(false);
                                  refreshComparisons();
                                }
                              } catch (e: unknown) {
                                setWzError(e instanceof Error ? e.message : "Failed");
                              } finally {
                                setWzLoading(false);
                              }
                            }}
                            className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40"
                          >
                            {wzLoading ? "Creating..." : "Create Comparison"}
                          </button>
                        </div>
                      </details>
                    )}
                    {wzExpIds.length < 2 && (
                      <p className="text-[9px] text-caution">
                        Go back to Step 2 and select at least 2 experiments.
                      </p>
                    )}

                    {/* Verify + Expert link */}
                    <div className="flex flex-wrap items-center gap-2">
                      {wzCmpId && (
                        <button
                          disabled={wzLoading}
                          onClick={async () => {
                            setWzLoading(true);
                            setWzVerifyResult(null);
                            setWzError(null);
                            try {
                              const res = await verifyFinrlxExperimentComparison(wzCmpId);
                              setWzVerifyResult(
                                res.data as unknown as Record<string, unknown>,
                              );
                            } catch (e: unknown) {
                              setWzError(e instanceof Error ? e.message : "Verify failed");
                            } finally {
                              setWzLoading(false);
                            }
                          }}
                          className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40"
                        >
                          Verify comparison
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setWizardOpen(false);
                          setActiveStep(2);
                        }}
                        className="text-[10px] text-primary hover:underline"
                      >
                        Open in Expert Tab →
                      </button>
                    </div>
                    {wzVerifyResult && wizardStep === 2 && (
                      <div className="p-2 rounded-md bg-surface-3 text-[9px]">
                        Status:{" "}
                        <span
                          className={
                            (wzVerifyResult as Record<string, unknown>).healthy
                              ? "text-pos"
                              : "text-caution"
                          }
                        >
                          {(wzVerifyResult as Record<string, unknown>).healthy
                            ? "healthy"
                            : "warnings"}
                        </span>
                        {Array.isArray(
                          (wzVerifyResult as Record<string, unknown>).warnings,
                        ) &&
                          (
                            (wzVerifyResult as Record<string, unknown>).warnings as string[]
                          ).length > 0 && (
                            <span className="text-caution ml-1">
                              {(
                                (wzVerifyResult as Record<string, unknown>)
                                  .warnings as string[]
                              ).join("; ")}
                            </span>
                          )}
                      </div>
                    )}

                    {wzCmpId && (
                      <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">
                        Selected: <span className="font-mono">{wzCmpId.slice(0, 16)}</span>
                      </div>
                    )}
                  </motion.div>
                )}

                {/* ══════════════════════════════════════════════════════ */}
                {/*  Step 4: Readiness Review                             */}
                {/* ══════════════════════════════════════════════════════ */}
                {wizardStep === 3 && (
                  <motion.div
                    key="step-3"
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-3"
                  >
                    <h3 className="text-[13px] font-semibold text-ink">
                      Step 4: Readiness Review
                    </h3>
                    <p className="text-[10px] text-ink-4">
                      Assess research evidence completeness. &quot;Research review ready&quot; does
                      not mean production-ready.
                    </p>
                    {!wzCmpId && (
                      <p className="text-[9px] text-caution">
                        Go back to Step 3 and select or create a comparison first.
                      </p>
                    )}

                    {/* Existing readiness reviews list */}
                    {rdList.length > 0 && (
                      <div className="space-y-1 max-h-[120px] overflow-y-auto">
                        {rdList.slice(0, 8).map((rv) => (
                          <button
                            key={rv.readiness_id}
                            onClick={() => {
                              setWzRdId(rv.readiness_id);
                              setPipelineId("readinessId", rv.readiness_id);
                              setWzSuccess(
                                `Selected readiness ${rv.readiness_id.slice(0, 8)}`,
                              );
                              setWzError(null);
                              setWzVerifyResult(null);
                              setWzRdState(rv.readiness_state);
                            }}
                            className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                              wzRdId === rv.readiness_id
                                ? "border-primary bg-primary/5"
                                : "border-line/30 hover:bg-surface-2"
                            }`}
                          >
                            <span className="font-mono text-ink-2">
                              {rv.readiness_id?.slice(0, 8)}
                            </span>
                            <span className="text-ink font-medium truncate max-w-[120px]">
                              {rv.name}
                            </span>
                            <span
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                                rv.readiness_state === "research_review_ready"
                                  ? "bg-pos/10 text-pos"
                                  : rv.readiness_state === "needs_more_evidence"
                                    ? "bg-caution/10 text-caution"
                                    : "bg-surface-3 text-ink-4"
                              }`}
                            >
                              {rv.readiness_state?.replace(/_/g, " ")}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Create readiness */}
                    {wzCmpId && (
                      <details className="border border-line/30 rounded-md" open={!wzRdId}>
                        <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">
                          Create readiness review (comparison {wzCmpId.slice(0, 8)})
                        </summary>
                        <div className="p-2 space-y-2">
                          <input
                            type="text"
                            value={wzRdName}
                            onChange={(e) => setWzRdName(e.target.value)}
                            placeholder="Review name"
                            className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                          />
                          <div className="pt-1 space-y-1">
                            <div className="text-[9px] text-ink-3 font-medium">
                              Evidence Checklist
                            </div>
                            {(
                              [
                                {
                                  key: "mc",
                                  label: "Metric coverage reviewed",
                                  val: wzRdMetricCoverageReviewed,
                                  set: setWzRdMetricCoverageReviewed,
                                },
                                {
                                  key: "mm",
                                  label: "Missing metrics reviewed",
                                  val: wzRdMissingMetricsReviewed,
                                  set: setWzRdMissingMetricsReviewed,
                                },
                                {
                                  key: "wr",
                                  label: "Warnings reviewed",
                                  val: wzRdWarningsReviewed,
                                  set: setWzRdWarningsReviewed,
                                },
                                {
                                  key: "lr",
                                  label: "Limitations reviewed",
                                  val: wzRdLimitationsReviewed,
                                  set: setWzRdLimitationsReviewed,
                                },
                                {
                                  key: "sf",
                                  label: "Safety flags confirmed",
                                  val: wzRdSafetyFlagsConfirmed,
                                  set: setWzRdSafetyFlagsConfirmed,
                                },
                              ] as const
                            ).map((item) => (
                              <label
                                key={item.key}
                                className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer"
                              >
                                <input
                                  type="checkbox"
                                  checked={item.val}
                                  onChange={(e) => item.set(e.target.checked)}
                                  className="rounded"
                                />
                                {item.label}
                              </label>
                            ))}
                          </div>
                          <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzRdAck}
                              onChange={(e) => setWzRdAck(e.target.checked)}
                              className="rounded"
                            />
                            Research-only readiness review — does not imply production suitability
                            (required)
                          </label>
                          <button
                            disabled={wzLoading || !wzRdAck || !wzRdName.trim()}
                            onClick={async () => {
                              setWzLoading(true);
                              setWzError(null);
                              setWzSuccess(null);
                              try {
                                const res = await createFinrlxResearchReadiness({
                                  name: wzRdName.trim(),
                                  linked_comparison_id: wzCmpId,
                                  research_acknowledgement: true,
                                  checklist: {
                                    metric_coverage_reviewed: wzRdMetricCoverageReviewed,
                                    missing_metrics_reviewed: wzRdMissingMetricsReviewed,
                                    warnings_reviewed: wzRdWarningsReviewed,
                                    limitations_reviewed: wzRdLimitationsReviewed,
                                    safety_flags_confirmed: wzRdSafetyFlagsConfirmed,
                                  },
                                });
                                if (res.data?.readiness_id) {
                                  setWzRdId(res.data.readiness_id);
                                  setPipelineId("readinessId", res.data.readiness_id);
                                  setWzSuccess(
                                    `Readiness ${res.data.readiness_id.slice(0, 8)} created. Suggested: ${res.data.suggested_readiness_state?.replace(/_/g, " ")}`,
                                  );
                                  setWzRdAck(false);
                                  refreshReadiness();
                                }
                              } catch (e: unknown) {
                                setWzError(e instanceof Error ? e.message : "Failed");
                              } finally {
                                setWzLoading(false);
                              }
                            }}
                            className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40"
                          >
                            {wzLoading ? "Creating..." : "Create Readiness Review"}
                          </button>
                        </div>
                      </details>
                    )}

                    {/* State update */}
                    {wzRdId && (
                      <details className="border border-line/30 rounded-md">
                        <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">
                          Update readiness state
                        </summary>
                        <div className="p-2 space-y-2">
                          <p className="text-[9px] text-ink-4">
                            Research review ready does not mean production-ready.
                          </p>
                          {wzRdState === "research_review_ready" && (
                            <p className="text-[9px] text-caution">
                              Backend gates require: reviewed warnings, reviewed limitations,
                              confirmed safety flags, and no blocking findings.
                            </p>
                          )}
                          <div className="flex flex-wrap gap-2">
                            <select
                              value={wzRdState}
                              onChange={(e) => setWzRdState(e.target.value)}
                              className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                            >
                              <option value="draft">draft</option>
                              <option value="needs_more_evidence">needs more evidence</option>
                              <option value="research_review_ready">
                                research review ready
                              </option>
                              <option value="archived">archived</option>
                            </select>
                            <input
                              type="text"
                              value={wzRdStateReason}
                              onChange={(e) => setWzRdStateReason(e.target.value)}
                              placeholder="Reason (optional)"
                              className="flex-1 min-w-[100px] px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none"
                            />
                          </div>
                          <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={wzRdStateAck}
                              onChange={(e) => setWzRdStateAck(e.target.checked)}
                              className="rounded"
                            />
                            I acknowledge this state change (research review only)
                          </label>
                          <button
                            disabled={wzLoading || !wzRdStateAck}
                            onClick={async () => {
                              setWzLoading(true);
                              setWzError(null);
                              setWzSuccess(null);
                              try {
                                await updateFinrlxResearchReadinessState(wzRdId, {
                                  readiness_state: wzRdState as ReadinessState,
                                  acknowledgement: true,
                                  reason: wzRdStateReason || undefined,
                                });
                                setWzSuccess(
                                  `State updated to ${wzRdState.replace(/_/g, " ")}.`,
                                );
                                setWzRdStateAck(false);
                                refreshReadiness();
                              } catch (e: unknown) {
                                setWzError(e instanceof Error ? e.message : "Update failed");
                              } finally {
                                setWzLoading(false);
                              }
                            }}
                            className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40"
                          >
                            {wzLoading ? "Updating..." : "Update State"}
                          </button>
                        </div>
                      </details>
                    )}

                    {/* Verify + Expert */}
                    <div className="flex flex-wrap items-center gap-2">
                      {wzRdId && (
                        <button
                          disabled={wzLoading}
                          onClick={async () => {
                            setWzLoading(true);
                            setWzVerifyResult(null);
                            setWzError(null);
                            try {
                              const res = await verifyFinrlxResearchReadiness(wzRdId);
                              setWzVerifyResult(
                                res.data as unknown as Record<string, unknown>,
                              );
                            } catch (e: unknown) {
                              setWzError(e instanceof Error ? e.message : "Verify failed");
                            } finally {
                              setWzLoading(false);
                            }
                          }}
                          className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40"
                        >
                          Verify readiness
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setWizardOpen(false);
                          setActiveStep(3);
                        }}
                        className="text-[10px] text-primary hover:underline"
                      >
                        Open in Expert Tab →
                      </button>
                    </div>
                    {wzVerifyResult && wizardStep === 3 && (
                      <div className="p-2 rounded-md bg-surface-3 text-[9px]">
                        Status:{" "}
                        <span
                          className={
                            (wzVerifyResult as Record<string, unknown>).healthy
                              ? "text-pos"
                              : "text-caution"
                          }
                        >
                          {(wzVerifyResult as Record<string, unknown>).healthy
                            ? "healthy"
                            : "warnings"}
                        </span>
                        {Array.isArray(
                          (wzVerifyResult as Record<string, unknown>).warnings,
                        ) &&
                          (
                            (wzVerifyResult as Record<string, unknown>).warnings as string[]
                          ).length > 0 && (
                            <span className="text-caution ml-1">
                              {(
                                (wzVerifyResult as Record<string, unknown>)
                                  .warnings as string[]
                              ).join("; ")}
                            </span>
                          )}
                      </div>
                    )}

                    {wzRdId && (
                      <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">
                        Selected: <span className="font-mono">{wzRdId.slice(0, 16)}</span>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── Navigation ── */}
              <div className="flex items-center justify-between pt-3 border-t border-line">
                <button
                  disabled={wizardStep === 0}
                  onClick={() => {
                    setWizardStep((s) => s - 1);
                    clearMessages();
                  }}
                  className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-surface-2 text-ink-3 hover:bg-surface-3 disabled:opacity-30 transition-colors"
                >
                  ← Back
                </button>
                <div className="flex items-center gap-1.5">
                  {[0, 1, 2, 3].map((i) => (
                    <span
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        wizardStep === i ? "bg-primary" : "bg-surface-3"
                      }`}
                    />
                  ))}
                </div>
                {wizardStep < 3 ? (
                  <button
                    onClick={() => {
                      setWizardStep((s) => s + 1);
                      clearMessages();
                    }}
                    className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-primary text-primary-ink hover:opacity-90 transition-opacity"
                  >
                    Next →
                  </button>
                ) : (
                  <button
                    onClick={() => setWizardOpen(false)}
                    className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-pos text-white hover:opacity-90 transition-opacity"
                  >
                    Done
                  </button>
                )}
              </div>

              {/* ── Safety disclaimer badges ── */}
              <div className="flex flex-wrap gap-1.5 pt-2 border-t border-line/30">
                {[
                  "research-only",
                  "offline-only",
                  "no production influence",
                  "not eligible for promotion",
                ].map((flag) => (
                  <span
                    key={flag}
                    className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-pos/10 text-pos"
                  >
                    {flag}
                  </span>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
