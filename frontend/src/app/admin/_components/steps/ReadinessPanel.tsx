"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../../_context/AdminContext";
import { GlassCard } from "../GlassCard";
import { Icon } from "@/components/icons/Icon";
import {
  createFinrlxResearchReadiness,
  getFinrlxResearchReadiness,
  updateFinrlxResearchReadinessState,
  archiveFinrlxResearchReadiness,
  verifyFinrlxResearchReadiness,
  ReadinessReview,
  ReadinessVerifyResult,
  ReadinessState,
  ReadinessFinding,
} from "@/services/api";

export function ReadinessPanel() {
  const {
    cmpList,
    rdList,
    refreshReadiness,
    pipelineIds,
    setPipelineId,
  } = useAdmin();

  // ── Create readiness form ──
  const [rdName, setRdName] = useState("Research readiness review");
  const [rdCmpId, setRdCmpId] = useState(pipelineIds.comparisonId || "");
  const [rdNotes, setRdNotes] = useState("");
  const [rdAck, setRdAck] = useState(false);
  const [rdCreateLoading, setRdCreateLoading] = useState(false);
  const [rdCreateError, setRdCreateError] = useState<string | null>(null);
  const [rdCreateSuccess, setRdCreateSuccess] = useState<string | null>(null);

  // ── Selected readiness detail ──
  const [rdSelected, setRdSelected] = useState<ReadinessReview | null>(null);
  const [rdVerifyResult, setRdVerifyResult] = useState<ReadinessVerifyResult | null>(null);
  const [rdStateValue, setRdStateValue] = useState<ReadinessState>("draft");
  const [rdStateAck, setRdStateAck] = useState(false);
  const [rdStateReason, setRdStateReason] = useState("");
  const [rdArchiveAck, setRdArchiveAck] = useState(false);
  const [rdLoading, setRdLoading] = useState<string | null>(null);
  const [rdError, setRdError] = useState<string | null>(null);
  const [rdSuccess, setRdSuccess] = useState<string | null>(null);

  // Effective comparison ID: use local or fall back to pipeline context
  const effectiveCmpId = rdCmpId || pipelineIds.comparisonId;

  // ── Callbacks ──
  const handleCreateReadiness = useCallback(async () => {
    if (!rdAck || !rdName.trim() || !effectiveCmpId.trim()) return;
    setRdCreateLoading(true);
    setRdCreateError(null);
    setRdCreateSuccess(null);
    try {
      const res = await createFinrlxResearchReadiness({
        name: rdName.trim(),
        linked_comparison_id: effectiveCmpId.trim(),
        operator_notes: rdNotes,
        research_acknowledgement: true,
      });
      if (res.data?.readiness_id) {
        setRdCreateSuccess(`Readiness ${res.data.readiness_id.slice(0, 8)} created.`);
        setRdAck(false);
        setPipelineId("readinessId", res.data.readiness_id);
        refreshReadiness();
      }
    } catch (e: unknown) {
      setRdCreateError(e instanceof Error ? e.message : "Failed");
    } finally {
      setRdCreateLoading(false);
    }
  }, [rdAck, rdName, effectiveCmpId, rdNotes, refreshReadiness, setPipelineId]);

  const selectReadiness = useCallback(async (rv: ReadinessReview) => {
    setRdSelected(null);
    setRdVerifyResult(null);
    setRdStateAck(false);
    setRdArchiveAck(false);
    setRdError(null);
    setRdSuccess(null);
    try {
      const res = await getFinrlxResearchReadiness(rv.readiness_id);
      if (res.data) {
        setRdSelected(res.data);
        setRdStateValue(res.data.readiness_state);
      }
    } catch { /* graceful */ }
  }, []);

  const handleRdVerify = useCallback(async () => {
    if (!rdSelected) return;
    setRdLoading("verify");
    setRdError(null);
    setRdVerifyResult(null);
    try {
      const res = await verifyFinrlxResearchReadiness(rdSelected.readiness_id);
      if (res.data) setRdVerifyResult(res.data);
    } catch (e: unknown) {
      setRdError(e instanceof Error ? e.message : "Verify failed");
    } finally {
      setRdLoading(null);
    }
  }, [rdSelected]);

  const handleRdStateUpdate = useCallback(async () => {
    if (!rdSelected || !rdStateAck) return;
    setRdLoading("state");
    setRdError(null);
    setRdSuccess(null);
    try {
      await updateFinrlxResearchReadinessState(rdSelected.readiness_id, {
        readiness_state: rdStateValue,
        acknowledgement: true,
        reason: rdStateReason || undefined,
      });
      setRdSuccess(`State updated to ${rdStateValue}.`);
      setRdStateAck(false);
      refreshReadiness();
      selectReadiness({ ...rdSelected, readiness_state: rdStateValue });
    } catch (e: unknown) {
      setRdError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setRdLoading(null);
    }
  }, [rdSelected, rdStateValue, rdStateAck, rdStateReason, refreshReadiness, selectReadiness]);

  const handleRdArchive = useCallback(async () => {
    if (!rdSelected || !rdArchiveAck) return;
    setRdLoading("archive");
    setRdError(null);
    setRdSuccess(null);
    try {
      await archiveFinrlxResearchReadiness(rdSelected.readiness_id, { acknowledgement: true });
      setRdSuccess("Readiness review archived.");
      setRdArchiveAck(false);
      refreshReadiness();
      selectReadiness({ ...rdSelected, readiness_state: "archived" });
    } catch (e: unknown) {
      setRdError(e instanceof Error ? e.message : "Archive failed");
    } finally {
      setRdLoading(null);
    }
  }, [rdSelected, rdArchiveAck, refreshReadiness, selectReadiness]);

  return (
    <AnimatePresence mode="wait">
      <GlassCard>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="shield" size={15} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Research Readiness Review</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">research-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">does not imply production suitability</span>
        </div>
        <p className="text-[10px] text-ink-4 mb-3">
          Assess whether a research package has enough evidence for deeper research review. Not used by production decisions.
        </p>

        {/* Create readiness form */}
        <div className="space-y-2 mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Review name</label>
              <input type="text" value={rdName} onChange={(e) => setRdName(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Linked comparison ID</label>
              <select
                value={effectiveCmpId}
                onChange={(e) => setRdCmpId(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink font-mono focus:border-primary focus:outline-none"
              >
                <option value="">Select a comparison...</option>
                {cmpList.map((cmp) => (
                  <option key={cmp.comparison_id} value={cmp.comparison_id}>
                    {cmp.comparison_id.slice(0, 8)} - {cmp.name} ({cmp.experiment_ids?.length} exp, {cmp.lifecycle_state})
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-0.5">Operator notes</label>
            <input type="text" value={rdNotes} onChange={(e) => setRdNotes(e.target.value)} placeholder="Research review notes"
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div className="rounded-lg border border-line bg-surface-2 p-3">
            <label className="flex items-start gap-2 text-[11px] text-ink-2 cursor-pointer">
              <input type="checkbox" checked={rdAck} onChange={(e) => setRdAck(e.target.checked)} className="rounded mt-0.5" />
              <span>I understand this creates a <strong className="text-ink">research-only readiness review</strong>. It does not imply production readiness or eligibility for promotion.</span>
            </label>
          </div>
          <button onClick={handleCreateReadiness} disabled={rdCreateLoading || !rdAck || !rdName.trim() || !effectiveCmpId.trim()}
            className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[11px] font-medium hover:opacity-90 transition-opacity disabled:opacity-40">
            {rdCreateLoading ? "Creating..." : "Create Readiness Review"}
          </button>
          {rdCreateError && <div className="p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{rdCreateError}</div>}
          {rdCreateSuccess && <div className="p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{rdCreateSuccess}</div>}
        </div>

        {/* Readiness list */}
        {rdList.length > 0 && (
          <div className="border-t border-line pt-3 mb-3">
            <h4 className="text-[12px] font-semibold text-ink mb-2">Readiness Registry ({rdList.length})</h4>
            <div className="space-y-1">
              {rdList.map((rv) => (
                <button key={rv.readiness_id} onClick={() => selectReadiness(rv)}
                  className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                    rdSelected?.readiness_id === rv.readiness_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                  }`}>
                  <span className="font-mono text-ink-2">{rv.readiness_id?.slice(0, 8)}</span>
                  <span className="text-ink font-medium truncate max-w-[150px]">{rv.name}</span>
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                    rv.readiness_state === "research_review_ready" ? "bg-pos/10 text-pos" :
                    rv.readiness_state === "needs_more_evidence" ? "bg-caution/10 text-caution" :
                    rv.readiness_state === "archived" ? "bg-surface-3 text-ink-4" :
                    "bg-primary/10 text-primary"
                  }`}>{rv.readiness_state?.replace(/_/g, " ")}</span>
                  <span className="text-ink-4 ml-auto">{rv.created_at?.slice(0, 19)}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected readiness detail */}
        {rdSelected && (
          <div className="border-t border-line pt-3">
            {rdError && <div className="mb-2 p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{rdError}</div>}
            {rdSuccess && <div className="mb-2 p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{rdSuccess}</div>}

            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2">
              <div className="font-semibold text-[11px] text-ink mb-1">Readiness Detail</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div><span className="text-ink-4">ID:</span> <span className="font-mono text-ink-2 break-all">{rdSelected.readiness_id}</span></div>
                <div><span className="text-ink-4">State:</span> <span className={
                  rdSelected.readiness_state === "research_review_ready" ? "text-pos" :
                  rdSelected.readiness_state === "needs_more_evidence" ? "text-caution" : "text-ink"
                }>{rdSelected.readiness_state?.replace(/_/g, " ")}</span></div>
                <div><span className="text-ink-4">Comparison:</span> <span className="font-mono text-ink-2 break-all">{rdSelected.linked_comparison_id}</span></div>
                <div><span className="text-ink-4">Experiments:</span> <span className="text-ink">{rdSelected.linked_experiment_ids?.length || 0}</span></div>
                {rdSelected.suggested_readiness_state && (
                  <div className="sm:col-span-2"><span className="text-ink-4">Suggested state:</span> <span className="text-primary font-medium">{rdSelected.suggested_readiness_state?.replace(/_/g, " ")}</span></div>
                )}
              </div>
              {rdSelected.operator_notes && <div><span className="text-ink-4">Notes:</span> <span className="text-ink">{rdSelected.operator_notes}</span></div>}

              {/* Checklist */}
              {rdSelected.checklist && (
                <div className="pt-2 border-t border-line/30">
                  <div className="text-[10px] text-ink-3 font-medium mb-1">Evidence Checklist</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                    {Object.entries(rdSelected.checklist).map(([k, v]) => (
                      <div key={k} className="flex items-center gap-1.5">
                        <span className={`w-2 h-2 rounded-full ${v ? "bg-pos" : "bg-ink-4"}`} />
                        <span className="text-[9px] text-ink-2">{k.replace(/_/g, " ")}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Findings */}
              {rdSelected.readiness_findings && rdSelected.readiness_findings.length > 0 && (
                <div className="pt-2 border-t border-line/30">
                  <div className="text-[10px] text-ink-3 font-medium mb-1">Readiness Findings</div>
                  {rdSelected.readiness_findings.map((f: ReadinessFinding) => (
                    <div key={f.finding_id} className={`p-1.5 rounded mb-1 text-[9px] ${
                      f.severity === "blocking" ? "bg-breach/10 text-breach" :
                      f.severity === "warning" ? "bg-caution/10 text-caution" :
                      "bg-surface-3 text-ink-3"
                    }`}>
                      <span className="font-medium">[{f.severity}]</span> {f.message}
                      {f.operator_action && <span className="text-ink-4 ml-1">-- {f.operator_action}</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Safety flags */}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(rdSelected.safety_flags || {}).map(([k, v]) => (
                  <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                    {k.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              {/* Verify */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-line/30">
                <button onClick={handleRdVerify} disabled={rdLoading === "verify"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
                  {rdLoading === "verify" ? "Verifying..." : "Verify Readiness"}
                </button>
              </div>
              {rdVerifyResult && (
                <div className="p-2 rounded-md bg-surface-3 text-[10px] space-y-1">
                  <div className="font-medium text-ink">Readiness Verification</div>
                  <div>Status: <span className={rdVerifyResult.healthy ? "text-pos" : "text-caution"}>{rdVerifyResult.healthy ? "healthy" : "warnings"}</span></div>
                  {rdVerifyResult.warnings.length > 0 && <div className="text-caution">{rdVerifyResult.warnings.join("; ")}</div>}
                </div>
              )}

              {/* State update */}
              <div className="pt-2 border-t border-line/30 space-y-2">
                <div className="text-[10px] text-ink-3 font-medium">Update Readiness State</div>
                <div className="flex flex-wrap gap-2 items-end">
                  <select value={rdStateValue} onChange={(e) => setRdStateValue(e.target.value as ReadinessState)}
                    className="px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none">
                    <option value="draft">draft</option>
                    <option value="needs_more_evidence">needs more evidence</option>
                    <option value="research_review_ready">research review ready</option>
                    <option value="archived">archived</option>
                  </select>
                  <input type="text" value={rdStateReason} onChange={(e) => setRdStateReason(e.target.value)} placeholder="Reason (optional)"
                    className="flex-1 min-w-[120px] px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
                </div>
                <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                  <input type="checkbox" checked={rdStateAck} onChange={(e) => setRdStateAck(e.target.checked)} className="rounded" />
                  <span className="text-ink-3">I acknowledge this state change (research review only, does not affect production)</span>
                </label>
                <button onClick={handleRdStateUpdate} disabled={!rdStateAck || rdLoading === "state"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-primary/20 text-primary hover:bg-primary/30 disabled:opacity-40 transition-colors">
                  {rdLoading === "state" ? "Updating..." : "Update State"}
                </button>
              </div>

              {/* Archive */}
              {rdSelected.readiness_state !== "archived" && (
                <div className="pt-2 border-t border-line/30 space-y-2">
                  <div className="text-[10px] text-ink-3 font-medium">Archive Review</div>
                  <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                    <input type="checkbox" checked={rdArchiveAck} onChange={(e) => setRdArchiveAck(e.target.checked)} className="rounded" />
                    <span className="text-ink-3">I acknowledge this archives the review (does not delete data)</span>
                  </label>
                  <button onClick={handleRdArchive} disabled={!rdArchiveAck || rdLoading === "archive"}
                    className="px-3 py-1 rounded-md text-[10px] font-medium bg-caution/20 text-caution hover:bg-caution/30 disabled:opacity-40 transition-colors">
                    {rdLoading === "archive" ? "Archiving..." : "Archive"}
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </GlassCard>
    </AnimatePresence>
  );
}
