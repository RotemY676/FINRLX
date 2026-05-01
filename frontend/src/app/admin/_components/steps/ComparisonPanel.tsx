"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../../_context/AdminContext";
import { GlassCard } from "../GlassCard";
import { Icon } from "@/components/icons/Icon";
import {
  createFinrlxExperimentComparison,
  getFinrlxExperimentComparison,
  archiveFinrlxExperimentComparison,
  verifyFinrlxExperimentComparison,
  ExperimentComparison,
  ComparisonVerifyResult,
} from "@/services/api";

export function ComparisonPanel() {
  const {
    expList,
    cmpList,
    refreshComparisons,
    pipelineIds,
    setPipelineId,
  } = useAdmin();

  // ── Create comparison form ──
  const [cmpName, setCmpName] = useState("Offline experiment comparison");
  const [cmpSelectedExpIds, setCmpSelectedExpIds] = useState<string[]>(pipelineIds.experimentIds.length > 0 ? [...pipelineIds.experimentIds] : []);
  const [cmpPriority, setCmpPriority] = useState("sharpe_ratio, max_drawdown, total_return");
  const [cmpNotes, setCmpNotes] = useState("");
  const [cmpAck, setCmpAck] = useState(false);
  const [cmpCreateLoading, setCmpCreateLoading] = useState(false);
  const [cmpCreateError, setCmpCreateError] = useState<string | null>(null);
  const [cmpCreateSuccess, setCmpCreateSuccess] = useState<string | null>(null);

  // ── Selected comparison detail ──
  const [cmpSelected, setCmpSelected] = useState<ExperimentComparison | null>(null);
  const [cmpVerifyResult, setCmpVerifyResult] = useState<ComparisonVerifyResult | null>(null);
  const [cmpArchiveAck, setCmpArchiveAck] = useState(false);
  const [cmpArchiveReason, setCmpArchiveReason] = useState("");
  const [cmpLoading, setCmpLoading] = useState<string | null>(null);
  const [cmpError, setCmpError] = useState<string | null>(null);
  const [cmpSuccess, setCmpSuccess] = useState<string | null>(null);

  // ── Help popup ──
  const [showHelp, setShowHelp] = useState(false);

  // Toggle experiment selection for multi-select
  const toggleExpId = (expId: string) => {
    setCmpSelectedExpIds(prev =>
      prev.includes(expId)
        ? prev.filter(id => id !== expId)
        : [...prev, expId]
    );
  };

  // Effective experiment IDs: use selected or fall back to pipeline context
  const effectiveExpIds = cmpSelectedExpIds.length > 0 ? cmpSelectedExpIds : pipelineIds.experimentIds;

  // ── Callbacks ──
  const handleCreateComparison = useCallback(async () => {
    if (!cmpAck || !cmpName.trim() || effectiveExpIds.length < 2) return;
    setCmpCreateLoading(true);
    setCmpCreateError(null);
    setCmpCreateSuccess(null);
    const priority = cmpPriority ? cmpPriority.split(",").map(s => s.trim()).filter(Boolean) : [];
    try {
      const res = await createFinrlxExperimentComparison({
        name: cmpName.trim(),
        experiment_ids: effectiveExpIds,
        metric_priority: priority,
        notes: cmpNotes,
        research_acknowledgement: true,
      });
      if (res.data?.comparison_id) {
        setCmpCreateSuccess(`Comparison ${res.data.comparison_id.slice(0, 8)} created.`);
        setCmpAck(false);
        setPipelineId("comparisonId", res.data.comparison_id);
        refreshComparisons();
      }
    } catch (e: unknown) {
      setCmpCreateError(e instanceof Error ? e.message : "Create comparison failed");
    } finally {
      setCmpCreateLoading(false);
    }
  }, [cmpAck, cmpName, effectiveExpIds, cmpPriority, cmpNotes, refreshComparisons, setPipelineId]);

  const selectComparison = useCallback(async (cmp: ExperimentComparison) => {
    setCmpSelected(null);
    setCmpVerifyResult(null);
    setCmpArchiveAck(false);
    setCmpArchiveReason("");
    setCmpError(null);
    setCmpSuccess(null);
    try {
      const res = await getFinrlxExperimentComparison(cmp.comparison_id);
      if (res.data) setCmpSelected(res.data);
    } catch { /* graceful */ }
  }, []);

  const handleCmpVerify = useCallback(async () => {
    if (!cmpSelected) return;
    setCmpLoading("verify");
    setCmpError(null);
    setCmpVerifyResult(null);
    try {
      const res = await verifyFinrlxExperimentComparison(cmpSelected.comparison_id);
      if (res.data) setCmpVerifyResult(res.data);
    } catch (e: unknown) {
      setCmpError(e instanceof Error ? e.message : "Verify failed");
    } finally {
      setCmpLoading(null);
    }
  }, [cmpSelected]);

  const handleCmpArchive = useCallback(async () => {
    if (!cmpSelected || !cmpArchiveAck) return;
    setCmpLoading("archive");
    setCmpError(null);
    setCmpSuccess(null);
    try {
      await archiveFinrlxExperimentComparison(cmpSelected.comparison_id, {
        acknowledgement: true,
        reason: cmpArchiveReason || undefined,
      });
      setCmpSuccess("Comparison archived.");
      setCmpArchiveAck(false);
      refreshComparisons();
      selectComparison({ ...cmpSelected, lifecycle_state: "archived" });
    } catch (e: unknown) {
      setCmpError(e instanceof Error ? e.message : "Archive failed");
    } finally {
      setCmpLoading(null);
    }
  }, [cmpSelected, cmpArchiveAck, cmpArchiveReason, refreshComparisons, selectComparison]);

  return (
    <AnimatePresence mode="wait">
      <GlassCard>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="compare" size={15} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Offline Experiment Comparison Workbench</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">research-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">metadata-only comparison</span>
          <button onClick={() => setShowHelp(true)} className="ml-auto p-1.5 rounded-lg hover:bg-surface-2 text-ink-4 hover:text-ink transition-colors" title="Help">
            <Icon name="info" size={16} />
          </button>
        </div>
        <p className="text-[10px] text-ink-4 mb-3">
          Compare offline research experiments using imported result metadata. Numeric metric sorting only -- does not imply production suitability. Not eligible for promotion.
        </p>

        {/* Numbered sub-steps guide */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 mb-4">
          {[
            { num: 1, text: "Select at least 2 experiments with imported results to compare." },
            { num: 2, text: "Set metric priority to control which metrics matter most in the ranking." },
            { num: 3, text: "Create the comparison and review the ranked metrics and experiment snapshots." },
          ].map(s => (
            <div key={s.num} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-surface-2/60 border border-line/30">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-[11px] font-bold shrink-0">{s.num}</span>
              <span className="text-[11px] text-ink-2 leading-relaxed">{s.text}</span>
            </div>
          ))}
        </div>

        {/* Create comparison form */}
        <div className="space-y-2 mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] text-ink-3 font-medium block mb-0.5">Comparison name</label>
              <input type="text" value={cmpName} onChange={(e) => setCmpName(e.target.value)}
                title="A descriptive name for this comparison. Helps identify it in the registry."
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[11px] text-ink-3 font-medium block mb-0.5">Metric priority (comma-separated)</label>
              <input type="text" value={cmpPriority} onChange={(e) => setCmpPriority(e.target.value)}
                placeholder="sharpe_ratio, max_drawdown"
                title="Comma-separated list of metrics to prioritize in ranking. The first metric is most important."
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
          </div>

          {/* Multi-select experiment list */}
          <div>
            <label className="text-[11px] text-ink-3 font-medium block mb-0.5">Experiment IDs (select at least 2)</label>
            {expList.length > 0 ? (
              <div className="max-h-[140px] overflow-y-auto border border-line rounded-md bg-surface" title="Select experiments to include in this comparison. Need at least 2 with imported results.">
                {expList.map((exp) => (
                  <label key={exp.experiment_id}
                    className={`flex items-center gap-2 px-2.5 py-1.5 text-[10px] cursor-pointer border-b border-line/30 last:border-b-0 transition-colors ${
                      effectiveExpIds.includes(exp.experiment_id) ? "bg-primary/5" : "hover:bg-surface-2"
                    }`}>
                    <input
                      type="checkbox"
                      checked={effectiveExpIds.includes(exp.experiment_id)}
                      onChange={() => toggleExpId(exp.experiment_id)}
                      className="rounded"
                    />
                    <span className="font-mono text-ink-2">{exp.experiment_id?.slice(0, 8)}</span>
                    <span className="text-ink font-medium truncate max-w-[120px]">{exp.name}</span>
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                      exp.lifecycle_state === "completed" ? "bg-pos/10 text-pos" :
                      exp.lifecycle_state === "failed" ? "bg-breach/10 text-breach" :
                      "bg-surface-3 text-ink-4"
                    }`}>{exp.lifecycle_state}</span>
                    {exp.result_summary && <span className="text-ink-4">has results</span>}
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-[10px] text-ink-4 py-2">No experiments available. Create experiments first.</p>
            )}
            {effectiveExpIds.length > 0 && effectiveExpIds.length < 2 && (
              <p className="text-[9px] text-caution mt-1">Select at least 2 experiments for comparison.</p>
            )}
            {effectiveExpIds.length >= 2 && (
              <p className="text-[9px] text-pos mt-1">{effectiveExpIds.length} experiments selected.</p>
            )}
          </div>

          <div>
            <label className="text-[11px] text-ink-3 font-medium block mb-0.5">Notes</label>
            <input type="text" value={cmpNotes} onChange={(e) => setCmpNotes(e.target.value)}
              placeholder="Research comparison notes"
              title="Optional notes about the purpose or context of this comparison."
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
          </div>

          <div className="rounded-lg border border-line bg-surface-2 p-3">
            <label className="flex items-start gap-2 text-[11px] text-ink-2 cursor-pointer">
              <input type="checkbox" checked={cmpAck} onChange={(e) => setCmpAck(e.target.checked)} className="rounded mt-0.5" />
              <span>
                I understand this creates a <strong className="text-ink">research-only offline comparison</strong>.
                It does not run training, benchmarks, or affect production recommendations.
              </span>
            </label>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleCreateComparison}
              disabled={cmpCreateLoading || !cmpAck || !cmpName.trim() || effectiveExpIds.length < 2}
              className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[11px] font-medium hover:opacity-90 transition-opacity disabled:opacity-40">
              {cmpCreateLoading ? "Creating..." : "Create Comparison"}
            </button>
          </div>
          {cmpCreateError && <div className="p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{cmpCreateError}</div>}
          {cmpCreateSuccess && <div className="p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{cmpCreateSuccess}</div>}
        </div>

        {/* Comparison list */}
        {cmpList.length > 0 && (
          <div className="border-t border-line pt-3 mb-3">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h4 className="text-[12px] font-semibold text-ink">Comparison Registry</h4>
              <span className="text-[10px] text-ink-4">{cmpList.length} comparison{cmpList.length !== 1 ? "s" : ""}</span>
            </div>
            <div className="space-y-1">
              {cmpList.map((cmp) => (
                <button key={cmp.comparison_id} onClick={() => selectComparison(cmp)}
                  className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                    cmpSelected?.comparison_id === cmp.comparison_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                  }`}>
                  <span className="font-mono text-ink-2 break-all">{cmp.comparison_id?.slice(0, 8)}</span>
                  <span className="text-ink font-medium truncate max-w-[150px]">{cmp.name}</span>
                  <span className="text-ink-3">{cmp.experiment_ids?.length} experiments</span>
                  <span className="text-ink-4">{cmp.comparison_summary?.metric_names?.length || 0} metrics</span>
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                    cmp.lifecycle_state === "active" ? "bg-pos/10 text-pos" : "bg-surface-3 text-ink-4"
                  }`}>{cmp.lifecycle_state}</span>
                  <span className="text-ink-4 ml-auto">{cmp.created_at?.slice(0, 19)}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected comparison detail */}
        {cmpSelected && (
          <div className="border-t border-line pt-3">
            {cmpError && <div className="mb-2 p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{cmpError}</div>}
            {cmpSuccess && <div className="mb-2 p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{cmpSuccess}</div>}

            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2">
              <div className="font-semibold text-[11px] text-ink mb-1">Comparison Detail</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div><span className="text-ink-4">ID:</span> <span className="font-mono text-ink-2 break-all">{cmpSelected.comparison_id}</span></div>
                <div><span className="text-ink-4">State:</span> <span className={cmpSelected.lifecycle_state === "active" ? "text-pos" : "text-ink-3"}>{cmpSelected.lifecycle_state}</span></div>
                <div><span className="text-ink-4">Name:</span> <span className="text-ink">{cmpSelected.name}</span></div>
                <div><span className="text-ink-4">Experiments:</span> <span className="text-ink">{cmpSelected.experiment_ids?.length}</span></div>
              </div>
              {cmpSelected.notes && <div><span className="text-ink-4">Notes:</span> <span className="text-ink">{cmpSelected.notes}</span></div>}

              {/* Experiment snapshots */}
              {cmpSelected.experiment_snapshots && cmpSelected.experiment_snapshots.length > 0 && (
                <div className="pt-2 border-t border-line/30">
                  <div className="text-[10px] text-ink-3 font-medium mb-1">Experiment Snapshots</div>
                  {cmpSelected.experiment_snapshots.map((snap) => (
                    <div key={snap.experiment_id} className="p-2 rounded bg-surface-3 mb-1">
                      <div className="flex flex-wrap gap-2 items-center">
                        <span className="font-mono text-ink-2">{snap.experiment_id?.slice(0, 8)}</span>
                        <span className="text-ink font-medium truncate max-w-[120px]">{snap.name}</span>
                        <span className="text-ink-4">{snap.lifecycle_state}</span>
                        <span className="text-ink-4">export:{snap.linked_export_id?.slice(0, 8)}</span>
                      </div>
                      {snap.result_metrics && Object.keys(snap.result_metrics).length > 0 && (
                        <div className="mt-1 text-[9px] text-ink-3">
                          {Object.entries(snap.result_metrics).map(([k, v]) => (
                            <span key={k} className="mr-2">{k}: <span className="font-mono text-ink-2">{String(v)}</span></span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Ranked metrics */}
              {cmpSelected.comparison_summary?.ranked_metrics && Object.keys(cmpSelected.comparison_summary.ranked_metrics).length > 0 && (
                <div className="pt-2 border-t border-line/30">
                  <div className="text-[10px] text-ink-3 font-medium mb-1">Numeric Metric Comparison (descending sort, offline only)</div>
                  {Object.entries(cmpSelected.comparison_summary.ranked_metrics).map(([metric, entries]) => (
                    <div key={metric} className="mb-1.5">
                      <div className="text-[9px] text-ink-4 font-medium">{metric}</div>
                      <div className="flex flex-wrap gap-2">
                        {(entries as Array<{experiment_id: string; value: number}>).map((e, i) => (
                          <span key={e.experiment_id} className={`font-mono text-[9px] ${i === 0 ? "text-primary" : "text-ink-2"}`}>
                            {e.experiment_id?.slice(0, 8)}: {e.value}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                  <p className="text-[8px] text-ink-4 mt-1">Numeric sorting only. Does not imply production suitability.</p>
                </div>
              )}

              {/* Warnings and limitations */}
              {cmpSelected.warnings && cmpSelected.warnings.length > 0 && (
                <div className="text-caution text-[9px]">Warnings: {cmpSelected.warnings.join("; ")}</div>
              )}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(cmpSelected.safety_flags || {}).map(([k, v]) => (
                  <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                    {k.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              {/* Verify and archive controls */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-line/30">
                <button onClick={handleCmpVerify} disabled={cmpLoading === "verify"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
                  {cmpLoading === "verify" ? "Verifying..." : "Verify Comparison"}
                </button>
              </div>
              {cmpVerifyResult && (
                <div className="p-2 rounded-md bg-surface-3 text-[10px] space-y-1">
                  <div className="font-medium text-ink">Comparison Verification</div>
                  <div>Status: <span className={cmpVerifyResult.healthy ? "text-pos" : "text-caution"}>{cmpVerifyResult.healthy ? "healthy" : "warnings"}</span></div>
                  {cmpVerifyResult.warnings.length > 0 && <div className="text-caution">{cmpVerifyResult.warnings.join("; ")}</div>}
                </div>
              )}

              {cmpSelected.lifecycle_state === "active" && (
                <div className="pt-2 border-t border-line/30 space-y-2">
                  <div className="text-[10px] text-ink-3 font-medium">Archive Comparison</div>
                  <input type="text" value={cmpArchiveReason} onChange={(e) => setCmpArchiveReason(e.target.value)}
                    placeholder="Reason (optional)"
                    className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
                  <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                    <input type="checkbox" checked={cmpArchiveAck} onChange={(e) => setCmpArchiveAck(e.target.checked)} className="rounded" />
                    <span className="text-ink-3">I acknowledge this archives the comparison (does not delete data or affect experiments)</span>
                  </label>
                  <button onClick={handleCmpArchive} disabled={!cmpArchiveAck || cmpLoading === "archive"}
                    className="px-3 py-1 rounded-md text-[10px] font-medium bg-caution/20 text-caution hover:bg-caution/30 disabled:opacity-40 transition-colors">
                    {cmpLoading === "archive" ? "Archiving..." : "Archive"}
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}

        {/* Help modal */}
        <AnimatePresence>
          {showHelp && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
              onClick={() => setShowHelp(false)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 10 }}
                className="bg-surface border border-line rounded-xl shadow-xl max-w-lg w-full mx-4 p-5 max-h-[80vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-[14px] font-semibold text-ink">Comparison Help</h3>
                  <button onClick={() => setShowHelp(false)} className="p-1 rounded-lg hover:bg-surface-2 text-ink-4 hover:text-ink transition-colors">
                    <Icon name="close" size={16} />
                  </button>
                </div>
                <div className="space-y-3 text-[12px] text-ink-2 leading-relaxed">
                  <p><strong className="text-ink">What is this screen?</strong></p>
                  <p>The Comparison panel lets you compare multiple research experiments side-by-side using their imported result metrics. The system ranks experiments by each metric to help identify the strongest candidates.</p>
                  <p><strong className="text-ink">Steps:</strong></p>
                  <ol className="list-decimal list-inside space-y-1.5">
                    <li><strong>Select Experiments</strong> — Choose at least 2 experiments with imported results. Experiments without results cannot be compared.</li>
                    <li><strong>Set Metric Priority</strong> — List the metrics that matter most, comma-separated. The first metric is the primary sort key.</li>
                    <li><strong>Create Comparison</strong> — The system creates snapshot copies of each experiment's metrics for fair comparison.</li>
                    <li><strong>Review Rankings</strong> — Metrics are sorted in descending order (highest is best, except drawdown where lowest is best).</li>
                    <li><strong>Verify</strong> — Use the verify button to check that all linked experiments and their data sources are intact.</li>
                  </ol>
                  <p><strong className="text-ink">Field Reference:</strong></p>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong>Ranked metrics</strong> — Numeric values sorted descending. The top-ranked experiment ID appears first.</li>
                    <li><strong>Experiment snapshots</strong> — Frozen copies of each experiment's state at comparison time.</li>
                    <li><strong>Lifecycle state</strong> — "active" means in use; "archived" means no longer relevant.</li>
                  </ul>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </GlassCard>
    </AnimatePresence>
  );
}
