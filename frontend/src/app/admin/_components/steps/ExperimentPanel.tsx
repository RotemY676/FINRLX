"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../../_context/AdminContext";
import { GlassCard } from "../GlassCard";
import { Icon } from "@/components/icons/Icon";
import {
  createFinrlxResearchExperiment,
  getFinrlxResearchExperiment,
  updateFinrlxResearchExperimentState,
  importFinrlxResearchExperimentResults,
  verifyFinrlxResearchExperiment,
  rebuildFinrlxResearchExperimentRegistry,
  ResearchExperiment,
  ExperimentVerifyResult,
  ExperimentLifecycleState,
} from "@/services/api";

export function ExperimentPanel() {
  const {
    dsExportHistory,
    expList,
    refreshExperiments,
    pipelineIds,
    setPipelineId,
  } = useAdmin();

  // ── Create experiment form ──
  const [expName, setExpName] = useState("Offline research experiment");
  const [expLinkedExportId, setExpLinkedExportId] = useState(pipelineIds.exportId || "");
  const [expHypothesis, setExpHypothesis] = useState("");
  const [expMethodNotes, setExpMethodNotes] = useState("");
  const [expParams, setExpParams] = useState("{}");
  const [expMetrics, setExpMetrics] = useState("");
  const [expAck, setExpAck] = useState(false);
  const [expCreateLoading, setExpCreateLoading] = useState(false);
  const [expCreateError, setExpCreateError] = useState<string | null>(null);
  const [expCreateSuccess, setExpCreateSuccess] = useState<string | null>(null);

  // ── Selected experiment detail ──
  const [expSelected, setExpSelected] = useState<ResearchExperiment | null>(null);
  const [expVerifyResult, setExpVerifyResult] = useState<ExperimentVerifyResult | null>(null);
  const [expStateValue, setExpStateValue] = useState<ExperimentLifecycleState>("planned");
  const [expStateAck, setExpStateAck] = useState(false);
  const [expStateReason, setExpStateReason] = useState("");
  const [expResultSummary, setExpResultSummary] = useState("");
  const [expResultMetrics, setExpResultMetrics] = useState("{}");
  const [expResultAck, setExpResultAck] = useState(false);
  const [expLoading, setExpLoading] = useState<string | null>(null);
  const [expError, setExpError] = useState<string | null>(null);
  const [expSuccess, setExpSuccess] = useState<string | null>(null);
  const [expRebuildAck, setExpRebuildAck] = useState(false);

  // Sync linked export id from context when it changes
  // (auto-populate)
  const effectiveLinkedExportId = expLinkedExportId || pipelineIds.exportId;

  // ── Callbacks ──
  const handleCreateExperiment = useCallback(async () => {
    if (!expAck || !expName.trim() || !effectiveLinkedExportId.trim()) return;
    setExpCreateLoading(true);
    setExpCreateError(null);
    setExpCreateSuccess(null);
    let parsedParams: Record<string, unknown> = {};
    try { parsedParams = JSON.parse(expParams); } catch { /* use empty */ }
    const metricsList = expMetrics ? expMetrics.split(",").map(s => s.trim()).filter(Boolean) : [];
    try {
      const res = await createFinrlxResearchExperiment({
        name: expName.trim(),
        linked_export_id: effectiveLinkedExportId.trim(),
        hypothesis: expHypothesis,
        method_notes: expMethodNotes,
        parameters: parsedParams,
        expected_metrics: metricsList,
        research_acknowledgement: true,
      });
      if (res.data?.experiment_id) {
        setExpCreateSuccess(`Experiment ${res.data.experiment_id.slice(0, 8)} created.`);
        setExpAck(false);
        setPipelineId("experimentIds", [...pipelineIds.experimentIds, res.data.experiment_id]);
        refreshExperiments();
      }
    } catch (e: unknown) {
      setExpCreateError(e instanceof Error ? e.message : "Create experiment failed");
    } finally {
      setExpCreateLoading(false);
    }
  }, [expAck, expName, effectiveLinkedExportId, expHypothesis, expMethodNotes, expParams, expMetrics, refreshExperiments, setPipelineId, pipelineIds.experimentIds]);

  const selectExperiment = useCallback(async (exp: ResearchExperiment) => {
    setExpSelected(null);
    setExpVerifyResult(null);
    setExpStateAck(false);
    setExpStateReason("");
    setExpResultAck(false);
    setExpError(null);
    setExpSuccess(null);
    try {
      const res = await getFinrlxResearchExperiment(exp.experiment_id);
      if (res.data) {
        setExpSelected(res.data);
        setExpStateValue(res.data.lifecycle_state);
      }
    } catch { /* graceful */ }
  }, []);

  const handleExpVerify = useCallback(async () => {
    if (!expSelected) return;
    setExpLoading("verify");
    setExpError(null);
    setExpVerifyResult(null);
    try {
      const res = await verifyFinrlxResearchExperiment(expSelected.experiment_id);
      if (res.data) setExpVerifyResult(res.data);
    } catch (e: unknown) {
      setExpError(e instanceof Error ? e.message : "Verify failed");
    } finally {
      setExpLoading(null);
    }
  }, [expSelected]);

  const handleExpStateUpdate = useCallback(async () => {
    if (!expSelected || !expStateAck) return;
    setExpLoading("state");
    setExpError(null);
    setExpSuccess(null);
    try {
      await updateFinrlxResearchExperimentState(expSelected.experiment_id, {
        lifecycle_state: expStateValue,
        acknowledgement: true,
        reason: expStateReason || undefined,
      });
      setExpSuccess(`State updated to ${expStateValue}.`);
      setExpStateAck(false);
      refreshExperiments();
      selectExperiment({ ...expSelected, lifecycle_state: expStateValue });
    } catch (e: unknown) {
      setExpError(e instanceof Error ? e.message : "State update failed");
    } finally {
      setExpLoading(null);
    }
  }, [expSelected, expStateValue, expStateAck, expStateReason, refreshExperiments, selectExperiment]);

  const handleExpResultImport = useCallback(async () => {
    if (!expSelected || !expResultAck) return;
    setExpLoading("results");
    setExpError(null);
    setExpSuccess(null);
    let parsedMetrics: Record<string, number | string> = {};
    try { parsedMetrics = JSON.parse(expResultMetrics); } catch { /* use empty */ }
    try {
      await importFinrlxResearchExperimentResults(expSelected.experiment_id, {
        acknowledgement: true,
        result_summary: expResultSummary,
        result_metrics: parsedMetrics,
      });
      setExpSuccess("Results imported (metadata-only).");
      setExpResultAck(false);
      refreshExperiments();
      selectExperiment(expSelected);
    } catch (e: unknown) {
      setExpError(e instanceof Error ? e.message : "Result import failed");
    } finally {
      setExpLoading(null);
    }
  }, [expSelected, expResultAck, expResultSummary, expResultMetrics, refreshExperiments, selectExperiment]);

  const handleExpRebuildRegistry = useCallback(async () => {
    if (!expRebuildAck) return;
    setExpLoading("rebuild");
    setExpError(null);
    setExpSuccess(null);
    try {
      const res = await rebuildFinrlxResearchExperimentRegistry({ acknowledgement: true });
      setExpSuccess(`Experiment registry rebuilt: ${res.data.experiment_count} experiments found.`);
      setExpRebuildAck(false);
      refreshExperiments();
    } catch (e: unknown) {
      setExpError(e instanceof Error ? e.message : "Rebuild failed");
    } finally {
      setExpLoading(null);
    }
  }, [expRebuildAck, refreshExperiments]);

  return (
    <AnimatePresence mode="wait">
      <GlassCard>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="sparkle" size={15} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Local Research Experiments</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">research-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">offline-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">not eligible for promotion</span>
        </div>
        <p className="text-[10px] text-ink-4 mb-3">
          Track offline/local research experiments linked to governed dataset exports. Shadow experiment metadata only — not used by production decisions, no broker execution, no automatic training.
        </p>

        {/* Create experiment form */}
        <div className="space-y-2 mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Experiment name</label>
              <input type="text" value={expName} onChange={(e) => setExpName(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Linked export ID</label>
              <select
                value={effectiveLinkedExportId}
                onChange={(e) => setExpLinkedExportId(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink font-mono focus:border-primary focus:outline-none"
              >
                <option value="">Select a dataset export...</option>
                {dsExportHistory.map((exp) => (
                  <option key={exp.export_id} value={exp.export_id}>
                    {exp.export_id.slice(0, 8)} - {exp.name} ({exp.row_count} rows, {exp.lifecycle_state})
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-0.5">Hypothesis</label>
            <input type="text" value={expHypothesis} onChange={(e) => setExpHypothesis(e.target.value)}
              placeholder="What are you testing?"
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-0.5">Method notes</label>
            <input type="text" value={expMethodNotes} onChange={(e) => setExpMethodNotes(e.target.value)}
              placeholder="Approach, tools, configuration notes"
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Parameters (JSON)</label>
              <textarea value={expParams} onChange={(e) => setExpParams(e.target.value)} rows={2}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink font-mono focus:border-primary focus:outline-none resize-y" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Expected metrics (comma-separated)</label>
              <input type="text" value={expMetrics} onChange={(e) => setExpMetrics(e.target.value)}
                placeholder="sharpe_ratio, max_drawdown, total_return"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
          </div>

          <div className="rounded-lg border border-line bg-surface-2 p-3">
            <label className="flex items-start gap-2 text-[11px] text-ink-2 cursor-pointer">
              <input type="checkbox" checked={expAck} onChange={(e) => setExpAck(e.target.checked)} className="rounded mt-0.5" />
              <span>
                I understand this creates a <strong className="text-ink">research-only offline experiment record</strong>.
                It does not run training, benchmarks, or affect production recommendations.
              </span>
            </label>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleCreateExperiment}
              disabled={expCreateLoading || !expAck || !expName.trim() || !effectiveLinkedExportId.trim()}
              className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[11px] font-medium hover:opacity-90 transition-opacity disabled:opacity-40">
              {expCreateLoading ? "Creating..." : "Create Experiment"}
            </button>
          </div>
          {expCreateError && <div className="p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{expCreateError}</div>}
          {expCreateSuccess && <div className="p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{expCreateSuccess}</div>}
        </div>

        {/* Experiment list */}
        {expList.length > 0 && (
          <div className="border-t border-line pt-3 mb-3">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h4 className="text-[12px] font-semibold text-ink">Experiment Registry</h4>
              <span className="text-[10px] text-ink-4">{expList.length} experiment{expList.length !== 1 ? "s" : ""}</span>
            </div>
            <div className="space-y-1">
              {expList.map((exp) => (
                <button key={exp.experiment_id} onClick={() => selectExperiment(exp)}
                  className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                    expSelected?.experiment_id === exp.experiment_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                  }`}>
                  <span className="font-mono text-ink-2 break-all">{exp.experiment_id?.slice(0, 8)}</span>
                  <span className="text-ink font-medium truncate max-w-[150px]">{exp.name}</span>
                  <span className="text-ink-3 truncate max-w-[100px]">export:{exp.linked_export_id?.slice(0, 8)}</span>
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                    exp.lifecycle_state === "completed" ? "bg-pos/10 text-pos" :
                    exp.lifecycle_state === "failed" ? "bg-breach/10 text-breach" :
                    exp.lifecycle_state === "running_offline" ? "bg-caution/10 text-caution" :
                    exp.lifecycle_state === "archived" ? "bg-surface-3 text-ink-4" :
                    "bg-primary/10 text-primary"
                  }`}>{exp.lifecycle_state}</span>
                  {exp.result_summary && <span className="text-ink-4">has results</span>}
                  <span className="text-ink-4 ml-auto">{exp.created_at?.slice(0, 19)}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected experiment detail */}
        {expSelected && (
          <div className="border-t border-line pt-3">
            {expError && <div className="mb-2 p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{expError}</div>}
            {expSuccess && <div className="mb-2 p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{expSuccess}</div>}

            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2 mb-3">
              <div className="font-semibold text-[11px] text-ink mb-1">Experiment Detail</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div><span className="text-ink-4">ID:</span> <span className="font-mono text-ink-2 break-all">{expSelected.experiment_id}</span></div>
                <div><span className="text-ink-4">State:</span> <span className={
                  expSelected.lifecycle_state === "completed" ? "text-pos" :
                  expSelected.lifecycle_state === "failed" ? "text-breach" :
                  "text-ink"
                }>{expSelected.lifecycle_state}</span></div>
                <div><span className="text-ink-4">Name:</span> <span className="text-ink">{expSelected.name}</span></div>
                <div><span className="text-ink-4">Linked export:</span> <span className="font-mono text-ink-2 break-all">{expSelected.linked_export_id}</span></div>
                <div className="sm:col-span-2"><span className="text-ink-4">Checksum:</span> <span className="font-mono text-ink-2 break-all">{expSelected.linked_export_checksum || "\u2014"}</span></div>
                <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-2 break-all">{expSelected.linked_export_fingerprint || "\u2014"}</span></div>
                <div><span className="text-ink-4">Export rows:</span> <span className="text-ink">{expSelected.linked_export_row_count}</span></div>
              </div>
              {expSelected.hypothesis && <div><span className="text-ink-4">Hypothesis:</span> <span className="text-ink">{expSelected.hypothesis}</span></div>}
              {expSelected.method_notes && <div><span className="text-ink-4">Method:</span> <span className="text-ink">{expSelected.method_notes}</span></div>}
              {expSelected.parameters && Object.keys(expSelected.parameters).length > 0 && (
                <div><span className="text-ink-4">Parameters:</span> <span className="font-mono text-ink-2 break-all">{JSON.stringify(expSelected.parameters)}</span></div>
              )}
              {expSelected.expected_metrics && expSelected.expected_metrics.length > 0 && (
                <div><span className="text-ink-4">Expected metrics:</span> <span className="text-ink">{expSelected.expected_metrics.join(", ")}</span></div>
              )}
              {expSelected.result_summary && <div><span className="text-ink-4">Result summary:</span> <span className="text-ink">{expSelected.result_summary}</span></div>}
              {expSelected.result_metrics && Object.keys(expSelected.result_metrics).length > 0 && (
                <div><span className="text-ink-4">Result metrics:</span> <span className="font-mono text-ink-2 break-all">{JSON.stringify(expSelected.result_metrics)}</span></div>
              )}
              {expSelected.warnings && expSelected.warnings.length > 0 && (
                <div className="text-caution">Warnings: {expSelected.warnings.join("; ")}</div>
              )}
              {expSelected.limitations && expSelected.limitations.length > 0 && (
                <div className="text-ink-3">Limitations: {expSelected.limitations.join("; ")}</div>
              )}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(expSelected.safety_flags || {}).map(([k, v]) => (
                  <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                    {k.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              {/* Verify experiment */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-line/30">
                <button onClick={handleExpVerify} disabled={expLoading === "verify"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
                  {expLoading === "verify" ? "Verifying..." : "Verify Linked Export"}
                </button>
              </div>
              {expVerifyResult && (
                <div className="p-2 rounded-md bg-surface-3 text-[10px] space-y-1">
                  <div className="font-medium text-ink">Linked Export Verification</div>
                  <div>Status: <span className={expVerifyResult.healthy ? "text-pos" : "text-caution"}>{expVerifyResult.healthy ? "healthy" : "warnings"}</span></div>
                  {expVerifyResult.warnings.length > 0 && <div className="text-caution">{expVerifyResult.warnings.join("; ")}</div>}
                </div>
              )}

              {/* Lifecycle state update */}
              <div className="pt-2 border-t border-line/30 space-y-2">
                <div className="text-[10px] text-ink-3 font-medium">Update Lifecycle State</div>
                <div className="flex flex-wrap gap-2 items-end">
                  <select value={expStateValue} onChange={(e) => setExpStateValue(e.target.value as ExperimentLifecycleState)}
                    className="px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none">
                    <option value="planned">planned</option>
                    <option value="running_offline">running_offline</option>
                    <option value="completed">completed</option>
                    <option value="failed">failed</option>
                    <option value="archived">archived</option>
                  </select>
                  <input type="text" value={expStateReason} onChange={(e) => setExpStateReason(e.target.value)}
                    placeholder="Reason (optional)"
                    className="flex-1 min-w-[120px] px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
                </div>
                <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                  <input type="checkbox" checked={expStateAck} onChange={(e) => setExpStateAck(e.target.checked)} className="rounded" />
                  <span className="text-ink-3">I acknowledge this updates the experiment state (tracking label only, does not trigger execution)</span>
                </label>
                <button onClick={handleExpStateUpdate} disabled={!expStateAck || expLoading === "state"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-primary/20 text-primary hover:bg-primary/30 disabled:opacity-40 transition-colors">
                  {expLoading === "state" ? "Updating..." : "Update State"}
                </button>
              </div>

              {/* Result import */}
              <div className="pt-2 border-t border-line/30 space-y-2">
                <div className="text-[10px] text-ink-3 font-medium">Import Result Metadata</div>
                <p className="text-[9px] text-ink-4">Metadata-only import -- no executable code, no file uploads. Offline research results only.</p>
                <input type="text" value={expResultSummary} onChange={(e) => setExpResultSummary(e.target.value)}
                  placeholder="Result summary (text)"
                  className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
                <textarea value={expResultMetrics} onChange={(e) => setExpResultMetrics(e.target.value)} rows={2}
                  placeholder='{"sharpe_ratio": 1.23, "max_drawdown": -0.05}'
                  className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink font-mono focus:border-primary focus:outline-none resize-y" />
                <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                  <input type="checkbox" checked={expResultAck} onChange={(e) => setExpResultAck(e.target.checked)} className="rounded" />
                  <span className="text-ink-3">I acknowledge this is a metadata-only offline result import</span>
                </label>
                <button onClick={handleExpResultImport} disabled={!expResultAck || expLoading === "results"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-primary/20 text-primary hover:bg-primary/30 disabled:opacity-40 transition-colors">
                  {expLoading === "results" ? "Importing..." : "Import Results"}
                </button>
              </div>
            </motion.div>
          </div>
        )}

        {/* Rebuild experiment registry */}
        <div className="pt-2 border-t border-line/30 mt-3">
          <div className="text-[10px] text-ink-3 font-medium mb-1">Rebuild Experiment Registry</div>
          <label className="flex items-center gap-1.5 cursor-pointer text-[10px] mb-1.5">
            <input type="checkbox" checked={expRebuildAck} onChange={(e) => setExpRebuildAck(e.target.checked)} className="rounded" />
            <span className="text-ink-3">I acknowledge this recreates the experiment registry (metadata reset)</span>
          </label>
          <button onClick={handleExpRebuildRegistry} disabled={!expRebuildAck || expLoading === "rebuild"}
            className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
            {expLoading === "rebuild" ? "Rebuilding..." : "Rebuild Registry"}
          </button>
        </div>
      </GlassCard>
    </AnimatePresence>
  );
}
