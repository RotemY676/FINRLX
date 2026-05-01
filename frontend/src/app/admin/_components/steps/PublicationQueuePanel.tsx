"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAdmin } from "../../_context/AdminContext";
import { GlassCard } from "../GlassCard";
import { Icon } from "@/components/icons/Icon";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import {
  KPI_TONE,
  STANCE_STYLE,
  PRIORITY_STYLE,
  FEED_STATUS,
  SEVERITY_STYLE,
  QUEUE_FILTERS,
  AUDIT_SCOPES,
} from "../constants";
import {
  runRLBenchmark,
  fetchRLBenchmarks,
  fetchRLBenchmark,
  fetchRLBenchmarkAudit,
  fetchFinRLXBenchmarkEligibility,
  runFinRLXCandidateBenchmark,
  fetchFinRLXCandidateBenchmarks,
  fetchFinRLXCandidates,
  validateFinRLXResearchArtifact,
  importFinRLXResearchArtifact,
  FinRLXCandidate,
  FinRLXBenchmarkEligibility,
  FinRLXCandidateBenchmarkResponse,
  FinRLXCandidateBenchmarkHistoryItem,
  FinRLXArtifactValidationResult,
  RLBenchmarkReport,
  RLBenchmarkAuditEvent,
} from "@/services/api";

export function PublicationQueuePanel() {
  const {
    ops,
    mlSummary,
    finrlxStatus,
    finrlxDeps,
    benchmarks: ctxBenchmarks,
    selectedBenchmark: ctxSelectedBenchmark,
    selectBenchmark: ctxSelectBenchmark,
    selectedBenchAudit,
    benchAuditEvents: ctxBenchAuditEvents,
    importedCandidates: ctxImportedCandidates,
    filteredQueue,
    filteredAudit,
    queueFilter,
    auditScope,
    actionLoading,
    handleQueueFilter,
    handleAuditScope,
    handleQueueAction,
    drawerIncident,
    setDrawerIncident,
  } = useAdmin();

  // ── Local state for benchmarks (mutable copies for run workflow) ──
  const [benchmarks, setBenchmarks] = useState<RLBenchmarkReport[]>(ctxBenchmarks);
  const [selectedBenchmark, setSelectedBenchmark] = useState<RLBenchmarkReport | null>(ctxSelectedBenchmark);
  const [benchAuditEvents, setBenchAuditEvents] = useState<RLBenchmarkAuditEvent[]>(ctxBenchAuditEvents);
  const [selectedForensicAgent, setSelectedForensicAgent] = useState<string | null>(null);

  // Sync from context
  const effectiveBenchmarks = benchmarks.length > 0 ? benchmarks : ctxBenchmarks;
  const effectiveSelectedBenchmark = selectedBenchmark || ctxSelectedBenchmark;
  const effectiveBenchAuditEvents = benchAuditEvents.length > 0 ? benchAuditEvents : ctxBenchAuditEvents;
  const effectiveSelectedBenchAudit = selectedBenchAudit;

  // ── Benchmark run workflow ──
  const [benchRunName, setBenchRunName] = useState("Offline Agent Comparison");
  const [benchRunStart, setBenchRunStart] = useState("2026-03-15");
  const [benchRunEnd, setBenchRunEnd] = useState("2026-04-15");
  const [benchRunAgents, setBenchRunAgents] = useState<Record<string, boolean>>({
    heuristic_baseline: true, random_valid: true, score_weighted_baseline: true,
  });
  const [benchRunAcknowledged, setBenchRunAcknowledged] = useState(false);
  const [benchRunLoading, setBenchRunLoading] = useState(false);
  const [benchRunError, setBenchRunError] = useState<string | null>(null);
  const [benchRunSuccess, setBenchRunSuccess] = useState<string | null>(null);

  // ── Imported candidate benchmark workflow ──
  const [importedCandidates, setImportedCandidates] = useState<FinRLXCandidate[]>(ctxImportedCandidates);
  const effectiveImportedCandidates = importedCandidates.length > 0 ? importedCandidates : ctxImportedCandidates;
  const [selectedCandidate, setSelectedCandidate] = useState<FinRLXCandidate | null>(null);
  const [candidateEligibility, setCandidateEligibility] = useState<FinRLXBenchmarkEligibility | null>(null);
  const [candidateBenchHistory, setCandidateBenchHistory] = useState<FinRLXCandidateBenchmarkHistoryItem[]>([]);
  const [candBenchName, setCandBenchName] = useState("Imported Candidate Offline Benchmark");
  const [candBenchStart, setCandBenchStart] = useState("2026-03-15");
  const [candBenchEnd, setCandBenchEnd] = useState("2026-04-15");
  const [candBenchBaselines, setCandBenchBaselines] = useState(true);
  const [candBenchAck, setCandBenchAck] = useState(false);
  const [candBenchLoading, setCandBenchLoading] = useState(false);
  const [candBenchError, setCandBenchError] = useState<string | null>(null);
  const [candBenchResult, setCandBenchResult] = useState<FinRLXCandidateBenchmarkResponse | null>(null);

  // ── Artifact import workflow ──
  const [importJson, setImportJson] = useState("");
  const [importSource, setImportSource] = useState("admin_ui");
  const [importNotes, setImportNotes] = useState("");
  const [importValidation, setImportValidation] = useState<FinRLXArtifactValidationResult | null>(null);
  const [importValidateError, setImportValidateError] = useState<string | null>(null);
  const [importAck, setImportAck] = useState(false);
  const [importAckHash, setImportAckHash] = useState<string | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  // ── Candidate selection ──
  const selectCandidate = useCallback(async (c: FinRLXCandidate) => {
    setSelectedCandidate(c);
    setCandidateEligibility(null);
    setCandidateBenchHistory([]);
    setCandBenchResult(null);
    setCandBenchError(null);
    setCandBenchAck(false);
    try {
      const [eligRes, histRes] = await Promise.all([
        fetchFinRLXBenchmarkEligibility(c.id).catch(() => null),
        fetchFinRLXCandidateBenchmarks(c.id).catch(() => null),
      ]);
      if (eligRes?.data) setCandidateEligibility(eligRes.data);
      if (histRes?.data) setCandidateBenchHistory(histRes.data);
    } catch { /* graceful */ }
  }, []);

  const runCandidateBenchmark = useCallback(async () => {
    if (!selectedCandidate || !candBenchAck) return;
    setCandBenchLoading(true);
    setCandBenchError(null);
    setCandBenchResult(null);
    try {
      const res = await runFinRLXCandidateBenchmark(selectedCandidate.id, {
        name: candBenchName,
        start_date: candBenchStart,
        end_date: candBenchEnd,
        include_baselines: candBenchBaselines,
        research_acknowledgement: true,
      });
      if (res.data) {
        setCandBenchResult(res.data);
        const histRes = await fetchFinRLXCandidateBenchmarks(selectedCandidate.id).catch(() => null);
        if (histRes?.data) setCandidateBenchHistory(histRes.data);
      }
    } catch (e: unknown) {
      setCandBenchError(e instanceof Error ? e.message : "Benchmark failed");
    } finally {
      setCandBenchLoading(false);
    }
  }, [selectedCandidate, candBenchName, candBenchStart, candBenchEnd, candBenchBaselines, candBenchAck]);

  const openBenchmarkById = useCallback(async (reportId: string) => {
    try {
      const res = await fetchRLBenchmark(reportId);
      if (res.data) {
        setSelectedBenchmark(res.data);
        ctxSelectBenchmark(res.data);
        document.getElementById("benchmark-drilldown")?.scrollIntoView({ behavior: "smooth" });
      }
    } catch { /* benchmark may not exist */ }
  }, [ctxSelectBenchmark]);

  const handleValidateArtifact = useCallback(async () => {
    setImportValidation(null);
    setImportValidateError(null);
    setImportError(null);
    setImportSuccess(null);
    setImportAck(false);
    setImportAckHash(null);
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(importJson);
    } catch {
      setImportValidateError("Invalid JSON. Please check the artifact text.");
      return;
    }
    try {
      const res = await validateFinRLXResearchArtifact(parsed);
      if (res.data) setImportValidation(res.data);
    } catch (e: unknown) {
      setImportValidateError(e instanceof Error ? e.message : "Validation request failed");
    }
  }, [importJson]);

  const handleImportArtifact = useCallback(async () => {
    if (!importValidation?.valid || !importAck || !importValidation.artifact_hash || importAckHash !== importValidation.artifact_hash) return;
    setImportLoading(true);
    setImportError(null);
    setImportSuccess(null);
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(importJson);
    } catch {
      setImportError("Invalid JSON.");
      setImportLoading(false);
      return;
    }
    try {
      const res = await importFinRLXResearchArtifact({
        artifact: parsed,
        import_acknowledgement: true,
        source: importSource || "admin_ui",
        notes: importNotes || undefined,
      });
      if (res.data?.policy_candidate_id) {
        setImportSuccess(`Imported as candidate ${res.data.policy_candidate_id.slice(0, 8)}`);
        setImportJson("");
        setImportValidation(null);
        setImportAck(false);
        const candRes = await fetchFinRLXCandidates().catch(() => null);
        if (candRes?.data) {
          const imported = candRes.data.filter(c => c.imported_from_artifact);
          setImportedCandidates(imported);
          const newCand = imported.find(c => c.id === res.data.policy_candidate_id);
          if (newCand) selectCandidate(newCand);
        }
      }
    } catch (e: unknown) {
      setImportError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setImportLoading(false);
    }
  }, [importJson, importValidation, importAck, importAckHash, importSource, importNotes, selectCandidate]);

  if (!ops) return null;

  return (
    <AnimatePresence mode="wait">
      <div className="space-y-gap">
        {/* ── KPI Strip ── */}
        {ops.system_kpis.length > 0 && (
          <GlassCard>
            <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {ops.system_kpis.map((kpi) => (
                <div key={kpi.key} className="text-center">
                  <p className={`text-[20px] font-semibold font-mono ${KPI_TONE[kpi.tone] || "text-ink"}`}>{kpi.value}</p>
                  <p className="text-[12px] text-ink-2 font-medium mt-0.5">{kpi.key}</p>
                  {kpi.sub && <p className="text-[10px] text-ink-4">{kpi.sub}</p>}
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* ── ML Observability ── */}
        {mlSummary && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Icon name="compare" size={15} className="text-primary" />
              <h3 className="text-[13px] font-semibold text-ink">ML Observability</h3>
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-caution-soft text-caution-soft-ink">
                Shadow
              </span>
              {!mlSummary.live_pipeline_influence && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">
                  Live influence: Off
                </span>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-4">
              <div className="text-center">
                <p className="text-[11px] text-ink-4 mb-0.5">Model</p>
                <p className="text-[12px] font-medium text-ink font-mono">{mlSummary.model_key}</p>
              </div>
              <div className="text-center">
                <p className="text-[11px] text-ink-4 mb-0.5">Status</p>
                <p className="text-[12px] font-medium text-caution">{mlSummary.status}</p>
              </div>
              <div className="text-center">
                <p className="text-[11px] text-ink-4 mb-0.5">Predictions</p>
                <p className="text-[12px] font-medium text-ink font-mono">{mlSummary.prediction_count}</p>
              </div>
              <div className="text-center">
                <p className="text-[11px] text-ink-4 mb-0.5">Validation</p>
                <p className="text-[12px] font-medium text-ink">{mlSummary.validation_status || "\u2014"}</p>
              </div>
              <div className="text-center">
                <p className="text-[11px] text-ink-4 mb-0.5">Accuracy</p>
                <p className="text-[12px] font-medium text-ink font-mono">
                  {mlSummary.directional_accuracy != null
                    ? `${(mlSummary.directional_accuracy * 100).toFixed(0)}%`
                    : "\u2014"}
                  {mlSummary.validation_sample_count != null && (
                    <span className="text-ink-4 text-[10px] ml-1">n={mlSummary.validation_sample_count}</span>
                  )}
                </p>
              </div>
              <div className="text-center">
                <p className="text-[11px] text-ink-4 mb-0.5">Readiness</p>
                <p className={`text-[12px] font-medium ${
                  mlSummary.promotion_readiness === "eligible_for_review" ? "text-pos" :
                  mlSummary.promotion_readiness === "promising_shadow" ? "text-caution" :
                  "text-ink-3"
                }`}>
                  {mlSummary.promotion_readiness || "\u2014"}
                </p>
              </div>
            </div>
            {mlSummary.total_return_delta != null && (
              <div className="flex items-center gap-4 text-[11px] border-t border-line pt-3 mb-3">
                <span className="text-ink-4">Baseline vs Shadow:</span>
                <span className="font-mono text-ink">
                  Return delta {mlSummary.total_return_delta >= 0 ? "+" : ""}{(mlSummary.total_return_delta * 100).toFixed(2)}%
                </span>
                {mlSummary.sharpe_delta != null && (
                  <span className="font-mono text-ink-3">
                    Sharpe delta {mlSummary.sharpe_delta >= 0 ? "+" : ""}{mlSummary.sharpe_delta.toFixed(2)}
                  </span>
                )}
                {mlSummary.max_drawdown_delta != null && (
                  <span className="font-mono text-ink-3">
                    DD delta {mlSummary.max_drawdown_delta >= 0 ? "+" : ""}{(mlSummary.max_drawdown_delta * 100).toFixed(2)}%
                  </span>
                )}
              </div>
            )}
            {mlSummary.warnings.length > 0 && (
              <div className="space-y-1 border-t border-line pt-3 mb-3">
                {mlSummary.warnings.map((w, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px]">
                    <Icon name={w.level === "warning" ? "alert-triangle" : "info"} size={10}
                      className={w.level === "warning" ? "text-caution" : "text-ink-4"} />
                    <span className={w.level === "warning" ? "text-caution" : "text-ink-3"}>{w.message}</span>
                  </div>
                ))}
              </div>
            )}
            {mlSummary.recommended_operator_action && (
              <div className="flex items-center gap-2 text-[11px] border-t border-line pt-3">
                <span className="text-ink-4">Recommended:</span>
                <span className="font-medium text-ink-2">{mlSummary.recommended_operator_action.replace(/_/g, " ")}</span>
              </div>
            )}
          </GlassCard>
        )}

        {/* ── RL Environment ── */}
        {ops.rl && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Icon name="sparkle" size={15} className="text-accent" />
              <h3 className="text-[13px] font-semibold text-ink">RL Environment</h3>
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">
                Offline / Shadow
              </span>
              {!ops.rl.live_pipeline_influence && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">
                  Live influence: Off
                </span>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3 text-center">
              <div>
                <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_environments}</p>
                <p className="text-[10px] text-ink-4">environments</p>
              </div>
              <div>
                <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_agents}</p>
                <p className="text-[10px] text-ink-4">agents ({ops.rl.trainable_agents} trainable)</p>
              </div>
              <div>
                <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_runs}</p>
                <p className="text-[10px] text-ink-4">simulations</p>
              </div>
              <div>
                <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_policy_snapshots}</p>
                <p className="text-[10px] text-ink-4">policy snapshots</p>
              </div>
              <div>
                <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_benchmarks}</p>
                <p className="text-[10px] text-ink-4">benchmarks</p>
              </div>
              <div>
                <p className="text-[14px] font-semibold text-ink">{ops.rl.latest_benchmark_status || "\u2014"}</p>
                <p className="text-[10px] text-ink-4">latest benchmark</p>
              </div>
              <div>
                <p className="text-[14px] font-semibold text-ink">{ops.rl.latest_training_agent?.replace(/_/g, " ") || "\u2014"}</p>
                <p className="text-[10px] text-ink-4">latest agent</p>
              </div>
            </div>
          </GlassCard>
        )}

        {/* ── FinRL-X Research Spike ── */}
        {finrlxStatus && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Icon name="sparkle" size={15} className="text-accent-2" />
              <h3 className="text-[13px] font-semibold text-ink">FinRL-X Research Spike</h3>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research only</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Offline / Shadow</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 text-center mb-3">
              <div>
                <p className="text-[12px] font-medium text-ink">{finrlxStatus.training_mode}</p>
                <p className="text-[10px] text-ink-4">training mode</p>
              </div>
              <div>
                <p className={`text-[12px] font-medium ${finrlxStatus.finrlx_available ? "text-pos" : "text-caution"}`}>
                  {finrlxStatus.finrlx_available ? "Available" : "Not installed"}
                </p>
                <p className="text-[10px] text-ink-4">FinRL-X status</p>
              </div>
              <div>
                <p className="text-[12px] font-medium text-ink">{finrlxStatus.gpu_required ? "Required" : "Not required"}</p>
                <p className="text-[10px] text-ink-4">GPU</p>
              </div>
              <div>
                <p className={`text-[12px] font-medium ${finrlxStatus.live_pipeline_influence ? "text-breach" : "text-pos"}`}>
                  {finrlxStatus.live_pipeline_influence ? "Active" : "None"}
                </p>
                <p className="text-[10px] text-ink-4">production influence</p>
              </div>
              <div>
                <p className="text-[12px] font-medium text-ink">{finrlxStatus.no_broker_execution ? "None" : "Active"}</p>
                <p className="text-[10px] text-ink-4">broker integration</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {["Promotion", "Publication", "Recommendation", "Overview", "Broker"].map((c) => (
                <span key={c} className="inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium bg-surface-3 text-ink-3">Research guardrail: {c.toLowerCase()} blocked</span>
              ))}
            </div>
            {finrlxStatus.missing_for_real_training?.length > 0 && (
              <div className="rounded-lg border border-caution bg-caution-soft p-2 text-[10px] text-caution-soft-ink mb-2">
                <span className="font-medium">Dependencies needed for real neural training: </span>
                {finrlxStatus.missing_for_real_training.join(", ")}
              </div>
            )}
            <p className="text-[10px] text-ink-4">{finrlxStatus.notes}</p>
            {finrlxDeps && (
              <div className="mt-3 pt-3 border-t border-line">
                <h4 className="text-[11px] font-semibold text-ink mb-2">CPU-Only Neural Dependency Status</h4>
                <div className="flex flex-wrap gap-1.5">
                  {(["numpy", "gymnasium", "stable_baselines3", "torch"] as const).map((lib) => {
                    const avail = (finrlxDeps as unknown as Record<string, unknown>)[`${lib}_available`];
                    return (
                      <span key={lib} className={`inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium ${
                        avail ? "bg-pos-soft text-pos-soft-ink" : "bg-surface-3 text-ink-3"
                      }`}>{lib}: {avail ? "installed" : "missing"}</span>
                    );
                  })}
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium ${
                    finrlxDeps.neural_training_available ? "bg-pos-soft text-pos-soft-ink" : "bg-caution-soft text-caution-soft-ink"
                  }`}>Neural training: {finrlxDeps.neural_training_available ? "available" : "unavailable"}</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium bg-surface-3 text-ink-3">CPU-only mode</span>
                </div>
              </div>
            )}
          </GlassCard>
        )}

        {/* ── Import Research Artifact ── */}
        <GlassCard>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="sparkle" size={15} className="text-accent-2" />
            <h3 className="text-[13px] font-semibold text-ink">Import Research Artifact</h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research only</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Shadow / Offline</span>
          </div>
          <p className="text-[10px] text-ink-4 mb-2">This imports a local research artifact as a shadow-only candidate. It cannot affect recommendations, overview, publication, or broker systems.</p>
          <textarea value={importJson} onChange={e => { setImportJson(e.target.value); setImportValidation(null); setImportValidateError(null); setImportError(null); setImportSuccess(null); setImportAck(false); setImportAckHash(null); }}
            placeholder="Paste research artifact JSON here..."
            className="w-full border border-line rounded-md px-3 py-2 text-[11px] font-mono bg-canvas focus:border-primary focus:outline-none min-h-[80px] max-h-[200px] resize-y mb-2" />
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-[11px] mb-2">
            <div>
              <label className="block text-ink-4 text-[10px] mb-0.5">Source</label>
              <input type="text" value={importSource} onChange={e => { setImportSource(e.target.value); setImportAck(false); setImportAckHash(null); }}
                className="w-full border border-line rounded px-2 py-1 text-[11px] bg-canvas focus:border-primary focus:outline-none" />
            </div>
            <div className="sm:col-span-3">
              <label className="block text-ink-4 text-[10px] mb-0.5">Notes (optional)</label>
              <input type="text" value={importNotes} onChange={e => { setImportNotes(e.target.value); setImportAck(false); setImportAckHash(null); }}
                className="w-full border border-line rounded px-2 py-1 text-[11px] bg-canvas focus:border-primary focus:outline-none" />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <button onClick={handleValidateArtifact} disabled={!importJson.trim()}
              className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-surface-3 text-ink hover:bg-surface-2 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity">
              Validate artifact
            </button>
            {importValidateError && <span className="text-[10px] text-breach">{importValidateError}</span>}
          </div>
          {importValidation && (
            <div className={`rounded-lg border p-2 text-[10px] mb-2 ${importValidation.valid ? "border-pos bg-pos-soft text-pos-soft-ink" : "border-breach bg-breach-soft text-breach-soft-ink"}`}>
              <span className="font-medium">{importValidation.valid ? "Artifact is valid" : "Artifact is invalid"}</span>
              {importValidation.artifact_hash && <span className="ml-2 font-mono text-[9px]">hash: {importValidation.artifact_hash.slice(0, 16)}</span>}
              {importValidation.errors.length > 0 && (
                <ul className="mt-1 list-disc list-inside">{importValidation.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
              )}
              {importValidation.warnings.length > 0 && (
                <ul className="mt-1 list-disc list-inside text-caution-soft-ink">{importValidation.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
              )}
              {importValidation.normalized_artifact_summary && (
                <p className="mt-1 font-mono text-[9px] break-all">{JSON.stringify(importValidation.normalized_artifact_summary)}</p>
              )}
            </div>
          )}
          {importValidation?.valid && (
            <div className="border-t border-line pt-2 mt-2">
              <label className="flex items-center gap-2 text-[10px] text-ink-3 mb-2 cursor-pointer">
                <input type="checkbox" checked={importAck} onChange={e => { setImportAck(e.target.checked); setImportAckHash(e.target.checked && importValidation?.artifact_hash ? importValidation.artifact_hash : null); }} className="rounded" />
                I confirm this is a research-only artifact. It will be imported as a shadow candidate with no production influence.
              </label>
              <button onClick={handleImportArtifact} disabled={importLoading || !importAck || !importValidation?.artifact_hash || importAckHash !== importValidation?.artifact_hash}
                className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-primary text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity">
                {importLoading ? "Importing..." : "Import research artifact"}
              </button>
              {importError && <span className="ml-2 text-[10px] text-breach">{importError}</span>}
              {importSuccess && <span className="ml-2 text-[10px] text-pos font-medium">{importSuccess}</span>}
            </div>
          )}
        </GlassCard>

        {/* ── Imported Research Candidates ── */}
        <GlassCard>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="sparkle" size={15} className="text-accent-2" />
            <h3 className="text-[13px] font-semibold text-ink">Imported Research Candidates</h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research only</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Shadow / Offline</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Not eligible for promotion</span>
          </div>

          {effectiveImportedCandidates.length === 0 ? (
            <p className="text-[11px] text-ink-4 py-2">No imported research candidates yet. Import a local research artifact before benchmarking.</p>
          ) : (
            <div className="space-y-1.5 mb-3">
              {effectiveImportedCandidates.slice(0, 10).map((c) => (
                <button key={c.id} onClick={() => selectCandidate(c)}
                  className={`w-full text-left rounded-md border px-3 py-2 text-[11px] transition-colors ${
                    selectedCandidate?.id === c.id ? "border-primary bg-primary/5" : "border-line hover:bg-surface-2"
                  }`}>
                  <div className="flex flex-wrap items-center justify-between gap-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-ink-2">{c.id.slice(0, 8)}</span>
                      <span className="text-ink-3">{c.policy_type}</span>
                      {c.artifact_hash && <span className="font-mono text-ink-4">#{c.artifact_hash.slice(0, 8)}</span>}
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5">
                      {c.real_neural_training && <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-accent-soft text-accent">neural</span>}
                      {c.artifact_summary?.synthetic_data === true && <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-caution-soft text-caution-soft-ink">synthetic</span>}
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-pos-soft text-pos-soft-ink">isolated</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Selected Candidate Review */}
          {selectedCandidate && (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="border-t border-line pt-3 mt-2 space-y-3">
              <h4 className="text-[12px] font-semibold text-ink">Candidate Review</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-[10px] sm:text-[10px]">
                <div><span className="text-ink-4">ID:</span> <span className="font-mono text-ink-2">{selectedCandidate.id}</span></div>
                <div><span className="text-ink-4">Policy type:</span> <span className="text-ink">{selectedCandidate.policy_type}</span></div>
                <div><span className="text-ink-4">Training mode:</span> <span className="text-ink">{selectedCandidate.training_mode}</span></div>
                <div><span className="text-ink-4">Artifact hash:</span> <span className="font-mono text-ink-2">{selectedCandidate.artifact_hash || "\u2014"}</span></div>
                <div><span className="text-ink-4">Source:</span> <span className="text-ink">{selectedCandidate.source || "\u2014"}</span></div>
                <div><span className="text-ink-4">Created:</span> <span className="text-ink">{selectedCandidate.created_at?.slice(0, 19) || "\u2014"}</span></div>
              </div>
              {selectedCandidate.artifact_summary && (
                <div className="text-[10px]">
                  <span className="text-ink-4">Artifact summary: </span>
                  <span className="font-mono text-ink-3 break-all">{JSON.stringify(selectedCandidate.artifact_summary)}</span>
                </div>
              )}
              {selectedCandidate.notes && (
                <div className="text-[10px]"><span className="text-ink-4">Notes: </span><span className="text-ink-3">{selectedCandidate.notes}</span></div>
              )}
              <div className="flex flex-wrap gap-1.5">
                {candidateEligibility ? (
                  <>
                    {([
                      ["promotion_blocked", "Promotion blocked"],
                      ["publication_blocked", "Publication blocked"],
                      ["live_recommendation_blocked", "Recommendation blocked"],
                      ["overview_influence_blocked", "Overview influence blocked"],
                      ["broker_execution_blocked", "Broker path blocked"],
                    ] as const).map(([key, label]) => {
                      const val = candidateEligibility.isolation_checks?.[key];
                      return (
                        <span key={key} className={`inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium ${
                          val === true ? "bg-pos-soft text-pos-soft-ink" : "bg-caution-soft text-caution-soft-ink"
                        }`}>{val === true ? label : `${label.replace(" blocked", "")} check missing`}</span>
                      );
                    })}
                  </>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium bg-surface-3 text-ink-3">Loading isolation checks...</span>
                )}
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[9px] font-medium bg-surface-3 text-ink-3">Not eligible for promotion</span>
              </div>
              <div className="rounded-lg border border-caution bg-caution-soft p-2 text-[10px] text-caution-soft-ink">
                Production benchmark uses score-weighted fallback surrogate. No neural model is loaded. No production influence.
              </div>

              {candidateEligibility && (
                <div className={`rounded-lg border p-2 text-[10px] ${
                  candidateEligibility.eligible
                    ? "border-pos bg-pos-soft text-pos-soft-ink"
                    : "border-breach bg-breach-soft text-breach-soft-ink"
                }`}>
                  <span className="font-medium">{candidateEligibility.eligible ? "Benchmark eligible" : "Not benchmark eligible"}</span>
                  {!candidateEligibility.eligible && (
                    <ul className="mt-1 list-disc list-inside">{candidateEligibility.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
                  )}
                </div>
              )}

              {/* Run Candidate Benchmark */}
              {candidateEligibility?.eligible && (
                <div className="border-t border-line pt-3">
                  <h4 className="text-[12px] font-semibold text-ink mb-2">Run Offline Candidate Benchmark</h4>
                  <p className="text-[10px] text-ink-4 mb-2">This is a research-only offline benchmark. It does not run neural inference in production and cannot affect recommendations, overview, publication, or broker systems.</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-[11px] mb-2">
                    <div>
                      <label className="block text-ink-4 text-[10px] mb-0.5">Name</label>
                      <input type="text" value={candBenchName} onChange={e => setCandBenchName(e.target.value)}
                        className="w-full border border-line rounded px-2 py-1 text-[11px] bg-canvas focus:border-primary focus:outline-none" />
                    </div>
                    <div>
                      <label className="block text-ink-4 text-[10px] mb-0.5">Start date</label>
                      <input type="date" value={candBenchStart} onChange={e => setCandBenchStart(e.target.value)}
                        className="w-full border border-line rounded px-2 py-1 text-[11px] bg-canvas focus:border-primary focus:outline-none" />
                    </div>
                    <div>
                      <label className="block text-ink-4 text-[10px] mb-0.5">End date</label>
                      <input type="date" value={candBenchEnd} onChange={e => setCandBenchEnd(e.target.value)}
                        className="w-full border border-line rounded px-2 py-1 text-[11px] bg-canvas focus:border-primary focus:outline-none" />
                    </div>
                    <div className="flex items-end">
                      <label className="flex items-center gap-1.5 text-[11px] text-ink-2 cursor-pointer">
                        <input type="checkbox" checked={candBenchBaselines} onChange={e => setCandBenchBaselines(e.target.checked)} className="rounded" />
                        Include baselines
                      </label>
                    </div>
                  </div>
                  <label className="flex items-center gap-2 text-[10px] text-ink-3 mb-2 cursor-pointer">
                    <input type="checkbox" checked={candBenchAck} onChange={e => setCandBenchAck(e.target.checked)} className="rounded" />
                    I understand this is an offline/shadow research benchmark only. No neural inference is run. Results are not used by production decisions.
                  </label>
                  <button onClick={runCandidateBenchmark}
                    disabled={candBenchLoading || !candBenchAck || !candBenchName || !candBenchStart || !candBenchEnd || candBenchStart > candBenchEnd}
                    className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-primary text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity">
                    {candBenchLoading ? "Running offline benchmark..." : "Run offline benchmark"}
                  </button>
                  {candBenchError && <p className="mt-2 text-[10px] text-breach">{candBenchError}</p>}
                </div>
              )}

              {/* Benchmark Result */}
              {candBenchResult && (
                <div className="border-t border-line pt-3">
                  <h4 className="text-[12px] font-semibold text-ink mb-2">Benchmark Result</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-[10px] mb-2">
                    <div><span className="text-ink-4">Status:</span> <span className={candBenchResult.status === "completed" ? "text-pos font-medium" : "text-caution font-medium"}>{candBenchResult.status}</span></div>
                    <div><span className="text-ink-4">Inference:</span> <span className="text-ink">{candBenchResult.candidate_benchmark_context.inference_mode}</span></div>
                    <div><span className="text-ink-4">Neural inference:</span> <span className="text-pos font-medium">none (surrogate)</span></div>
                    <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-3">{candBenchResult.result_fingerprint?.slice(0, 12) || "\u2014"}</span></div>
                  </div>
                  <div className="text-[10px] text-ink-4 mb-1">Executed agents: <span className="text-ink-2">{candBenchResult.executed_agents.join(", ")}</span></div>
                  {candBenchResult.metrics_by_agent && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-[10px] border-collapse">
                        <thead><tr className="border-b border-line text-ink-4">
                          <th className="text-left py-1 pr-2">Agent</th>
                          <th className="text-right py-1 px-1">Return</th>
                          <th className="text-right py-1 px-1">Reward</th>
                          <th className="text-right py-1 px-1">Drawdown</th>
                          <th className="text-right py-1 px-1">Steps</th>
                        </tr></thead>
                        <tbody>{Object.entries(candBenchResult.metrics_by_agent).map(([agent, m]) => (
                          <tr key={agent} className="border-b border-line/50">
                            <td className="py-1 pr-2 font-mono text-ink-2">{agent.length > 24 ? agent.slice(0, 24) + "\u2026" : agent}</td>
                            <td className="text-right py-1 px-1">{(m.total_return ?? 0).toFixed(4)}</td>
                            <td className="text-right py-1 px-1">{(m.total_reward ?? 0).toFixed(4)}</td>
                            <td className="text-right py-1 px-1">{(m.max_drawdown ?? 0).toFixed(4)}</td>
                            <td className="text-right py-1 px-1">{m.step_count ?? 0}</td>
                          </tr>
                        ))}</tbody>
                      </table>
                    </div>
                  )}
                  {candBenchResult.benchmark_report_id && (
                    <button onClick={() => openBenchmarkById(candBenchResult.benchmark_report_id)}
                      className="mt-2 px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink hover:bg-surface-2 transition-opacity">
                      View in benchmark drilldown
                    </button>
                  )}
                  {candBenchResult.warnings.length > 0 && (
                    <div className="mt-2 rounded-lg border border-caution bg-caution-soft p-2 text-[9px] text-caution-soft-ink">
                      {candBenchResult.warnings.map((w, i) => <p key={i}>{w}</p>)}
                    </div>
                  )}
                </div>
              )}

              {/* Candidate Benchmark History */}
              <div className="border-t border-line pt-3">
                <h4 className="text-[12px] font-semibold text-ink mb-2">Candidate Benchmark History</h4>
                {candidateBenchHistory.length === 0 ? (
                  <p className="text-[10px] text-ink-4">No benchmark history for this imported candidate.</p>
                ) : (
                  <div className="space-y-1">
                    {candidateBenchHistory.slice(0, 8).map((h, i) => (
                      <div key={i} className="flex flex-wrap items-center justify-between gap-1 rounded-md border border-line px-2 py-1.5 text-[10px]">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-ink-3">{h.benchmark_report_id?.slice(0, 8) || "\u2014"}</span>
                          <span className="text-ink-4">{h.inference_mode}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${h.real_neural_inference ? "bg-breach-soft text-breach-soft-ink" : "bg-pos-soft text-pos-soft-ink"}`}>
                            {h.real_neural_inference ? "neural" : "surrogate"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-ink-4">
                          <span>{h.executed_agents?.length || 0} agents</span>
                          <span>{h.occurred_at?.slice(0, 19) || ""}</span>
                          {h.benchmark_report_id && (
                            <button onClick={() => openBenchmarkById(h.benchmark_report_id)}
                              className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-surface-3 text-ink hover:bg-surface-2">
                              details
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </GlassCard>

        {/* ── Run Offline Benchmark ── */}
        <GlassCard>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="sparkle" size={15} className="text-accent" />
            <h3 className="text-[13px] font-semibold text-ink">Run Offline Benchmark</h3>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Offline / Shadow only</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">No broker execution</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">Benchmark name</label>
              <input type="text" value={benchRunName} onChange={(e) => setBenchRunName(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">Start date</label>
              <input type="date" value={benchRunStart} onChange={(e) => setBenchRunStart(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">End date</label>
              <input type="date" value={benchRunEnd} onChange={(e) => setBenchRunEnd(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
          </div>
          <div className="mb-3">
            <label className="text-[10px] text-ink-4 block mb-1">Agents to compare</label>
            <div className="flex flex-wrap gap-2">
              {["heuristic_baseline", "random_valid", "score_weighted_baseline"].map((ak) => (
                <label key={ak} className="flex items-center gap-1.5 text-[11px] text-ink-2 cursor-pointer">
                  <input type="checkbox" checked={benchRunAgents[ak] ?? false}
                    onChange={(e) => setBenchRunAgents((prev) => ({ ...prev, [ak]: e.target.checked }))}
                    className="rounded" />
                  {ak.replace(/_/g, " ")}
                </label>
              ))}
            </div>
            {Object.values(benchRunAgents).filter(Boolean).length === 0 && (
              <p className="text-[10px] text-breach mt-1">At least one agent is required.</p>
            )}
            {Object.values(benchRunAgents).filter(Boolean).length > 0 && Object.values(benchRunAgents).filter(Boolean).length < 3 && (
              <p className="text-[10px] text-caution mt-1">Partial benchmark: not all required baseline agents selected.</p>
            )}
          </div>
          <div className="rounded-lg border border-line bg-surface-2 p-3 mb-3">
            <label className="flex items-start gap-2 text-[11px] text-ink-2 cursor-pointer">
              <input type="checkbox" checked={benchRunAcknowledged} onChange={(e) => setBenchRunAcknowledged(e.target.checked)} className="rounded mt-0.5" />
              <span>
                I understand this is an <strong className="text-ink">offline/shadow benchmark only</strong>.
                It cannot affect live recommendations, production decisions, broker systems, or publication workflow.
              </span>
            </label>
          </div>
          <div className="flex items-center gap-3">
            <button
              disabled={
                benchRunLoading || !benchRunAcknowledged || !benchRunName.trim() ||
                !benchRunStart || !benchRunEnd || benchRunStart > benchRunEnd ||
                Object.values(benchRunAgents).filter(Boolean).length === 0
              }
              onClick={async () => {
                setBenchRunLoading(true);
                setBenchRunError(null);
                setBenchRunSuccess(null);
                try {
                  const agents = Object.entries(benchRunAgents).filter(([, v]) => v).map(([k]) => k);
                  const res = await runRLBenchmark({
                    name: benchRunName.trim(),
                    start_date: benchRunStart,
                    end_date: benchRunEnd,
                    agent_keys: agents,
                  });
                  const report = res.data;
                  const REQUIRED = ["heuristic_baseline", "random_valid", "score_weighted_baseline"];
                  const selectedAllRequired = REQUIRED.every(a => agents.includes(a));
                  const executedAllRequired = REQUIRED.every(a => report.executed_agents?.includes(a));
                  const isFullPass =
                    selectedAllRequired && executedAllRequired &&
                    report.status === "completed" &&
                    report.is_complete_comparison === true &&
                    (report.skipped_agents?.length || 0) === 0;
                  const partialReason = !selectedAllRequired
                    ? "not all required baseline agents were selected"
                    : !executedAllRequired
                    ? "not all required baseline agents were executed"
                    : (report.skipped_agents?.length || 0) > 0
                    ? `${report.skipped_agents!.length} agent(s) skipped`
                    : report.status !== "completed"
                    ? `status: ${report.status}`
                    : "";
                  setBenchRunSuccess(
                    isFullPass
                      ? `Benchmark ${report.id.slice(0, 8)}... completed \u2014 ${report.executed_agents?.length || 0} agents compared`
                      : `partial|Offline benchmark created with partial scope \u2014 ${partialReason}. ${report.executed_agents?.length || 0} executed.`
                  );
                  const refreshed = await fetchRLBenchmarks().catch(() => null);
                  if (refreshed && refreshed.data) {
                    setBenchmarks(refreshed.data);
                    setSelectedBenchmark(report);
                    ctxSelectBenchmark(report);
                  }
                  const refreshAudit = await fetchRLBenchmarkAudit().catch(() => null);
                  if (refreshAudit && refreshAudit.data) setBenchAuditEvents(refreshAudit.data);
                } catch (err: unknown) {
                  setBenchRunError(err instanceof Error ? err.message : "Benchmark run failed");
                } finally {
                  setBenchRunLoading(false);
                }
              }}
              className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12px] font-medium flex items-center gap-1.5 hover:opacity-90 transition-opacity disabled:opacity-40"
            >
              {benchRunLoading ? (
                <><Icon name="clock" size={13} /> Running offline benchmark...</>
              ) : (
                <><Icon name="sparkle" size={13} /> Run offline benchmark</>
              )}
            </button>
            {benchRunStart && benchRunEnd && benchRunStart > benchRunEnd && (
              <span className="text-[10px] text-breach">Start date must be before end date.</span>
            )}
          </div>
          {benchRunSuccess && !benchRunSuccess.startsWith("partial|") && (
            <div className="mt-3 rounded-lg border border-pos bg-pos-soft p-3 text-[11px] text-pos-soft-ink">
              <Icon name="check" size={12} className="inline mr-1" />{benchRunSuccess}
            </div>
          )}
          {benchRunSuccess && benchRunSuccess.startsWith("partial|") && (
            <div className="mt-3 rounded-lg border border-caution bg-caution-soft p-3 text-[11px] text-caution-soft-ink">
              <Icon name="alert-triangle" size={12} className="inline mr-1" />{benchRunSuccess.slice(8)}
            </div>
          )}
          {benchRunError && (
            <div className="mt-3 rounded-lg border border-breach bg-breach-soft p-3 text-[11px] text-breach-soft-ink">
              <Icon name="alert-triangle" size={12} className="inline mr-1" />{benchRunError}
            </div>
          )}
        </GlassCard>

        {/* ── Benchmark History ── */}
        {effectiveBenchmarks.length === 0 && ops.rl && ops.rl.total_benchmarks === 0 && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Icon name="compare" size={15} className="text-ink-4" />
              <h3 className="text-[13px] font-semibold text-ink-3">Offline Benchmark</h3>
            </div>
            <p className="text-[12px] text-ink-3">No offline benchmarks have been run yet. Use the RL benchmark API to compare agents on historical data.</p>
            <p className="text-[10px] text-ink-4 mt-1">This is an offline/shadow forensic tool -- not a live recommendation system.</p>
          </GlassCard>
        )}

        {effectiveBenchmarks.length > 0 && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Icon name="history" size={15} className="text-accent" />
              <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark History</h3>
              <span className="text-[10px] text-ink-4 ml-auto">{effectiveBenchmarks.length} report{effectiveBenchmarks.length !== 1 ? "s" : ""}</span>
            </div>
            <div className="space-y-1">
              {effectiveBenchmarks.slice(0, 8).map((b) => (
                <div key={b.id} onClick={() => { setSelectedBenchmark(b); ctxSelectBenchmark(b); }}
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                    effectiveSelectedBenchmark?.id === b.id ? "bg-primary-soft border border-primary" : "hover:bg-surface-3"
                  }`}>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={b.status} />
                    <span className="text-[12px] text-ink-2">{b.name}</span>
                    <span className="text-[10px] text-ink-4 font-mono">{b.start_date} \u2014 {b.end_date}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-ink-3">{b.executed_agents?.length || 0} agents</span>
                    {b.is_complete_comparison ? (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-pos-soft text-pos-soft-ink">Complete</span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-caution-soft text-caution-soft-ink">Partial</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Selected Benchmark Drill-down */}
        {effectiveSelectedBenchmark && (
          <GlassCard>
            <div id="benchmark-drilldown" className="flex flex-wrap items-center gap-2 mb-4">
              <Icon name="compare" size={15} className="text-accent" />
              <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark -- Forensic Comparison</h3>
              <StatusBadge status={effectiveSelectedBenchmark.status} />
              {effectiveSelectedBenchmark.is_complete_comparison ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-pos-soft text-pos-soft-ink">Complete</span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-caution-soft text-caution-soft-ink">Partial</span>
              )}
              <span className="text-[10px] text-ink-4 ml-auto font-mono">{effectiveSelectedBenchmark.id.slice(0, 8)}...</span>
            </div>

            <div className="flex flex-wrap gap-1.5 mb-4">
              {[
                { key: "offline_only", label: "Offline only", safeWhen: true },
                { key: "shadow_only", label: "Shadow only", safeWhen: true },
                { key: "live_pipeline_influence", label: "No live pipeline influence", safeWhen: false },
                { key: "no_broker_execution", label: "No broker execution", safeWhen: true },
                { key: "no_publication_influence", label: "No publication influence", safeWhen: true },
                { key: "no_recommendation_pollution", label: "Not a live recommendation", safeWhen: true },
              ].map((f) => {
                const raw = (effectiveSelectedBenchmark.safety_flags as unknown as Record<string, boolean>)?.[f.key];
                const isSafe = raw === f.safeWhen;
                return (
                  <span key={f.key} className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium ${
                    isSafe ? "bg-surface-3 text-ink-3" : "bg-breach-soft text-breach-soft-ink"
                  }`}>{isSafe ? f.label : `WARNING: ${f.key}`}</span>
                );
              })}
            </div>

            <div className="flex items-center gap-4 text-[11px] text-ink-3 mb-4 flex-wrap">
              <span>Window: {effectiveSelectedBenchmark.start_date} \u2014 {effectiveSelectedBenchmark.end_date}</span>
              <span>Agents: {effectiveSelectedBenchmark.executed_agents?.length || 0} executed</span>
              {effectiveSelectedBenchmark.skipped_agents?.length > 0 && (
                <span className="text-caution">{effectiveSelectedBenchmark.skipped_agents.length} skipped</span>
              )}
              {effectiveSelectedBenchmark.environment_key && <span>Env: {effectiveSelectedBenchmark.environment_key}</span>}
              {effectiveSelectedBenchmark.created_at && <span>Created: {effectiveSelectedBenchmark.created_at.slice(0, 16).replace("T", " ")}</span>}
            </div>

            {effectiveSelectedBenchmark.skipped_agents?.length > 0 && (
              <div className="rounded-lg border border-caution bg-caution-soft p-3 mb-4 text-[12px] text-caution-soft-ink">
                <p className="font-medium mb-1">Skipped agents:</p>
                {effectiveSelectedBenchmark.skipped_agents.map((s, i) => (
                  <p key={i}>{s.agent_key}: {s.reason}</p>
                ))}
              </div>
            )}

            {/* Agent comparison table */}
            {effectiveSelectedBenchmark.metrics_by_agent && Object.keys(effectiveSelectedBenchmark.metrics_by_agent).length > 0 && (
              <div className="mb-4">
                <h4 className="text-[12px] font-semibold text-ink mb-2">Agent Comparison -- Offline Metrics</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr className="border-b border-line text-[10px] text-ink-4 uppercase tracking-wider">
                        <th className="text-left py-2 pr-3 font-medium">Agent</th>
                        <th className="text-right py-2 pr-3 font-medium">Return</th>
                        <th className="text-right py-2 pr-3 font-medium">Reward</th>
                        <th className="text-right py-2 pr-3 font-medium">Drawdown</th>
                        <th className="text-right py-2 pr-3 font-medium">Turnover</th>
                        <th className="text-right py-2 pr-3 font-medium">Steps</th>
                        <th className="text-right py-2 font-medium">Violations</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        const agents = Object.entries(effectiveSelectedBenchmark.metrics_by_agent);
                        const bestReturn = Math.max(...agents.map(([, m]) => m.total_return ?? -Infinity));
                        const bestReward = Math.max(...agents.map(([, m]) => m.total_reward ?? -Infinity));
                        const lowestDrawdown = Math.max(...agents.map(([, m]) => m.max_drawdown ?? -Infinity));
                        const lowestTurnover = Math.min(...agents.filter(([, m]) => m.total_turnover != null).map(([, m]) => m.total_turnover!));
                        return agents.map(([key, m]) => (
                          <tr key={key} className="border-b border-line/50 hover:bg-surface-3 transition-colors">
                            <td className="py-2 pr-3 font-medium text-ink">{key.replace(/_/g, " ")}</td>
                            <td className={`py-2 pr-3 text-right font-mono ${m.total_return === bestReturn ? "text-pos font-semibold" : "text-ink-2"}`}>
                              {m.total_return != null ? `${(m.total_return * 100).toFixed(2)}%` : "\u2014"}
                            </td>
                            <td className={`py-2 pr-3 text-right font-mono ${m.total_reward === bestReward ? "text-pos font-semibold" : "text-ink-2"}`}>
                              {m.total_reward?.toFixed(4) ?? "\u2014"}
                            </td>
                            <td className={`py-2 pr-3 text-right font-mono ${m.max_drawdown === lowestDrawdown ? "text-pos font-semibold" : "text-ink-2"}`}>
                              {m.max_drawdown != null ? `${(m.max_drawdown * 100).toFixed(2)}%` : "\u2014"}
                            </td>
                            <td className={`py-2 pr-3 text-right font-mono ${m.total_turnover === lowestTurnover ? "text-pos font-semibold" : "text-ink-2"}`}>
                              {m.total_turnover?.toFixed(2) ?? "\u2014"}
                            </td>
                            <td className="py-2 pr-3 text-right font-mono text-ink-3">{m.step_count ?? "\u2014"}</td>
                            <td className={`py-2 text-right font-mono ${(m.violation_count ?? 0) > 0 ? "text-caution" : "text-ink-3"}`}>
                              {m.violation_count ?? 0}
                            </td>
                          </tr>
                        ));
                      })()}
                    </tbody>
                  </table>
                </div>
                <p className="text-[10px] text-ink-4 mt-2">
                  Green highlight: best offline return, highest offline reward, lowest drawdown, lowest turnover in this benchmark. Not a live recommendation.
                </p>
              </div>
            )}

            {/* Reward breakdown */}
            {effectiveSelectedBenchmark.reward_breakdown_by_agent && Object.keys(effectiveSelectedBenchmark.reward_breakdown_by_agent).length > 0 && (
              <div className="mb-4">
                <h4 className="text-[12px] font-semibold text-ink mb-2">Reward Component Breakdown</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr className="border-b border-line text-[10px] text-ink-4 uppercase tracking-wider">
                        <th className="text-left py-2 pr-3 font-medium">Agent</th>
                        <th className="text-right py-2 pr-3 font-medium">Return Component</th>
                        <th className="text-right py-2 pr-3 font-medium">Drawdown Penalty</th>
                        <th className="text-right py-2 font-medium">Turnover Penalty</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(effectiveSelectedBenchmark.reward_breakdown_by_agent).map(([key, rb]) => (
                        <tr key={key} className="border-b border-line/50">
                          <td className="py-2 pr-3 text-ink-2">{key.replace(/_/g, " ")}</td>
                          <td className="py-2 pr-3 text-right font-mono text-ink-2">{rb.portfolio_return_component?.toFixed(4) ?? "\u2014"}</td>
                          <td className="py-2 pr-3 text-right font-mono text-caution">{rb.drawdown_penalty_component?.toFixed(4) ?? "\u2014"}</td>
                          <td className="py-2 text-right font-mono text-ink-3">{rb.turnover_penalty_component?.toFixed(6) ?? "\u2014"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Equity / Portfolio Value Curve */}
            {(() => {
              const forensicByAgent = effectiveSelectedBenchmark.forensic_summary_by_agent;
              const agentKeys = forensicByAgent ? Object.keys(forensicByAgent) : [];
              const hasPerAgent = agentKeys.length > 0;
              const displaySteps = hasPerAgent
                ? forensicByAgent![agentKeys[0]] || []
                : effectiveSelectedBenchmark.forensic_summary || [];
              if (displaySteps.length === 0) return null;
              return (
                <div className="mb-4">
                  <h4 className="text-[12px] font-semibold text-ink mb-1">Offline Forensic Portfolio Value Curve</h4>
                  <p className="text-[10px] text-ink-4 mb-2">
                    {hasPerAgent
                      ? `Per-agent portfolio value available for: ${agentKeys.map(k => k.replace(/_/g, " ")).join(", ")}`
                      : `Portfolio value curve based on: ${displaySteps[0]?.agent_key?.replace(/_/g, " ") || "first agent"}`
                    }. Offline forensic curve only -- no production influence.
                  </p>
                  <div className="space-y-3">
                    {(hasPerAgent ? agentKeys : ["_default"]).map((agentKey) => {
                      const steps = hasPerAgent ? (forensicByAgent![agentKey] || []) : displaySteps;
                      if (steps.length < 2) return null;
                      const values = steps.map(s => s.portfolio_value ?? 100);
                      const minV = Math.min(...values);
                      const maxV = Math.max(...values);
                      const range = maxV - minV || 1;
                      const w = 600;
                      const h = 40;
                      const points = values.map((v, i) =>
                        `${(i / (values.length - 1)) * w},${h - ((v - minV) / range) * (h - 4) - 2}`
                      ).join(" ");
                      const label = agentKey === "_default" ? (steps[0]?.agent_key || "agent") : agentKey;
                      const finalVal = values[values.length - 1];
                      return (
                        <div key={agentKey} className="flex items-center gap-3">
                          <span className="text-[11px] text-ink-2 w-32 shrink-0 truncate">{label.replace(/_/g, " ")}</span>
                          <svg viewBox={`0 0 ${w} ${h}`} className="flex-1 h-10" preserveAspectRatio="none">
                            <polyline points={points} fill="none" stroke="oklch(0.52 0.17 255)" strokeWidth="2" />
                            <line x1="0" y1={h - ((100 - minV) / range) * (h - 4) - 2} x2={w} y2={h - ((100 - minV) / range) * (h - 4) - 2}
                              stroke="oklch(0.92 0.008 240)" strokeDasharray="4 4" strokeWidth="1" />
                          </svg>
                          <span className={`text-[11px] font-mono w-14 text-right ${finalVal >= 100 ? "text-pos" : "text-breach"}`}>{finalVal.toFixed(1)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {/* Forensic step summary */}
            {(() => {
              const byAgent = effectiveSelectedBenchmark.forensic_summary_by_agent;
              const hasPerAgent = byAgent && Object.keys(byAgent).length > 0;
              const agentKeys = hasPerAgent ? Object.keys(byAgent!) : [];
              const activeAgent = hasPerAgent
                ? (selectedForensicAgent && agentKeys.includes(selectedForensicAgent) ? selectedForensicAgent : agentKeys[0])
                : null;
              const rows = hasPerAgent && activeAgent
                ? (byAgent![activeAgent] || [])
                : (effectiveSelectedBenchmark.forensic_summary || []);
              if (rows.length === 0) return null;
              return (
                <div className="mb-3">
                  <h4 className="text-[12px] font-semibold text-ink mb-2">Forensic Step Summary</h4>
                  {hasPerAgent ? (
                    <>
                      <div className="flex items-center gap-1 mb-2">
                        {agentKeys.map((ak) => (
                          <button key={ak} onClick={() => setSelectedForensicAgent(ak)}
                            className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                              ak === activeAgent ? "bg-primary text-primary-ink" : "text-ink-3 hover:bg-surface-3"
                            }`}>{ak.replace(/_/g, " ")}</button>
                        ))}
                      </div>
                      <p className="text-[10px] text-ink-4 mb-2">
                        Step-level forensic detail for: {activeAgent?.replace(/_/g, " ")} -- up to 50 rows per agent -- offline forensic only
                      </p>
                    </>
                  ) : (
                    <p className="text-[10px] text-ink-4 mb-2">
                      Step-level forensic rows currently available for first agent only: {rows[0]?.agent_key?.replace(/_/g, " ") || "unknown"}
                    </p>
                  )}
                  <div className="overflow-x-auto max-h-48 overflow-y-auto">
                    <table className="w-full text-[11px]">
                      <thead className="sticky top-0 bg-surface">
                        <tr className="border-b border-line text-[10px] text-ink-4 uppercase tracking-wider">
                          <th className="text-left py-1.5 pr-2 font-medium">Step</th>
                          <th className="text-left py-1.5 pr-2 font-medium">Date</th>
                          <th className="text-left py-1.5 pr-2 font-medium">Action</th>
                          <th className="text-right py-1.5 pr-2 font-medium">Reward</th>
                          <th className="text-right py-1.5 pr-2 font-medium">Value</th>
                          <th className="text-right py-1.5 pr-2 font-medium">Turnover</th>
                          <th className="text-right py-1.5 font-medium">Violations</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.slice(0, 50).map((s, i) => (
                          <tr key={i} className="border-b border-line/30">
                            <td className="py-1.5 pr-2 font-mono text-ink-3">{s.step_index}</td>
                            <td className="py-1.5 pr-2 font-mono text-ink-2">{s.as_of_date?.slice(5) || "\u2014"}</td>
                            <td className="py-1.5 pr-2 text-ink-2">{s.action_type || "\u2014"}</td>
                            <td className={`py-1.5 pr-2 text-right font-mono ${(s.reward ?? 0) >= 0 ? "text-ink-2" : "text-breach"}`}>{s.reward?.toFixed(4) ?? "\u2014"}</td>
                            <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{s.portfolio_value?.toFixed(1) ?? "\u2014"}</td>
                            <td className="py-1.5 pr-2 text-right font-mono text-ink-3">{s.turnover?.toFixed(2) ?? "\u2014"}</td>
                            <td className={`py-1.5 text-right font-mono ${(s.violations?.length ?? 0) > 0 ? "text-caution" : "text-ink-4"}`}>
                              {s.violations?.length ?? 0}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })()}

            {effectiveSelectedBenchmark.warnings && effectiveSelectedBenchmark.warnings.length > 0 && (
              <div className="rounded-lg border border-caution bg-caution-soft p-3 text-[11px] text-caution-soft-ink">
                {effectiveSelectedBenchmark.warnings.map((w, i) => (
                  <p key={i} className="flex items-center gap-1.5">
                    <Icon name="alert-triangle" size={10} />{w}
                  </p>
                ))}
              </div>
            )}
          </GlassCard>
        )}

        {/* Benchmark Governance & Audit Trail */}
        {effectiveBenchAuditEvents.length > 0 && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Icon name="history" size={15} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Benchmark Governance & Audit Trail</h3>
              <span className="text-[10px] text-ink-4 ml-auto">{effectiveBenchAuditEvents.length} event{effectiveBenchAuditEvents.length !== 1 ? "s" : ""} -- offline forensic audit</span>
            </div>
            <div className="overflow-x-auto max-h-56 overflow-y-auto">
              <table className="w-full text-[11px]">
                <thead className="sticky top-0 bg-surface">
                  <tr className="border-b border-line text-[10px] text-ink-4 uppercase tracking-wider">
                    <th className="text-left py-1.5 pr-2 font-medium">Time</th>
                    <th className="text-left py-1.5 pr-2 font-medium">Event</th>
                    <th className="text-left py-1.5 pr-2 font-medium">Report</th>
                    <th className="text-left py-1.5 pr-2 font-medium">Status</th>
                    <th className="text-right py-1.5 pr-2 font-medium">Agents</th>
                    <th className="text-left py-1.5 pr-2 font-medium">Fingerprint</th>
                    <th className="text-left py-1.5 font-medium">Invariants</th>
                  </tr>
                </thead>
                <tbody>
                  {effectiveBenchAuditEvents.slice(0, 20).map((ev) => {
                    const invPassed = ev.invariant_check_results?.all_passed;
                    return (
                      <tr key={ev.id} className="border-b border-line/30">
                        <td className="py-1.5 pr-2 font-mono text-ink-3">{ev.created_at?.slice(11, 19) || "\u2014"}</td>
                        <td className="py-1.5 pr-2 text-ink-2">{ev.event_type?.replace(/_/g, " ") || "\u2014"}</td>
                        <td className="py-1.5 pr-2 font-mono text-ink-3">{ev.benchmark_report_id?.slice(0, 6) || "\u2014"}</td>
                        <td className="py-1.5 pr-2">{ev.status && <StatusBadge status={ev.status} />}</td>
                        <td className="py-1.5 pr-2 text-right font-mono text-ink-3">{ev.executed_agents?.length || "\u2014"}/{ev.requested_agents?.length || "\u2014"}</td>
                        <td className="py-1.5 pr-2 font-mono text-ink-4 text-[9px]">{ev.result_fingerprint?.slice(0, 12) || "\u2014"}</td>
                        <td className="py-1.5">
                          {invPassed === true && <span className="text-[9px] font-medium text-pos">passed</span>}
                          {invPassed === false && <span className="text-[9px] font-medium text-breach">failed</span>}
                          {invPassed == null && <span className="text-[9px] text-ink-4">\u2014</span>}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-[10px] text-ink-4 mt-2">Offline benchmark forensic audit trail -- not used by production decisions.</p>
          </GlassCard>
        )}

        {/* Audit Trail -- Selected Benchmark */}
        {effectiveSelectedBenchmark && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Icon name="history" size={14} className="text-ink-3" />
              <h4 className="text-[12px] font-semibold text-ink">Audit Trail -- Selected Benchmark</h4>
              <span className="text-[10px] text-ink-4 font-mono ml-auto">{effectiveSelectedBenchmark.id.slice(0, 8)}...</span>
            </div>
            {effectiveSelectedBenchAudit.length > 0 ? (
              <div className="overflow-x-auto max-h-36 overflow-y-auto mb-3">
                <table className="w-full text-[11px]">
                  <thead className="sticky top-0 bg-surface">
                    <tr className="border-b border-line text-[10px] text-ink-4 uppercase tracking-wider">
                      <th className="text-left py-1.5 pr-2 font-medium">Time</th>
                      <th className="text-left py-1.5 pr-2 font-medium">Event</th>
                      <th className="text-left py-1.5 pr-2 font-medium">Status</th>
                      <th className="text-right py-1.5 pr-2 font-medium">Agents</th>
                      <th className="text-left py-1.5 pr-2 font-medium">Fingerprint</th>
                      <th className="text-left py-1.5 font-medium">Invariants</th>
                    </tr>
                  </thead>
                  <tbody>
                    {effectiveSelectedBenchAudit.map((ev) => (
                      <tr key={ev.id} className="border-b border-line/30">
                        <td className="py-1.5 pr-2 font-mono text-ink-3">{ev.created_at?.slice(11, 19) || "\u2014"}</td>
                        <td className="py-1.5 pr-2 text-ink-2">{ev.event_type?.replace(/_/g, " ") || "\u2014"}</td>
                        <td className="py-1.5 pr-2">{ev.status ? <StatusBadge status={ev.status} /> : "\u2014"}</td>
                        <td className="py-1.5 pr-2 text-right font-mono text-ink-3">{ev.executed_agents?.length || "\u2014"}/{ev.requested_agents?.length || "\u2014"}</td>
                        <td className="py-1.5 pr-2 font-mono text-ink-4 text-[9px]">{ev.result_fingerprint?.slice(0, 12) || "\u2014"}</td>
                        <td className="py-1.5">
                          {ev.invariant_check_results?.all_passed === true && <span className="text-[9px] font-medium text-pos">passed</span>}
                          {ev.invariant_check_results?.all_passed === false && <span className="text-[9px] font-medium text-breach">failed</span>}
                          {ev.invariant_check_results == null && <span className="text-[9px] text-ink-4">\u2014</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-[11px] text-ink-3 mb-3">No audit events recorded for this benchmark. Audit trail is available for benchmark runs created after Phase 7G.</p>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] pt-3 border-t border-line">
              <div>
                <p className="text-[10px] text-ink-4 mb-0.5">Result fingerprint</p>
                {effectiveSelectedBenchmark.result_fingerprint ? (
                  <p className="font-mono text-ink-3 text-[10px] break-all">{effectiveSelectedBenchmark.result_fingerprint}</p>
                ) : (
                  <p className="text-ink-4 text-[10px]">No result fingerprint -- this benchmark likely predates Phase 7G governance.</p>
                )}
              </div>
              <div>
                <p className="text-[10px] text-ink-4 mb-0.5">Invariant checks</p>
                {effectiveSelectedBenchmark.invariant_check_results ? (
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(effectiveSelectedBenchmark.invariant_check_results).filter(([k]) => k !== "all_passed").map(([k, v]) => (
                      <span key={k} className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos-soft text-pos-soft-ink" : "bg-breach-soft text-breach-soft-ink"}`}>
                        {k.replace(/_/g, " ")}: {v ? "pass" : "FAIL"}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-ink-4 text-[10px]">No invariant data -- this benchmark likely predates Phase 7G governance.</p>
                )}
              </div>
            </div>
          </GlassCard>
        )}

        {/* Benchmark Trend Table */}
        {effectiveBenchmarks.length > 1 && (
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Icon name="trend-up" size={15} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark Trend</h3>
              <span className="text-[10px] text-ink-4 ml-auto">Across {effectiveBenchmarks.length} reports -- not live performance</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="border-b border-line text-[10px] text-ink-4 uppercase tracking-wider">
                    <th className="text-left py-1.5 pr-2 font-medium">Benchmark</th>
                    <th className="text-left py-1.5 pr-2 font-medium">Window</th>
                    <th className="text-left py-1.5 pr-2 font-medium">Agent</th>
                    <th className="text-right py-1.5 pr-2 font-medium">Return</th>
                    <th className="text-right py-1.5 pr-2 font-medium">Reward</th>
                    <th className="text-right py-1.5 pr-2 font-medium">Drawdown</th>
                    <th className="text-right py-1.5 font-medium">Turnover</th>
                  </tr>
                </thead>
                <tbody>
                  {effectiveBenchmarks.slice(0, 5).flatMap((b) =>
                    Object.entries(b.metrics_by_agent || {}).map(([agent, m]) => (
                      <tr key={`${b.id}-${agent}`} className="border-b border-line/30">
                        <td className="py-1.5 pr-2 text-ink-3 font-mono">{b.id.slice(0, 6)}</td>
                        <td className="py-1.5 pr-2 text-ink-3">{b.start_date?.slice(5)} \u2014 {b.end_date?.slice(5)}</td>
                        <td className="py-1.5 pr-2 text-ink-2">{agent.replace(/_/g, " ")}</td>
                        <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{m.total_return != null ? `${(m.total_return * 100).toFixed(2)}%` : "\u2014"}</td>
                        <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{m.total_reward?.toFixed(4) ?? "\u2014"}</td>
                        <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{m.max_drawdown != null ? `${(m.max_drawdown * 100).toFixed(2)}%` : "\u2014"}</td>
                        <td className="py-1.5 text-right font-mono text-ink-3">{m.total_turnover?.toFixed(2) ?? "\u2014"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        )}

        {/* ── Publication Queue ── */}
        <GlassCard>
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Icon name="decision" size={15} className="text-primary" />
            <h3 className="text-[13px] font-semibold text-ink">Publication Queue</h3>
            <div className="flex items-center gap-1 ml-4">
              {QUEUE_FILTERS.map((f) => (
                <button key={f.key} onClick={() => handleQueueFilter(f.key)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                    queueFilter === f.key ? "bg-primary text-primary-ink" : "text-ink-3 hover:bg-surface-3"
                  }`}>
                  {f.label}
                </button>
              ))}
            </div>
            <span className="text-[11px] text-ink-4 ml-auto">{filteredQueue.length} pending</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="border-b border-line text-[11px] text-ink-4 uppercase tracking-wider">
                  <th className="text-left py-2 pr-3 font-medium">Rec</th>
                  <th className="text-left py-2 pr-3 font-medium">Stance</th>
                  <th className="text-right py-2 pr-3 font-medium">Conf</th>
                  <th className="text-right py-2 pr-3 font-medium">Weight</th>
                  <th className="text-left py-2 pr-3 font-medium">Submitter</th>
                  <th className="text-left py-2 pr-3 font-medium">Flags</th>
                  <th className="text-left py-2 pr-3 font-medium">Priority</th>
                  <th className="text-right py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredQueue.map((q) => (
                  <tr key={q.id || q.recommendation_id} className="border-b border-line/50 hover:bg-surface-3 transition-colors">
                    <td className="py-2 pr-3">
                      <span className="font-mono font-semibold text-ink">{q.ticker}</span>
                      <span className="text-ink-4 text-[10px] ml-1">{q.version} {q.submitted_ago}</span>
                    </td>
                    <td className="py-2 pr-3">
                      <span className={`inline-block px-2 py-0.5 rounded-md text-[11px] font-medium ${STANCE_STYLE[q.stance] || ""}`}>{q.stance}</span>
                    </td>
                    <td className="py-2 pr-3 text-right font-mono">{q.confidence.toFixed(2)}</td>
                    <td className="py-2 pr-3 text-right font-mono">{q.weight}</td>
                    <td className="py-2 pr-3 text-ink-2">{q.submitter}</td>
                    <td className="py-2 pr-3">
                      {q.flags.map((f, i) => (
                        <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-caution-soft text-caution-soft-ink text-[10px] mr-1">
                          <Icon name="alert-triangle" size={9} />{f}
                        </span>
                      ))}
                    </td>
                    <td className={`py-2 pr-3 text-[11px] font-medium ${PRIORITY_STYLE[q.priority] || ""}`}>{q.priority}</td>
                    <td className="py-2 text-right">
                      {q.id && (
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => handleQueueAction(q.id!, "approve")} disabled={actionLoading === q.id}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-pos-soft text-pos-soft-ink hover:opacity-80 transition-opacity disabled:opacity-40">
                            Approve
                          </button>
                          <button onClick={() => handleQueueAction(q.id!, "defer")} disabled={actionLoading === q.id}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-caution-soft text-caution-soft-ink hover:opacity-80 transition-opacity disabled:opacity-40">
                            Defer
                          </button>
                          <button onClick={() => handleQueueAction(q.id!, "challenge")} disabled={actionLoading === q.id}
                            className="px-2 py-0.5 rounded text-[10px] font-medium bg-breach-soft text-breach-soft-ink hover:opacity-80 transition-opacity disabled:opacity-40">
                            Challenge
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-gap">
          {/* ── Data Feeds ── */}
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Icon name="database" size={15} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Data Feeds</h3>
            </div>
            <div className="space-y-2">
              {ops.feeds.map((f) => (
                <div key={f.name} className="flex items-center gap-3 text-[12.5px]">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${FEED_STATUS[f.status] || "bg-ink-4"}`} />
                  <span className="text-ink-2 flex-1 truncate">{f.name}</span>
                  <span className="text-ink-4 font-mono text-[11px] w-12 text-right">{f.lag}</span>
                  <span className="text-ink-4 font-mono text-[11px] w-12 text-right">{f.coverage}</span>
                  <div className="w-12 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${f.slo >= 0.95 ? "bg-pos" : f.slo >= 0.8 ? "bg-caution" : "bg-breach"}`} style={{ width: `${f.slo * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* ── Engine Health ── */}
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Icon name="compare" size={15} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Engine Health</h3>
            </div>
            <div className="space-y-2">
              {ops.engines.map((e) => (
                <div key={e.name} className="flex items-center gap-3 text-[12.5px]">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${e.status === "ok" ? "bg-pos" : e.status === "warn" ? "bg-caution" : "bg-breach"}`} />
                  <span className="text-ink-2 flex-1">{e.name}</span>
                  <span className="text-ink-4 font-mono text-[11px]">{e.latency}</span>
                  <span className={`font-mono text-[11px] ${e.drift > 0.05 ? "text-caution" : e.drift < -0.05 ? "text-breach" : "text-ink-3"}`}>
                    drift {e.drift > 0 ? "+" : ""}{e.drift.toFixed(2)}
                  </span>
                  <span className="text-ink-4 text-[11px]">{e.last_run}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* ── Policy / Integrations / Universe strip ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gap">
          {ops.policy && (
            <GlassCard>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <Icon name="risk" size={14} className="text-ink-3" />
                <h3 className="text-[13px] font-semibold text-ink">Policy Rules</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-center">
                <div>
                  <p className="text-[18px] font-display font-semibold text-ink">{ops.policy.active_rules}</p>
                  <p className="text-[10px] text-ink-4">active rules</p>
                </div>
                <div>
                  <p className="text-[18px] font-display font-semibold text-ink">{ops.policy.enforced_rules}</p>
                  <p className="text-[10px] text-ink-4">enforced</p>
                </div>
                <div>
                  <p className={`text-[18px] font-display font-semibold ${ops.policy.active_breaches > 0 ? "text-breach" : "text-pos"}`}>{ops.policy.active_breaches}</p>
                  <p className="text-[10px] text-ink-4">active breaches</p>
                </div>
                <div>
                  <p className="text-[18px] font-display font-semibold text-ink-3">{ops.policy.total_rules - ops.policy.enforced_rules}</p>
                  <p className="text-[10px] text-ink-4">display-only</p>
                </div>
              </div>
            </GlassCard>
          )}

          {ops.integrations_summary && (
            <GlassCard>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <Icon name="database" size={14} className="text-ink-3" />
                <h3 className="text-[13px] font-semibold text-ink">Integrations</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-center">
                <div>
                  <p className={`text-[18px] font-display font-semibold ${ops.integrations_summary.healthy > 0 ? "text-pos" : "text-ink-3"}`}>{ops.integrations_summary.healthy}</p>
                  <p className="text-[10px] text-ink-4">healthy</p>
                </div>
                <div>
                  <p className={`text-[18px] font-display font-semibold ${ops.integrations_summary.degraded > 0 ? "text-caution" : "text-ink-3"}`}>{ops.integrations_summary.degraded}</p>
                  <p className="text-[10px] text-ink-4">degraded</p>
                </div>
                <div>
                  <p className="text-[18px] font-display font-semibold text-ink">{ops.integrations_summary.real_providers}</p>
                  <p className="text-[10px] text-ink-4">real providers</p>
                </div>
                <div>
                  <p className="text-[18px] font-display font-semibold text-caution">{ops.integrations_summary.placeholder}</p>
                  <p className="text-[10px] text-ink-4">placeholder / demo</p>
                </div>
              </div>
            </GlassCard>
          )}

          {ops.universe && (
            <GlassCard>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <Icon name="universe" size={14} className="text-ink-3" />
                <h3 className="text-[13px] font-semibold text-ink">Universe</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-center">
                <div>
                  <p className="text-[18px] font-display font-semibold text-ink">{ops.universe.total_assets}</p>
                  <p className="text-[10px] text-ink-4">assets</p>
                </div>
                <div>
                  <p className="text-[18px] font-display font-semibold text-ink">{ops.universe.total_universes}</p>
                  <p className="text-[10px] text-ink-4">universes</p>
                </div>
              </div>
              {ops.universe.default_universe_name && (
                <div className="mt-2 pt-2 border-t border-line text-center">
                  <p className="text-[11px] text-ink-3">{ops.universe.default_universe_name}</p>
                  <p className={`text-[11px] font-medium ${ops.universe.default_readiness === "ready" ? "text-pos" : "text-caution"}`}>
                    {ops.universe.default_readiness || "unknown"}
                  </p>
                </div>
              )}
            </GlassCard>
          )}
        </div>

        {/* ── Breach Watch ── */}
        <GlassCard>
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Icon name="risk" size={15} className="text-breach" />
            <h3 className="text-[13px] font-semibold text-ink">Breach Watch</h3>
            <span className="text-[11px] text-ink-4 ml-auto">{ops.breaches.length} active</span>
          </div>
          <div className="space-y-3">
            {ops.breaches.map((b, i) => (
              <div key={i} className="flex items-center gap-3 text-[12.5px]">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                  b.severity === "breach" ? "bg-breach-soft text-breach-soft-ink" :
                  b.severity === "high" ? "bg-caution-soft text-caution-soft-ink" :
                  "bg-surface-3 text-ink-3"
                }`}>
                  <Icon name="alert-triangle" size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-ink font-medium">{b.label}</p>
                  <p className="text-[11px] text-ink-3">{b.related}</p>
                </div>
                <div className="text-right shrink-0">
                  <div className="w-16 h-2 bg-surface-3 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${b.utilization > 1 ? "bg-breach" : b.utilization > 0.9 ? "bg-caution" : "bg-pos"}`}
                         style={{ width: `${Math.min(b.utilization * 100, 100)}%` }} />
                  </div>
                  <span className={`text-[10px] font-mono ${b.utilization > 1 ? "text-breach" : "text-ink-4"}`}>{(b.utilization * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-gap">
          {/* ── Incidents ── */}
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Icon name="alert-triangle" size={15} className="text-caution" />
              <h3 className="text-[13px] font-semibold text-ink">Incidents</h3>
            </div>
            <div className="space-y-3">
              {ops.incidents.map((inc) => (
                <div key={inc.id} className="border border-line/50 rounded-lg p-3 cursor-pointer hover:border-primary/30 transition-colors" onClick={() => setDrawerIncident(inc)}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-[11px] text-ink-4">{inc.id}</span>
                    <span className={`text-[11px] ${SEVERITY_STYLE[inc.severity] || ""}`}>{inc.severity}</span>
                    <StatusBadge status={inc.status === "investigating" ? "provisional" : inc.status === "monitoring" ? "staged" : inc.status === "open" ? "provisional" : "published"} />
                  </div>
                  <p className="text-[12.5px] text-ink font-medium">{inc.title}</p>
                  <p className="text-[11px] text-ink-3 mt-1">{inc.note}</p>
                  <div className="flex items-center gap-3 mt-2 text-[11px] text-ink-4">
                    <span>Owner: {inc.owner}</span>
                    <span>Started: {inc.started}</span>
                    {inc.affected_recs > 0 && <span className="text-caution">{inc.affected_recs} recs affected</span>}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* ── Audit Trail ── */}
          <GlassCard>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <Icon name="history" size={15} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Audit Trail</h3>
              <div className="flex items-center gap-1 ml-4">
                {AUDIT_SCOPES.map((s) => (
                  <button key={s.key} onClick={() => handleAuditScope(s.key)}
                    className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                      auditScope === s.key ? "bg-primary text-primary-ink" : "text-ink-3 hover:bg-surface-3"
                    }`}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              {filteredAudit.map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-[12px] py-1 border-b border-line/30">
                  <span className="text-ink-4 font-mono w-8 shrink-0">{a.when}</span>
                  <span className="text-ink font-medium">{a.actor}</span>
                  <span className="text-ink-3">{a.action}</span>
                  <span className="text-ink-2 flex-1 truncate">{a.target}</span>
                  <span className={`w-1.5 h-1.5 rounded-full ${a.ok ? "bg-pos" : "bg-breach"}`} />
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </AnimatePresence>
  );
}
