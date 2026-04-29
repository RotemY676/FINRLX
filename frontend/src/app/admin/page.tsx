"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchOps, fetchOpsQueue, fetchOpsAudit,
  approveQueueItem, deferQueueItem, challengeQueueItem,
  fetchMLOpsSummary, fetchRLBenchmarks, fetchRLBenchmark, runRLBenchmark,
  fetchRLBenchmarkAudit, fetchRLBenchmarkAuditForReport,
  fetchFinRLXStatus, fetchFinRLXDependencies,
  fetchFinRLXCandidates, fetchFinRLXBenchmarkEligibility,
  runFinRLXCandidateBenchmark, fetchFinRLXCandidateBenchmarks,
  validateFinRLXResearchArtifact, importFinRLXResearchArtifact,
  createFinrlxDatasetExport, listFinrlxDatasetExports, getFinrlxDatasetExport,
  markFinrlxDatasetExportStale, verifyFinrlxDatasetExport, rebuildFinrlxDatasetExportRegistry,
  createFinrlxResearchExperiment, listFinrlxResearchExperiments, getFinrlxResearchExperiment,
  updateFinrlxResearchExperimentState, importFinrlxResearchExperimentResults,
  verifyFinrlxResearchExperiment, rebuildFinrlxResearchExperimentRegistry,
  createFinrlxExperimentComparison, listFinrlxExperimentComparisons, getFinrlxExperimentComparison,
  archiveFinrlxExperimentComparison, verifyFinrlxExperimentComparison,
  createFinrlxResearchReadiness, listFinrlxResearchReadiness, getFinrlxResearchReadiness,
  updateFinrlxResearchReadinessState, archiveFinrlxResearchReadiness, verifyFinrlxResearchReadiness,
  OpsData, OpsQueueItem, OpsAuditEntry, OpsIncident, MLOpsSummary,
  FinRLXDependencyStatus, FinRLXCandidate, FinRLXBenchmarkEligibility,
  FinRLXCandidateBenchmarkResponse, FinRLXCandidateBenchmarkHistoryItem,
  FinRLXArtifactValidationResult,
  DatasetExportResponse, DatasetExportRegistryEntry, DatasetExportVerifyResult,
  ResearchExperiment, ExperimentVerifyResult, ExperimentLifecycleState,
  ExperimentComparison, ComparisonVerifyResult,
  ReadinessReview, ReadinessVerifyResult, ReadinessState, ReadinessFinding,
  RLBenchmarkReport, RLBenchmarkAuditEvent, FinRLXAdapterStatus,
} from "@/services/api";
import { Icon } from "@/components/icons/Icon";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";
import { IncidentDrawer } from "@/components/ops/IncidentDrawer";

const STANCE_STYLE: Record<string, string> = {
  LONG: "text-pos-soft-ink bg-pos-soft", SHORT: "text-breach-soft-ink bg-breach-soft",
  TRIM: "text-caution-soft-ink bg-caution-soft", HOLD: "text-ink-3 bg-surface-3",
};
const PRIORITY_STYLE: Record<string, string> = {
  high: "text-breach", mid: "text-caution", low: "text-ink-3",
};
const FEED_STATUS: Record<string, string> = {
  ok: "bg-pos", degraded: "bg-caution", stale: "bg-breach",
};
const SEVERITY_STYLE: Record<string, string> = {
  "sev-1": "text-breach font-semibold", "sev-2": "text-caution font-semibold",
  "sev-3": "text-ink-2", "sev-4": "text-ink-3",
};
const KPI_TONE: Record<string, string> = {
  pos: "text-pos", caution: "text-caution", breach: "text-breach", neutral: "text-ink",
};

const QUEUE_FILTERS = [
  { key: "all", label: "All" },
  { key: "high", label: "High priority" },
];

const AUDIT_SCOPES = [
  { key: "all", label: "All" },
  { key: "recommendation", label: "Queue" },
  { key: "breach", label: "Policy" },
  { key: "engine", label: "Engine" },
  { key: "incident", label: "Ops" },
];

export default function AdminPage() {
  const [ops, setOps] = useState<OpsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Queue filter state
  const [queueFilter, setQueueFilter] = useState("all");
  const [filteredQueue, setFilteredQueue] = useState<OpsQueueItem[]>([]);

  // Audit scope state
  const [auditScope, setAuditScope] = useState("all");
  const [filteredAudit, setFilteredAudit] = useState<OpsAuditEntry[]>([]);

  // Action loading
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Incident drawer
  const [drawerIncident, setDrawerIncident] = useState<OpsIncident | null>(null);

  // ML Ops summary
  const [mlSummary, setMlSummary] = useState<MLOpsSummary | null>(null);

  // RL Benchmarks
  const [benchmarks, setBenchmarks] = useState<RLBenchmarkReport[]>([]);
  const [selectedBenchmark, setSelectedBenchmark] = useState<RLBenchmarkReport | null>(null);
  const [selectedForensicAgent, setSelectedForensicAgent] = useState<string | null>(null);

  // RL Benchmark run workflow
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
  const [benchAuditEvents, setBenchAuditEvents] = useState<RLBenchmarkAuditEvent[]>([]);
  const [selectedBenchAudit, setSelectedBenchAudit] = useState<RLBenchmarkAuditEvent[]>([]);
  const [finrlxStatus, setFinrlxStatus] = useState<FinRLXAdapterStatus | null>(null);
  const [finrlxDeps, setFinrlxDeps] = useState<FinRLXDependencyStatus | null>(null);

  // Imported candidate benchmark workflow
  const [importedCandidates, setImportedCandidates] = useState<FinRLXCandidate[]>([]);
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

  // Artifact import workflow
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

  // Dataset export workflow (Phase 8I)
  const [dsExportName, setDsExportName] = useState("Local Research Dataset Export");
  const [dsExportStart, setDsExportStart] = useState("2026-03-15");
  const [dsExportEnd, setDsExportEnd] = useState("2026-04-15");
  const [dsExportCandidateId, setDsExportCandidateId] = useState("");
  const [dsExportBenchmarkId, setDsExportBenchmarkId] = useState("");
  const [dsExportFormat, setDsExportFormat] = useState<"jsonl" | "json">("jsonl");
  const [dsExportFeatures, setDsExportFeatures] = useState(true);
  const [dsExportTargets, setDsExportTargets] = useState(true);
  const [dsExportWarnings, setDsExportWarnings] = useState(true);
  const [dsExportAck, setDsExportAck] = useState(false);
  const [dsExportLoading, setDsExportLoading] = useState(false);
  const [dsExportError, setDsExportError] = useState<string | null>(null);
  const [dsExportResult, setDsExportResult] = useState<DatasetExportResponse | null>(null);
  const [dsExportHistory, setDsExportHistory] = useState<DatasetExportRegistryEntry[]>([]);
  const [dsSelectedExport, setDsSelectedExport] = useState<DatasetExportResponse | null>(null);
  const [dsVerifyResult, setDsVerifyResult] = useState<DatasetExportVerifyResult | null>(null);
  const [dsStaleAck, setDsStaleAck] = useState(false);
  const [dsStaleReason, setDsStaleReason] = useState("");
  const [dsRebuildAck, setDsRebuildAck] = useState(false);
  const [dsGovLoading, setDsGovLoading] = useState<string | null>(null);
  const [dsGovError, setDsGovError] = useState<string | null>(null);
  const [dsGovSuccess, setDsGovSuccess] = useState<string | null>(null);

  // Research experiment tracking (Phase 8J.1)
  const [expName, setExpName] = useState("Offline research experiment");
  const [expLinkedExportId, setExpLinkedExportId] = useState("");
  const [expHypothesis, setExpHypothesis] = useState("");
  const [expMethodNotes, setExpMethodNotes] = useState("");
  const [expParams, setExpParams] = useState("{}");
  const [expMetrics, setExpMetrics] = useState("");
  const [expAck, setExpAck] = useState(false);
  const [expCreateLoading, setExpCreateLoading] = useState(false);
  const [expCreateError, setExpCreateError] = useState<string | null>(null);
  const [expCreateSuccess, setExpCreateSuccess] = useState<string | null>(null);
  const [expList, setExpList] = useState<ResearchExperiment[]>([]);
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

  // Comparison workbench (Phase 8K.1)
  const [cmpName, setCmpName] = useState("Offline experiment comparison");
  const [cmpExpIds, setCmpExpIds] = useState("");
  const [cmpPriority, setCmpPriority] = useState("");
  const [cmpNotes, setCmpNotes] = useState("");
  const [cmpAck, setCmpAck] = useState(false);
  const [cmpCreateLoading, setCmpCreateLoading] = useState(false);
  const [cmpCreateError, setCmpCreateError] = useState<string | null>(null);
  const [cmpCreateSuccess, setCmpCreateSuccess] = useState<string | null>(null);
  const [cmpList, setCmpList] = useState<ExperimentComparison[]>([]);
  const [cmpSelected, setCmpSelected] = useState<ExperimentComparison | null>(null);
  const [cmpVerifyResult, setCmpVerifyResult] = useState<ComparisonVerifyResult | null>(null);
  const [cmpArchiveAck, setCmpArchiveAck] = useState(false);
  const [cmpArchiveReason, setCmpArchiveReason] = useState("");
  const [cmpLoading, setCmpLoading] = useState<string | null>(null);
  const [cmpError, setCmpError] = useState<string | null>(null);
  const [cmpSuccess, setCmpSuccess] = useState<string | null>(null);

  // Readiness review (Phase 8L.1)
  const [rdName, setRdName] = useState("Research readiness review");
  const [rdCmpId, setRdCmpId] = useState("");
  const [rdNotes, setRdNotes] = useState("");
  const [rdAck, setRdAck] = useState(false);
  const [rdCreateLoading, setRdCreateLoading] = useState(false);
  const [rdCreateError, setRdCreateError] = useState<string | null>(null);
  const [rdCreateSuccess, setRdCreateSuccess] = useState<string | null>(null);
  const [rdList, setRdList] = useState<ReadinessReview[]>([]);
  const [rdSelected, setRdSelected] = useState<ReadinessReview | null>(null);
  const [rdVerifyResult, setRdVerifyResult] = useState<ReadinessVerifyResult | null>(null);
  const [rdStateValue, setRdStateValue] = useState<ReadinessState>("draft");
  const [rdStateAck, setRdStateAck] = useState(false);
  const [rdStateReason, setRdStateReason] = useState("");
  const [rdArchiveAck, setRdArchiveAck] = useState(false);
  const [rdLoading, setRdLoading] = useState<string | null>(null);
  const [rdError, setRdError] = useState<string | null>(null);
  const [rdSuccess, setRdSuccess] = useState<string | null>(null);

  // Admin workflow tab (Phase 8M.1)
  const [adminTab, setAdminTab] = useState<"research-data" | "experiments" | "comparisons" | "readiness" | "safety">("research-data");

  // Guided Research Workflow Wizard (Phase 8M.2)
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [wzExportId, setWzExportId] = useState("");
  const [wzExpIds, setWzExpIds] = useState<string[]>([]);
  const [wzCmpId, setWzCmpId] = useState("");
  const [wzRdId, setWzRdId] = useState("");
  const [wzLoading, setWzLoading] = useState(false);
  const [wzError, setWzError] = useState<string | null>(null);
  const [wzSuccess, setWzSuccess] = useState<string | null>(null);
  // Wizard step-local form state
  const [wzExpName, setWzExpName] = useState("Research experiment");
  const [wzExpHyp, setWzExpHyp] = useState("");
  const [wzExpAck, setWzExpAck] = useState(false);
  const [wzCmpName, setWzCmpName] = useState("Offline comparison");
  const [wzCmpAck, setWzCmpAck] = useState(false);
  const [wzRdName, setWzRdName] = useState("Research readiness review");
  const [wzRdAck, setWzRdAck] = useState(false);
  // Wizard: Step 1 create export
  const [wzNewExpName, setWzNewExpName] = useState("Local Research Dataset Export");
  const [wzNewExpStart, setWzNewExpStart] = useState("2026-03-15");
  const [wzNewExpEnd, setWzNewExpEnd] = useState("2026-04-15");
  const [wzNewExpFmt, setWzNewExpFmt] = useState<"jsonl" | "json">("jsonl");
  const [wzNewExpFeat, setWzNewExpFeat] = useState(true);
  const [wzNewExpTgt, setWzNewExpTgt] = useState(true);
  const [wzNewExpWarn, setWzNewExpWarn] = useState(true);
  const [wzNewExpAck, setWzNewExpAck] = useState(false);
  // Wizard: Step 1 verify
  const [wzVerifyResult, setWzVerifyResult] = useState<Record<string, unknown> | null>(null);
  // Wizard: Step 2 result import
  const [wzResSum, setWzResSum] = useState("");
  const [wzResMetrics, setWzResMetrics] = useState("{}");
  const [wzResAck, setWzResAck] = useState(false);
  const [wzResExpId, setWzResExpId] = useState("");
  // Wizard: Step 4 state update
  const [wzRdState, setWzRdState] = useState("draft");
  const [wzRdStateReason, setWzRdStateReason] = useState("");
  const [wzRdStateAck, setWzRdStateAck] = useState(false);

  const selectBenchmark = useCallback(async (b: RLBenchmarkReport) => {
    setSelectedBenchmark(b);
    setSelectedBenchAudit([]);
    try {
      const res = await fetchRLBenchmarkAuditForReport(b.id);
      if (res.data) setSelectedBenchAudit(res.data);
    } catch { /* audit unavailable for old benchmarks */ }
  }, []);

  const openBenchmarkById = useCallback(async (reportId: string) => {
    try {
      const res = await fetchRLBenchmark(reportId);
      if (res.data) {
        selectBenchmark(res.data);
        // Scroll to benchmark drilldown
        document.getElementById("benchmark-drilldown")?.scrollIntoView({ behavior: "smooth" });
      }
    } catch { /* benchmark may not exist */ }
  }, [selectBenchmark]);

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
        // Refresh candidates and select the new one
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

  const runDatasetExport = useCallback(async () => {
    if (!dsExportAck) return;
    setDsExportLoading(true);
    setDsExportError(null);
    setDsExportResult(null);
    try {
      const res = await createFinrlxDatasetExport({
        name: dsExportName,
        start_date: dsExportStart,
        end_date: dsExportEnd,
        candidate_id: dsExportCandidateId || null,
        benchmark_report_id: dsExportBenchmarkId || null,
        format: dsExportFormat,
        include_features: dsExportFeatures,
        include_targets: dsExportTargets,
        include_warnings: dsExportWarnings,
        research_acknowledgement: true,
      });
      if (res.data) {
        setDsExportResult(res.data);
        listFinrlxDatasetExports().then(r => { if (r.data) setDsExportHistory(r.data); }).catch(() => {});
      }
    } catch (e: unknown) {
      setDsExportError(e instanceof Error ? e.message : "Dataset export failed");
    } finally {
      setDsExportLoading(false);
    }
  }, [dsExportName, dsExportStart, dsExportEnd, dsExportCandidateId, dsExportBenchmarkId, dsExportFormat, dsExportFeatures, dsExportTargets, dsExportWarnings, dsExportAck]);

  const refreshExportHistory = useCallback(() => {
    listFinrlxDatasetExports().then(r => { if (r.data) setDsExportHistory(r.data); }).catch(() => {});
  }, []);

  const selectExportEntry = useCallback(async (entry: DatasetExportRegistryEntry) => {
    setDsSelectedExport(null);
    setDsVerifyResult(null);
    setDsStaleAck(false);
    setDsStaleReason("");
    setDsGovError(null);
    setDsGovSuccess(null);
    try {
      const res = await getFinrlxDatasetExport(entry.export_id);
      if (res.data) setDsSelectedExport(res.data);
    } catch { /* graceful */ }
  }, []);

  const handleVerifyExport = useCallback(async () => {
    if (!dsSelectedExport) return;
    setDsGovLoading("verify");
    setDsGovError(null);
    setDsVerifyResult(null);
    try {
      const res = await verifyFinrlxDatasetExport(dsSelectedExport.export_id);
      if (res.data) setDsVerifyResult(res.data);
    } catch (e: unknown) {
      setDsGovError(e instanceof Error ? e.message : "Verify failed");
    } finally {
      setDsGovLoading(null);
    }
  }, [dsSelectedExport]);

  const handleMarkStale = useCallback(async () => {
    if (!dsSelectedExport || !dsStaleAck) return;
    setDsGovLoading("stale");
    setDsGovError(null);
    setDsGovSuccess(null);
    try {
      await markFinrlxDatasetExportStale(dsSelectedExport.export_id, {
        acknowledgement: true, reason: dsStaleReason || undefined,
      });
      setDsGovSuccess("Export marked as stale.");
      refreshExportHistory();
      selectExportEntry({ ...dsExportHistory.find(e => e.export_id === dsSelectedExport.export_id)! });
    } catch (e: unknown) {
      setDsGovError(e instanceof Error ? e.message : "Mark stale failed");
    } finally {
      setDsGovLoading(null);
    }
  }, [dsSelectedExport, dsStaleAck, dsStaleReason, refreshExportHistory, selectExportEntry, dsExportHistory]);

  const handleRebuildRegistry = useCallback(async () => {
    if (!dsRebuildAck) return;
    setDsGovLoading("rebuild");
    setDsGovError(null);
    setDsGovSuccess(null);
    try {
      const res = await rebuildFinrlxDatasetExportRegistry({ acknowledgement: true });
      setDsGovSuccess(`Registry rebuilt: ${res.data.export_count} exports found.`);
      setDsRebuildAck(false);
      refreshExportHistory();
    } catch (e: unknown) {
      setDsGovError(e instanceof Error ? e.message : "Rebuild failed");
    } finally {
      setDsGovLoading(null);
    }
  }, [dsRebuildAck, refreshExportHistory]);

  // ── Experiment tracking callbacks ──
  const refreshExperiments = useCallback(() => {
    listFinrlxResearchExperiments().then(r => { if (r.data) setExpList(r.data); }).catch(() => {});
  }, []);

  const handleCreateExperiment = useCallback(async () => {
    if (!expAck || !expName.trim() || !expLinkedExportId.trim()) return;
    setExpCreateLoading(true);
    setExpCreateError(null);
    setExpCreateSuccess(null);
    let parsedParams: Record<string, unknown> = {};
    try { parsedParams = JSON.parse(expParams); } catch { /* use empty */ }
    const metricsList = expMetrics ? expMetrics.split(",").map(s => s.trim()).filter(Boolean) : [];
    try {
      const res = await createFinrlxResearchExperiment({
        name: expName.trim(),
        linked_export_id: expLinkedExportId.trim(),
        hypothesis: expHypothesis,
        method_notes: expMethodNotes,
        parameters: parsedParams,
        expected_metrics: metricsList,
        research_acknowledgement: true,
      });
      if (res.data?.experiment_id) {
        setExpCreateSuccess(`Experiment ${res.data.experiment_id.slice(0, 8)} created.`);
        setExpAck(false);
        refreshExperiments();
      }
    } catch (e: unknown) {
      setExpCreateError(e instanceof Error ? e.message : "Create experiment failed");
    } finally {
      setExpCreateLoading(false);
    }
  }, [expAck, expName, expLinkedExportId, expHypothesis, expMethodNotes, expParams, expMetrics, refreshExperiments]);

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

  // ── Comparison workbench callbacks ──
  const refreshComparisons = useCallback(() => {
    listFinrlxExperimentComparisons().then(r => { if (r.data) setCmpList(r.data); }).catch(() => {});
  }, []);

  const handleCreateComparison = useCallback(async () => {
    if (!cmpAck || !cmpName.trim() || !cmpExpIds.trim()) return;
    setCmpCreateLoading(true);
    setCmpCreateError(null);
    setCmpCreateSuccess(null);
    const ids = cmpExpIds.split(",").map(s => s.trim()).filter(Boolean);
    const priority = cmpPriority ? cmpPriority.split(",").map(s => s.trim()).filter(Boolean) : [];
    try {
      const res = await createFinrlxExperimentComparison({
        name: cmpName.trim(),
        experiment_ids: ids,
        metric_priority: priority,
        notes: cmpNotes,
        research_acknowledgement: true,
      });
      if (res.data?.comparison_id) {
        setCmpCreateSuccess(`Comparison ${res.data.comparison_id.slice(0, 8)} created.`);
        setCmpAck(false);
        refreshComparisons();
      }
    } catch (e: unknown) {
      setCmpCreateError(e instanceof Error ? e.message : "Create comparison failed");
    } finally {
      setCmpCreateLoading(false);
    }
  }, [cmpAck, cmpName, cmpExpIds, cmpPriority, cmpNotes, refreshComparisons]);

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

  // ── Readiness callbacks ──
  const refreshReadiness = useCallback(() => {
    listFinrlxResearchReadiness().then(r => { if (r.data) setRdList(r.data); }).catch(() => {});
  }, []);

  const handleCreateReadiness = useCallback(async () => {
    if (!rdAck || !rdName.trim() || !rdCmpId.trim()) return;
    setRdCreateLoading(true); setRdCreateError(null); setRdCreateSuccess(null);
    try {
      const res = await createFinrlxResearchReadiness({
        name: rdName.trim(), linked_comparison_id: rdCmpId.trim(),
        operator_notes: rdNotes, research_acknowledgement: true,
      });
      if (res.data?.readiness_id) {
        setRdCreateSuccess(`Readiness ${res.data.readiness_id.slice(0, 8)} created.`);
        setRdAck(false); refreshReadiness();
      }
    } catch (e: unknown) { setRdCreateError(e instanceof Error ? e.message : "Failed"); }
    finally { setRdCreateLoading(false); }
  }, [rdAck, rdName, rdCmpId, rdNotes, refreshReadiness]);

  const selectReadiness = useCallback(async (rv: ReadinessReview) => {
    setRdSelected(null); setRdVerifyResult(null); setRdStateAck(false); setRdArchiveAck(false);
    setRdError(null); setRdSuccess(null);
    try {
      const res = await getFinrlxResearchReadiness(rv.readiness_id);
      if (res.data) { setRdSelected(res.data); setRdStateValue(res.data.readiness_state); }
    } catch { /* */ }
  }, []);

  const handleRdVerify = useCallback(async () => {
    if (!rdSelected) return;
    setRdLoading("verify"); setRdError(null); setRdVerifyResult(null);
    try {
      const res = await verifyFinrlxResearchReadiness(rdSelected.readiness_id);
      if (res.data) setRdVerifyResult(res.data);
    } catch (e: unknown) { setRdError(e instanceof Error ? e.message : "Verify failed"); }
    finally { setRdLoading(null); }
  }, [rdSelected]);

  const handleRdStateUpdate = useCallback(async () => {
    if (!rdSelected || !rdStateAck) return;
    setRdLoading("state"); setRdError(null); setRdSuccess(null);
    try {
      await updateFinrlxResearchReadinessState(rdSelected.readiness_id, {
        readiness_state: rdStateValue, acknowledgement: true, reason: rdStateReason || undefined,
      });
      setRdSuccess(`State updated to ${rdStateValue}.`); setRdStateAck(false);
      refreshReadiness(); selectReadiness({ ...rdSelected, readiness_state: rdStateValue });
    } catch (e: unknown) { setRdError(e instanceof Error ? e.message : "Update failed"); }
    finally { setRdLoading(null); }
  }, [rdSelected, rdStateValue, rdStateAck, rdStateReason, refreshReadiness, selectReadiness]);

  const handleRdArchive = useCallback(async () => {
    if (!rdSelected || !rdArchiveAck) return;
    setRdLoading("archive"); setRdError(null); setRdSuccess(null);
    try {
      await archiveFinrlxResearchReadiness(rdSelected.readiness_id, { acknowledgement: true });
      setRdSuccess("Readiness review archived."); setRdArchiveAck(false);
      refreshReadiness(); selectReadiness({ ...rdSelected, readiness_state: "archived" });
    } catch (e: unknown) { setRdError(e instanceof Error ? e.message : "Archive failed"); }
    finally { setRdLoading(null); }
  }, [rdSelected, rdArchiveAck, refreshReadiness, selectReadiness]);

  useEffect(() => {
    Promise.all([
      fetchOps(),
      fetchMLOpsSummary().catch(() => null),
      fetchRLBenchmarks().catch(() => null),
      fetchRLBenchmarkAudit().catch(() => null),
      fetchFinRLXStatus().catch(() => null),
    ])
      .then(([opsRes, mlRes, benchRes, auditRes, finrlxRes]) => {
        setOps(opsRes.data);
        setFilteredQueue(opsRes.data.queue);
        setFilteredAudit(opsRes.data.audit);
        if (mlRes) setMlSummary(mlRes.data);
        if (benchRes && benchRes.data) {
          setBenchmarks(benchRes.data);
          if (benchRes.data.length > 0) selectBenchmark(benchRes.data[0]);
        }
        if (auditRes && auditRes.data) setBenchAuditEvents(auditRes.data);
        if (finrlxRes && finrlxRes.data) setFinrlxStatus(finrlxRes.data);
        fetchFinRLXDependencies().then(r => { if (r.data) setFinrlxDeps(r.data); }).catch(() => {});
        fetchFinRLXCandidates().then(r => {
          if (r.data) setImportedCandidates(r.data.filter(c => c.imported_from_artifact));
        }).catch(() => {});
        listFinrlxDatasetExports().then(r => { if (r.data) setDsExportHistory(r.data); }).catch(() => {});
        listFinrlxResearchExperiments().then(r => { if (r.data) setExpList(r.data); }).catch(() => {});
        listFinrlxExperimentComparisons().then(r => { if (r.data) setCmpList(r.data); }).catch(() => {});
        listFinrlxResearchReadiness().then(r => { if (r.data) setRdList(r.data); }).catch(() => {});
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectBenchmark]);

  // Queue filter handler
  const handleQueueFilter = useCallback(async (filter: string) => {
    setQueueFilter(filter);
    try {
      const res = await fetchOpsQueue(filter);
      setFilteredQueue(res.data);
    } catch {
      // fallback to local filter
      if (ops) {
        setFilteredQueue(
          filter === "all" ? ops.queue : ops.queue.filter((q) => q.priority === filter)
        );
      }
    }
  }, [ops]);

  // Audit scope handler
  const handleAuditScope = useCallback(async (scope: string) => {
    setAuditScope(scope);
    try {
      const res = await fetchOpsAudit(scope);
      setFilteredAudit(res.data);
    } catch {
      if (ops) setFilteredAudit(ops.audit);
    }
  }, [ops]);

  // Queue action handler
  const handleQueueAction = useCallback(async (id: string, action: "approve" | "defer" | "challenge") => {
    setActionLoading(id);
    try {
      const fn = action === "approve" ? approveQueueItem : action === "defer" ? deferQueueItem : challengeQueueItem;
      await fn(id);
      // Refresh queue
      const res = await fetchOpsQueue(queueFilter);
      setFilteredQueue(res.data);
      // Refresh full ops for KPI update
      const opsRes = await fetchOps();
      setOps(opsRes.data);
    } catch {
      // silently fail
    } finally {
      setActionLoading(null);
    }
  }, [queueFilter]);

  if (loading) return <PageLoading label="Loading Ops Command Center..." />;
  if (error) return <PageError title="Ops Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!ops) return null;

  return (
    <div className="space-y-gap max-w-[1400px] px-4 md:px-0">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Ops Command Center</h1>
        <p className="text-[12px] text-ink-3 mt-0.5">
          {filteredQueue.length} queued · {ops.breaches.filter(b => b.severity === "breach").length} breaches · {ops.incidents.length} incidents
        </p>
      </div>

      {/* ── Research Workflow Navigation (Phase 8M.1) ── */}
      <div className="flex flex-wrap gap-1.5">
        {([
          { key: "research-data" as const, label: "Research Data", count: dsExportHistory.length },
          { key: "experiments" as const, label: "Experiments", count: expList.length },
          { key: "comparisons" as const, label: "Comparisons", count: cmpList.length },
          { key: "readiness" as const, label: "Readiness", count: rdList.length },
          { key: "safety" as const, label: "Safety / Ops", count: null },
        ]).map(tab => (
          <button key={tab.key} onClick={() => setAdminTab(tab.key)}
            className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors ${
              adminTab === tab.key ? "bg-primary text-primary-ink" : "bg-surface-2 text-ink-3 hover:bg-surface-3"
            }`}>
            {tab.label}{tab.count !== null ? ` (${tab.count})` : ""}
          </button>
        ))}
      </div>

      {/* Workflow guidance */}
      {adminTab === "research-data" && dsExportHistory.length === 0 && (
        <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 text-[11px] text-ink-2">
          <strong className="text-ink">Next step:</strong> Create a dataset export to begin your research workflow.
        </div>
      )}
      {adminTab === "experiments" && expList.length === 0 && dsExportHistory.length > 0 && (
        <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 text-[11px] text-ink-2">
          <strong className="text-ink">Next step:</strong> Create a research experiment linked to an existing dataset export.
        </div>
      )}
      {adminTab === "comparisons" && cmpList.length === 0 && expList.length >= 2 && (
        <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 text-[11px] text-ink-2">
          <strong className="text-ink">Next step:</strong> Create an offline comparison from your research experiments.
        </div>
      )}
      {adminTab === "readiness" && rdList.length === 0 && cmpList.length > 0 && (
        <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 text-[11px] text-ink-2">
          <strong className="text-ink">Next step:</strong> Create a readiness review linked to an existing comparison.
        </div>
      )}

      {/* ── Guided Research Workflow CTA ── */}
      <div className="flex items-center gap-3">
        <button onClick={() => { setWizardOpen(true); setWizardStep(0); setWzError(null); setWzSuccess(null); }}
          className="px-4 py-2 rounded-md bg-primary text-primary-ink text-[12px] font-medium hover:opacity-90 transition-opacity">
          Start Research Workflow
        </button>
        <span className="text-[10px] text-ink-4">Guided flow for research-only dataset export, experiment tracking, comparison, and readiness review.</span>
      </div>

      {/* ── KPI Strip ── */}
      {adminTab === "safety" && <>
      {ops.system_kpis.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {ops.system_kpis.map((kpi) => (
            <div key={kpi.key} className="rounded-lg border border-line bg-surface p-3 text-center">
              <p className={`text-[20px] font-semibold font-mono ${KPI_TONE[kpi.tone] || "text-ink"}`}>{kpi.value}</p>
              <p className="text-[12px] text-ink-2 font-medium mt-0.5">{kpi.key}</p>
              {kpi.sub && <p className="text-[10px] text-ink-4">{kpi.sub}</p>}
            </div>
          ))}
        </div>
      )}

      {/* ── ML Observability ── */}
      {mlSummary && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
              <p className="text-[12px] font-medium text-ink">{mlSummary.validation_status || "—"}</p>
            </div>
            <div className="text-center">
              <p className="text-[11px] text-ink-4 mb-0.5">Accuracy</p>
              <p className="text-[12px] font-medium text-ink font-mono">
                {mlSummary.directional_accuracy != null
                  ? `${(mlSummary.directional_accuracy * 100).toFixed(0)}%`
                  : "—"}
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
                {mlSummary.promotion_readiness || "—"}
              </p>
            </div>
          </div>
          {/* Shadow vs Baseline delta */}
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
          {/* Warnings */}
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
          {/* Recommended action */}
          {mlSummary.recommended_operator_action && (
            <div className="flex items-center gap-2 text-[11px] border-t border-line pt-3">
              <span className="text-ink-4">Recommended:</span>
              <span className="font-medium text-ink-2">{mlSummary.recommended_operator_action.replace(/_/g, " ")}</span>
            </div>
          )}
        </section>
      )}

      {/* ── RL Environment ── */}
      {ops.rl && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
              <p className="text-[14px] font-semibold text-ink">{ops.rl.latest_benchmark_status || "—"}</p>
              <p className="text-[10px] text-ink-4">latest benchmark</p>
            </div>
            <div>
              <p className="text-[14px] font-semibold text-ink">{ops.rl.latest_training_agent?.replace(/_/g, " ") || "—"}</p>
              <p className="text-[10px] text-ink-4">latest agent</p>
            </div>
          </div>
        </section>
      )}

      {/* ── FinRL-X Research Spike ── */}
      {finrlxStatus && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
          {/* System-level research guardrails (not candidate-specific) */}
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
          {/* CPU-only dependency status */}
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
        </section>
      )}

      {/* ── Import Research Artifact ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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

        {/* Validation result */}
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

        {/* Import action */}
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
      </section>

      {/* ── Imported Research Candidates ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="sparkle" size={15} className="text-accent-2" />
          <h3 className="text-[13px] font-semibold text-ink">Imported Research Candidates</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Shadow / Offline</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Not eligible for promotion</span>
        </div>

        {importedCandidates.length === 0 ? (
          <p className="text-[11px] text-ink-4 py-2">No imported research candidates yet. Import a local research artifact before benchmarking.</p>
        ) : (
          <div className="space-y-1.5 mb-3">
            {importedCandidates.slice(0, 10).map((c) => (
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

        {/* ── Selected Candidate Review ── */}
        {selectedCandidate && (
          <div className="border-t border-line pt-3 mt-2 space-y-3">
            <h4 className="text-[12px] font-semibold text-ink">Candidate Review</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-[10px] sm:text-[10px]">
              <div><span className="text-ink-4">ID:</span> <span className="font-mono text-ink-2">{selectedCandidate.id}</span></div>
              <div><span className="text-ink-4">Policy type:</span> <span className="text-ink">{selectedCandidate.policy_type}</span></div>
              <div><span className="text-ink-4">Training mode:</span> <span className="text-ink">{selectedCandidate.training_mode}</span></div>
              <div><span className="text-ink-4">Artifact hash:</span> <span className="font-mono text-ink-2">{selectedCandidate.artifact_hash || "—"}</span></div>
              <div><span className="text-ink-4">Source:</span> <span className="text-ink">{selectedCandidate.source || "—"}</span></div>
              <div><span className="text-ink-4">Created:</span> <span className="text-ink">{selectedCandidate.created_at?.slice(0, 19) || "—"}</span></div>
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

            {/* Eligibility */}
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

            {/* ── Run Candidate Benchmark ── */}
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

            {/* ── Benchmark Result ── */}
            {candBenchResult && (
              <div className="border-t border-line pt-3">
                <h4 className="text-[12px] font-semibold text-ink mb-2">Benchmark Result</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-[10px] mb-2">
                  <div><span className="text-ink-4">Status:</span> <span className={candBenchResult.status === "completed" ? "text-pos font-medium" : "text-caution font-medium"}>{candBenchResult.status}</span></div>
                  <div><span className="text-ink-4">Inference:</span> <span className="text-ink">{candBenchResult.candidate_benchmark_context.inference_mode}</span></div>
                  <div><span className="text-ink-4">Neural inference:</span> <span className="text-pos font-medium">none (surrogate)</span></div>
                  <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-3">{candBenchResult.result_fingerprint?.slice(0, 12) || "—"}</span></div>
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
                          <td className="py-1 pr-2 font-mono text-ink-2">{agent.length > 24 ? agent.slice(0, 24) + "…" : agent}</td>
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

            {/* ── Candidate Benchmark History ── */}
            <div className="border-t border-line pt-3">
              <h4 className="text-[12px] font-semibold text-ink mb-2">Candidate Benchmark History</h4>
              {candidateBenchHistory.length === 0 ? (
                <p className="text-[10px] text-ink-4">No benchmark history for this imported candidate.</p>
              ) : (
                <div className="space-y-1">
                  {candidateBenchHistory.slice(0, 8).map((h, i) => (
                    <div key={i} className="flex flex-wrap items-center justify-between gap-1 rounded-md border border-line px-2 py-1.5 text-[10px]">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-ink-3">{h.benchmark_report_id?.slice(0, 8) || "—"}</span>
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
          </div>
        )}
      </section>
      </>}

      {/* ── Dataset Export for Local Research ── */}
      {adminTab === "research-data" && <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="sparkle" size={15} className="text-accent-2" />
          <h3 className="text-[13px] font-semibold text-ink">Dataset Export for Local Research</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Research-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Offline-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">No production influence</span>
        </div>
        <p className="text-[10px] text-ink-4 mb-3">
          Export shadow dataset for local offline research. Not used by production decisions. Not eligible for promotion. No broker execution.
        </p>

        {/* Export form */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <div className="sm:col-span-3">
            <label className="text-[10px] text-ink-4 block mb-1">Export name</label>
            <input type="text" value={dsExportName} onChange={(e) => setDsExportName(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">Start date</label>
            <input type="date" value={dsExportStart} onChange={(e) => setDsExportStart(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">End date</label>
            <input type="date" value={dsExportEnd} onChange={(e) => setDsExportEnd(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">Format</label>
            <select value={dsExportFormat} onChange={(e) => setDsExportFormat(e.target.value as "jsonl" | "json")}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none">
              <option value="jsonl">JSONL</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <div className="sm:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">Candidate ID (optional)</label>
              <input type="text" value={dsExportCandidateId} onChange={(e) => setDsExportCandidateId(e.target.value)}
                placeholder="Leave empty for general export"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-1">Benchmark report ID (optional)</label>
              <input type="text" value={dsExportBenchmarkId} onChange={(e) => setDsExportBenchmarkId(e.target.value)}
                placeholder="Leave empty"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none" />
            </div>
          </div>
        </div>

        {/* Checkboxes */}
        <div className="flex flex-wrap gap-4 mb-3 text-[11px]">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dsExportFeatures} onChange={(e) => setDsExportFeatures(e.target.checked)} className="rounded" />
            <span className="text-ink-2">Include features</span>
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dsExportTargets} onChange={(e) => setDsExportTargets(e.target.checked)} className="rounded" />
            <span className="text-ink-2">Include targets</span>
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dsExportWarnings} onChange={(e) => setDsExportWarnings(e.target.checked)} className="rounded" />
            <span className="text-ink-2">Include warnings</span>
          </label>
        </div>

        {/* Acknowledgement */}
        <label className="flex items-start gap-2 mb-3 cursor-pointer">
          <input type="checkbox" checked={dsExportAck} onChange={(e) => setDsExportAck(e.target.checked)} className="mt-0.5 rounded" />
          <span className="text-[10px] text-ink-3">
            I acknowledge this is a research-only, offline-only, shadow-only dataset export.
            It is not used by production decisions and is not eligible for promotion.
          </span>
        </label>

        {/* Run button */}
        <button
          onClick={runDatasetExport}
          disabled={dsExportLoading || !dsExportAck || !dsExportStart || !dsExportEnd}
          className="px-4 py-1.5 rounded-md text-[12px] font-medium bg-primary text-primary-ink hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {dsExportLoading ? "Exporting..." : "Run Dataset Export"}
        </button>

        {dsExportError && (
          <div className="mt-3 p-3 rounded-md bg-breach/10 border border-breach/20 text-[11px] text-breach break-words">{dsExportError}</div>
        )}

        {/* Result panel */}
        {dsExportResult && (
          <div className="mt-3 p-3 rounded-md bg-surface-2 border border-line text-[11px] space-y-1.5">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="font-semibold text-ink">Export completed</span>
              <span className="text-pos text-[10px]">{dsExportResult.status}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[10px]">
              <div><span className="text-ink-4">Export ID:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.export_id}</span></div>
              <div><span className="text-ink-4">Row count:</span> <span className="text-ink">{dsExportResult.row_count}</span></div>
              <div><span className="text-ink-4">Date range:</span> <span className="text-ink">{dsExportResult.date_range ? `${dsExportResult.date_range.start} - ${dsExportResult.date_range.end}` : "N/A"}</span></div>
              <div><span className="text-ink-4">Format:</span> <span className="text-ink">{dsExportResult.export_format}</span></div>
              <div className="sm:col-span-2"><span className="text-ink-4">Export path:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.export_path}</span></div>
              <div className="sm:col-span-2"><span className="text-ink-4">Checksum:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.checksum}</span></div>
              <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-2 break-all">{dsExportResult.fingerprint}</span></div>
            </div>
            {dsExportResult.feature_schema.length > 0 && (
              <div className="text-[10px]"><span className="text-ink-4">Features:</span> <span className="text-ink-2">{dsExportResult.feature_schema.join(", ")}</span></div>
            )}
            {dsExportResult.target_schema.length > 0 && (
              <div className="text-[10px]"><span className="text-ink-4">Targets:</span> <span className="text-ink-2">{dsExportResult.target_schema.join(", ")}</span></div>
            )}
            {dsExportResult.warnings.length > 0 && (
              <div className="text-[10px] text-caution">Warnings: {dsExportResult.warnings.join("; ")}</div>
            )}
            <div className="flex flex-wrap gap-1.5 mt-1">
              {Object.entries(dsExportResult.safety_flags).map(([k, v]) => (
                <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                  {k.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Export registry / governance */}
        <div className="mt-4 border-t border-line pt-3">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <h4 className="text-[12px] font-semibold text-ink">Dataset Export Governance</h4>
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Local export registry</span>
          </div>

          {dsGovError && <div className="mb-2 p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{dsGovError}</div>}
          {dsGovSuccess && <div className="mb-2 p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{dsGovSuccess}</div>}

          {/* Export registry list */}
          {dsExportHistory.length > 0 && (
            <div className="mb-3">
              <div className="space-y-1">
                {dsExportHistory.map((h) => (
                  <button key={h.export_id} onClick={() => selectExportEntry(h)}
                    className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                      dsSelectedExport?.export_id === h.export_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                    }`}>
                    <span className="font-mono text-ink-2 break-all">{h.export_id?.slice(0, 8)}</span>
                    <span className="text-ink font-medium truncate max-w-[150px]">{h.name}</span>
                    <span className="text-ink-3">{h.row_count} rows</span>
                    <span className="text-ink-4">{h.export_format}</span>
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                      h.lifecycle_state === "active" ? "bg-pos/10 text-pos" : "bg-caution/10 text-caution"
                    }`}>{h.lifecycle_state}</span>
                    <span className={`w-1.5 h-1.5 rounded-full ${h.artifact_exists ? "bg-pos" : "bg-breach"}`} title={h.artifact_exists ? "Artifact exists" : "Artifact missing"} />
                    <span className="text-ink-4 ml-auto">{h.created_at?.slice(0, 19)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected export detail */}
          {dsSelectedExport && (
            <div className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2 mb-3">
              <div className="font-semibold text-[11px] text-ink mb-1">Export Detail</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                <div><span className="text-ink-4">Export ID:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.export_id}</span></div>
                <div><span className="text-ink-4">Status:</span> <span className="text-ink">{dsSelectedExport.status}</span> / <span className={dsSelectedExport.lifecycle_state === "active" ? "text-pos" : "text-caution"}>{dsSelectedExport.lifecycle_state}</span></div>
                <div><span className="text-ink-4">Row count:</span> <span className="text-ink">{dsSelectedExport.row_count}</span></div>
                <div><span className="text-ink-4">Format:</span> <span className="text-ink">{dsSelectedExport.export_format}</span></div>
                <div className="sm:col-span-2"><span className="text-ink-4">Path:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.export_path}</span></div>
                <div className="sm:col-span-2"><span className="text-ink-4">Checksum:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.checksum}</span></div>
                <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-2 break-all">{dsSelectedExport.fingerprint}</span></div>
                <div><span className="text-ink-4">Artifact:</span> <span className={dsSelectedExport.artifact_exists ? "text-pos" : "text-breach"}>{dsSelectedExport.artifact_exists ? "exists" : "missing"}</span></div>
              </div>
              {dsSelectedExport.warnings && dsSelectedExport.warnings.length > 0 && (
                <div className="text-caution">Warnings: {dsSelectedExport.warnings.join("; ")}</div>
              )}
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(dsSelectedExport.safety_flags || {}).map(([k, v]) => (
                  <span key={k} className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos/10 text-pos" : "bg-breach/10 text-breach"}`}>
                    {k.replace(/_/g, " ")}
                  </span>
                ))}
              </div>

              {/* Operator controls */}
              <div className="flex flex-wrap gap-2 pt-2 border-t border-line/30">
                <button onClick={handleVerifyExport} disabled={dsGovLoading === "verify"}
                  className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
                  {dsGovLoading === "verify" ? "Verifying..." : "Verify Artifact"}
                </button>
              </div>

              {dsVerifyResult && (
                <div className="p-2 rounded-md bg-surface-3 text-[10px] space-y-1">
                  <div className="font-medium text-ink">Artifact Verification</div>
                  <div>Metadata: <span className={dsVerifyResult.metadata_exists ? "text-pos" : "text-breach"}>{dsVerifyResult.metadata_exists ? "found" : "missing"}</span></div>
                  <div>Data: <span className={dsVerifyResult.data_exists ? "text-pos" : "text-breach"}>{dsVerifyResult.data_exists ? "found" : "missing"}</span></div>
                  {dsVerifyResult.warnings.length > 0 && <div className="text-caution">{dsVerifyResult.warnings.join("; ")}</div>}
                </div>
              )}

              {/* Mark stale control */}
              {dsSelectedExport.lifecycle_state === "active" && (
                <div className="pt-2 border-t border-line/30 space-y-2">
                  <div className="text-[10px] text-ink-3 font-medium">Mark as Stale</div>
                  <input type="text" value={dsStaleReason} onChange={(e) => setDsStaleReason(e.target.value)}
                    placeholder="Reason (optional)"
                    className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
                  <label className="flex items-center gap-1.5 cursor-pointer text-[10px]">
                    <input type="checkbox" checked={dsStaleAck} onChange={(e) => setDsStaleAck(e.target.checked)} className="rounded" />
                    <span className="text-ink-3">I acknowledge this marks the export as stale (does not delete files)</span>
                  </label>
                  <button onClick={handleMarkStale} disabled={!dsStaleAck || dsGovLoading === "stale"}
                    className="px-3 py-1 rounded-md text-[10px] font-medium bg-caution/20 text-caution hover:bg-caution/30 disabled:opacity-40 transition-colors">
                    {dsGovLoading === "stale" ? "Marking..." : "Mark Stale"}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Rebuild registry control */}
          <div className="pt-2 border-t border-line/30">
            <div className="text-[10px] text-ink-3 font-medium mb-1">Rebuild Registry from Files</div>
            <label className="flex items-center gap-1.5 cursor-pointer text-[10px] mb-1.5">
              <input type="checkbox" checked={dsRebuildAck} onChange={(e) => setDsRebuildAck(e.target.checked)} className="rounded" />
              <span className="text-ink-3">I acknowledge this scans research/finrlx_cpu/exports/ and rebuilds the registry</span>
            </label>
            <button onClick={handleRebuildRegistry} disabled={!dsRebuildAck || dsGovLoading === "rebuild"}
              className="px-3 py-1 rounded-md text-[10px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40 transition-colors">
              {dsGovLoading === "rebuild" ? "Rebuilding..." : "Rebuild Registry"}
            </button>
          </div>
        </div>
      </section>}

      {/* ── Local Research Experiments (Phase 8J.1) ── */}
      {adminTab === "experiments" && <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
              <input type="text" value={expLinkedExportId} onChange={(e) => setExpLinkedExportId(e.target.value)}
                placeholder="paste export_id from dataset exports"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none font-mono" />
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
              disabled={expCreateLoading || !expAck || !expName.trim() || !expLinkedExportId.trim()}
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

            <div className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2 mb-3">
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
                <div className="sm:col-span-2"><span className="text-ink-4">Checksum:</span> <span className="font-mono text-ink-2 break-all">{expSelected.linked_export_checksum || "—"}</span></div>
                <div><span className="text-ink-4">Fingerprint:</span> <span className="font-mono text-ink-2 break-all">{expSelected.linked_export_fingerprint || "—"}</span></div>
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
                <p className="text-[9px] text-ink-4">Metadata-only import — no executable code, no file uploads. Offline research results only.</p>
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
            </div>
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
      </section>}

      {/* ── Offline Experiment Comparison Workbench (Phase 8K.1) ── */}
      {adminTab === "comparisons" && <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="compare" size={15} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Offline Experiment Comparison Workbench</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">research-only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">metadata-only comparison</span>
        </div>
        <p className="text-[10px] text-ink-4 mb-3">
          Compare offline research experiments using imported result metadata. Numeric metric sorting only — does not imply production suitability. Not eligible for promotion.
        </p>

        {/* Create comparison form */}
        <div className="space-y-2 mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Comparison name</label>
              <input type="text" value={cmpName} onChange={(e) => setCmpName(e.target.value)}
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Experiment IDs (comma-separated, min 2)</label>
              <input type="text" value={cmpExpIds} onChange={(e) => setCmpExpIds(e.target.value)}
                placeholder="exp-id-1, exp-id-2"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink font-mono focus:border-primary focus:outline-none" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Metric priority (comma-separated)</label>
              <input type="text" value={cmpPriority} onChange={(e) => setCmpPriority(e.target.value)}
                placeholder="sharpe_ratio, max_drawdown"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
            <div>
              <label className="text-[10px] text-ink-4 block mb-0.5">Notes</label>
              <input type="text" value={cmpNotes} onChange={(e) => setCmpNotes(e.target.value)}
                placeholder="Research comparison notes"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink focus:border-primary focus:outline-none" />
            </div>
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
              disabled={cmpCreateLoading || !cmpAck || !cmpName.trim() || !cmpExpIds.trim()}
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

            <div className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2">
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
            </div>
          </div>
        )}
      </section>}

      {/* ── Research Readiness Review (Phase 8L.1) ── */}
      {adminTab === "readiness" && <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
              <input type="text" value={rdCmpId} onChange={(e) => setRdCmpId(e.target.value)} placeholder="comparison_id"
                className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[11px] text-ink font-mono focus:border-primary focus:outline-none" />
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
          <button onClick={handleCreateReadiness} disabled={rdCreateLoading || !rdAck || !rdName.trim() || !rdCmpId.trim()}
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

            <div className="p-3 rounded-md bg-surface-2 border border-line text-[10px] space-y-2">
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
                      {f.operator_action && <span className="text-ink-4 ml-1">— {f.operator_action}</span>}
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
            </div>
          </div>
        )}
      </section>}

      {/* ── Run Offline Benchmark ── */}
      {adminTab === "safety" && <><section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Icon name="sparkle" size={15} className="text-accent" />
          <h3 className="text-[13px] font-semibold text-ink">Run Offline Benchmark</h3>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">Offline / Shadow only</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface-3 text-ink-3">No broker execution</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">Benchmark name</label>
            <input
              type="text" value={benchRunName} onChange={(e) => setBenchRunName(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none"
            />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">Start date</label>
            <input
              type="date" value={benchRunStart} onChange={(e) => setBenchRunStart(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none"
            />
          </div>
          <div>
            <label className="text-[10px] text-ink-4 block mb-1">End date</label>
            <input
              type="date" value={benchRunEnd} onChange={(e) => setBenchRunEnd(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded-md border border-line bg-surface text-[12px] text-ink focus:border-primary focus:outline-none"
            />
          </div>
        </div>
        {/* Agent selection */}
        <div className="mb-3">
          <label className="text-[10px] text-ink-4 block mb-1">Agents to compare</label>
          <div className="flex flex-wrap gap-2">
            {["heuristic_baseline", "random_valid", "score_weighted_baseline"].map((ak) => (
              <label key={ak} className="flex items-center gap-1.5 text-[11px] text-ink-2 cursor-pointer">
                <input
                  type="checkbox" checked={benchRunAgents[ak] ?? false}
                  onChange={(e) => setBenchRunAgents((prev) => ({ ...prev, [ak]: e.target.checked }))}
                  className="rounded"
                />
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
        {/* Safety acknowledgment */}
        <div className="rounded-lg border border-line bg-surface-2 p-3 mb-3">
          <label className="flex items-start gap-2 text-[11px] text-ink-2 cursor-pointer">
            <input
              type="checkbox" checked={benchRunAcknowledged}
              onChange={(e) => setBenchRunAcknowledged(e.target.checked)}
              className="rounded mt-0.5"
            />
            <span>
              I understand this is an <strong className="text-ink">offline/shadow benchmark only</strong>.
              It cannot affect live recommendations, production decisions, broker systems, or publication workflow.
            </span>
          </label>
        </div>
        {/* Validation + submit */}
        <div className="flex items-center gap-3">
          <button
            disabled={
              benchRunLoading ||
              !benchRunAcknowledged ||
              !benchRunName.trim() ||
              !benchRunStart ||
              !benchRunEnd ||
              benchRunStart > benchRunEnd ||
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
                  selectedAllRequired &&
                  executedAllRequired &&
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
                    ? `Benchmark ${report.id.slice(0, 8)}... completed — ${report.executed_agents?.length || 0} agents compared`
                    : `partial|Offline benchmark created with partial scope — ${partialReason}. ${report.executed_agents?.length || 0} executed.`
                );
                // Refresh benchmarks + audit and select the new one
                const refreshed = await fetchRLBenchmarks().catch(() => null);
                if (refreshed && refreshed.data) {
                  setBenchmarks(refreshed.data);
                  selectBenchmark(report);
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
        {/* Result messages */}
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
      </section>

      {/* ── RL Offline Benchmark — Forensic Analysis ── */}
      {benchmarks.length === 0 && ops && ops.rl && ops.rl.total_benchmarks === 0 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <Icon name="compare" size={15} className="text-ink-4" />
            <h3 className="text-[13px] font-semibold text-ink-3">Offline Benchmark</h3>
          </div>
          <p className="text-[12px] text-ink-3">No offline benchmarks have been run yet. Use the RL benchmark API to compare agents on historical data.</p>
          <p className="text-[10px] text-ink-4 mt-1">This is an offline/shadow forensic tool — not a live recommendation system.</p>
        </section>
      )}

      {/* Benchmark History */}
      {benchmarks.length > 0 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="history" size={15} className="text-accent" />
            <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark History</h3>
            <span className="text-[10px] text-ink-4 ml-auto">{benchmarks.length} report{benchmarks.length !== 1 ? "s" : ""}</span>
          </div>
          <div className="space-y-1">
            {benchmarks.slice(0, 8).map((b) => (
              <div
                key={b.id}
                onClick={() => selectBenchmark(b)}
                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                  selectedBenchmark?.id === b.id ? "bg-primary-soft border border-primary" : "hover:bg-surface-3"
                }`}
              >
                <div className="flex items-center gap-2">
                  <StatusBadge status={b.status} />
                  <span className="text-[12px] text-ink-2">{b.name}</span>
                  <span className="text-[10px] text-ink-4 font-mono">{b.start_date} — {b.end_date}</span>
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
        </section>
      )}

      {/* Selected Benchmark Drill-down */}
      {selectedBenchmark && (
        <section id="benchmark-drilldown" className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Icon name="compare" size={15} className="text-accent" />
            <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark — Forensic Comparison</h3>
            <StatusBadge status={selectedBenchmark.status} />
            {selectedBenchmark.is_complete_comparison ? (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-pos-soft text-pos-soft-ink">Complete</span>
            ) : (
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-caution-soft text-caution-soft-ink">Partial</span>
            )}
            <span className="text-[10px] text-ink-4 ml-auto font-mono">{selectedBenchmark.id.slice(0, 8)}...</span>
          </div>

          {/* Safety badges — all 6 */}
          <div className="flex flex-wrap gap-1.5 mb-4">
            {[
              { key: "offline_only", label: "Offline only", safeWhen: true },
              { key: "shadow_only", label: "Shadow only", safeWhen: true },
              { key: "live_pipeline_influence", label: "No live pipeline influence", safeWhen: false },
              { key: "no_broker_execution", label: "No broker execution", safeWhen: true },
              { key: "no_publication_influence", label: "No publication influence", safeWhen: true },
              { key: "no_recommendation_pollution", label: "Not a live recommendation", safeWhen: true },
            ].map((f) => {
              const raw = (selectedBenchmark.safety_flags as unknown as Record<string, boolean>)?.[f.key];
              const isSafe = raw === f.safeWhen;
              return (
                <span key={f.key} className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium ${
                  isSafe ? "bg-surface-3 text-ink-3" : "bg-breach-soft text-breach-soft-ink"
                }`}>{isSafe ? f.label : `WARNING: ${f.key}`}</span>
              );
            })}
          </div>

          {/* Benchmark metadata */}
          <div className="flex items-center gap-4 text-[11px] text-ink-3 mb-4 flex-wrap">
            <span>Window: {selectedBenchmark.start_date} — {selectedBenchmark.end_date}</span>
            <span>Agents: {selectedBenchmark.executed_agents?.length || 0} executed</span>
            {selectedBenchmark.skipped_agents?.length > 0 && (
              <span className="text-caution">{selectedBenchmark.skipped_agents.length} skipped</span>
            )}
            {selectedBenchmark.environment_key && <span>Env: {selectedBenchmark.environment_key}</span>}
            {selectedBenchmark.created_at && <span>Created: {selectedBenchmark.created_at.slice(0, 16).replace("T", " ")}</span>}
          </div>

          {/* Skipped agents warning */}
          {selectedBenchmark.skipped_agents?.length > 0 && (
            <div className="rounded-lg border border-caution bg-caution-soft p-3 mb-4 text-[12px] text-caution-soft-ink">
              <p className="font-medium mb-1">Skipped agents:</p>
              {selectedBenchmark.skipped_agents.map((s, i) => (
                <p key={i}>{s.agent_key}: {s.reason}</p>
              ))}
            </div>
          )}

          {/* Agent comparison table */}
          {selectedBenchmark.metrics_by_agent && Object.keys(selectedBenchmark.metrics_by_agent).length > 0 && (
            <div className="mb-4">
              <h4 className="text-[12px] font-semibold text-ink mb-2">Agent Comparison — Offline Metrics</h4>
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
                      const agents = Object.entries(selectedBenchmark.metrics_by_agent);
                      const bestReturn = Math.max(...agents.map(([, m]) => m.total_return ?? -Infinity));
                      const bestReward = Math.max(...agents.map(([, m]) => m.total_reward ?? -Infinity));
                      const lowestDrawdown = Math.max(...agents.map(([, m]) => m.max_drawdown ?? -Infinity));
                      const lowestTurnover = Math.min(...agents.filter(([, m]) => m.total_turnover != null).map(([, m]) => m.total_turnover!));
                      return agents.map(([key, m]) => (
                        <tr key={key} className="border-b border-line/50 hover:bg-surface-3 transition-colors">
                          <td className="py-2 pr-3 font-medium text-ink">{key.replace(/_/g, " ")}</td>
                          <td className={`py-2 pr-3 text-right font-mono ${m.total_return === bestReturn ? "text-pos font-semibold" : "text-ink-2"}`}>
                            {m.total_return != null ? `${(m.total_return * 100).toFixed(2)}%` : "—"}
                          </td>
                          <td className={`py-2 pr-3 text-right font-mono ${m.total_reward === bestReward ? "text-pos font-semibold" : "text-ink-2"}`}>
                            {m.total_reward?.toFixed(4) ?? "—"}
                          </td>
                          <td className={`py-2 pr-3 text-right font-mono ${m.max_drawdown === lowestDrawdown ? "text-pos font-semibold" : "text-ink-2"}`}>
                            {m.max_drawdown != null ? `${(m.max_drawdown * 100).toFixed(2)}%` : "—"}
                          </td>
                          <td className={`py-2 pr-3 text-right font-mono ${m.total_turnover === lowestTurnover ? "text-pos font-semibold" : "text-ink-2"}`}>
                            {m.total_turnover?.toFixed(2) ?? "—"}
                          </td>
                          <td className="py-2 pr-3 text-right font-mono text-ink-3">{m.step_count ?? "—"}</td>
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
                Green highlight: best offline return · highest offline reward · lowest drawdown · lowest turnover in this benchmark. Not a live recommendation.
              </p>
            </div>
          )}

          {/* Reward breakdown */}
          {selectedBenchmark.reward_breakdown_by_agent && Object.keys(selectedBenchmark.reward_breakdown_by_agent).length > 0 && (
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
                    {Object.entries(selectedBenchmark.reward_breakdown_by_agent).map(([key, rb]) => (
                      <tr key={key} className="border-b border-line/50">
                        <td className="py-2 pr-3 text-ink-2">{key.replace(/_/g, " ")}</td>
                        <td className="py-2 pr-3 text-right font-mono text-ink-2">{rb.portfolio_return_component?.toFixed(4) ?? "—"}</td>
                        <td className="py-2 pr-3 text-right font-mono text-caution">{rb.drawdown_penalty_component?.toFixed(4) ?? "—"}</td>
                        <td className="py-2 text-right font-mono text-ink-3">{rb.turnover_penalty_component?.toFixed(6) ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Equity / Portfolio Value Curve */}
          {(() => {
            const forensicByAgent = selectedBenchmark.forensic_summary_by_agent;
            const agentKeys = forensicByAgent ? Object.keys(forensicByAgent) : [];
            const hasPerAgent = agentKeys.length > 0;
            const displaySteps = hasPerAgent
              ? forensicByAgent![agentKeys[0]] || []
              : selectedBenchmark.forensic_summary || [];
            if (displaySteps.length === 0) return null;
            return (
              <div className="mb-4">
                <h4 className="text-[12px] font-semibold text-ink mb-1">Offline Forensic Portfolio Value Curve</h4>
                <p className="text-[10px] text-ink-4 mb-2">
                  {hasPerAgent
                    ? `Per-agent portfolio value available for: ${agentKeys.map(k => k.replace(/_/g, " ")).join(", ")}`
                    : `Portfolio value curve based on: ${displaySteps[0]?.agent_key?.replace(/_/g, " ") || "first agent"}`
                  }. Offline forensic curve only — no production influence.
                </p>
                {/* Simple inline SVG sparkline per agent */}
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

          {/* Forensic step summary — per-agent drill-down */}
          {(() => {
            const byAgent = selectedBenchmark.forensic_summary_by_agent;
            const hasPerAgent = byAgent && Object.keys(byAgent).length > 0;
            const agentKeys = hasPerAgent ? Object.keys(byAgent!) : [];
            const activeAgent = hasPerAgent
              ? (selectedForensicAgent && agentKeys.includes(selectedForensicAgent) ? selectedForensicAgent : agentKeys[0])
              : null;
            const rows = hasPerAgent && activeAgent
              ? (byAgent![activeAgent] || [])
              : (selectedBenchmark.forensic_summary || []);
            if (rows.length === 0) return null;
            return (
              <div className="mb-3">
                <h4 className="text-[12px] font-semibold text-ink mb-2">Forensic Step Summary</h4>
                {hasPerAgent ? (
                  <>
                    <div className="flex items-center gap-1 mb-2">
                      {agentKeys.map((ak) => (
                        <button
                          key={ak}
                          onClick={() => setSelectedForensicAgent(ak)}
                          className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                            ak === activeAgent ? "bg-primary text-primary-ink" : "text-ink-3 hover:bg-surface-3"
                          }`}
                        >{ak.replace(/_/g, " ")}</button>
                      ))}
                    </div>
                    <p className="text-[10px] text-ink-4 mb-2">
                      Step-level forensic detail for: {activeAgent?.replace(/_/g, " ")} · up to 50 rows per agent · offline forensic only
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
                          <td className="py-1.5 pr-2 font-mono text-ink-2">{s.as_of_date?.slice(5) || "—"}</td>
                          <td className="py-1.5 pr-2 text-ink-2">{s.action_type || "—"}</td>
                          <td className={`py-1.5 pr-2 text-right font-mono ${(s.reward ?? 0) >= 0 ? "text-ink-2" : "text-breach"}`}>{s.reward?.toFixed(4) ?? "—"}</td>
                          <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{s.portfolio_value?.toFixed(1) ?? "—"}</td>
                          <td className="py-1.5 pr-2 text-right font-mono text-ink-3">{s.turnover?.toFixed(2) ?? "—"}</td>
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

          {/* Warnings */}
          {selectedBenchmark.warnings && selectedBenchmark.warnings.length > 0 && (
            <div className="rounded-lg border border-caution bg-caution-soft p-3 text-[11px] text-caution-soft-ink">
              {selectedBenchmark.warnings.map((w, i) => (
                <p key={i} className="flex items-center gap-1.5">
                  <Icon name="alert-triangle" size={10} />{w}
                </p>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Benchmark Governance & Audit Trail */}
      {benchAuditEvents.length > 0 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="history" size={15} className="text-ink-3" />
            <h3 className="text-[13px] font-semibold text-ink">Benchmark Governance & Audit Trail</h3>
            <span className="text-[10px] text-ink-4 ml-auto">{benchAuditEvents.length} event{benchAuditEvents.length !== 1 ? "s" : ""} — offline forensic audit</span>
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
                {benchAuditEvents.slice(0, 20).map((ev) => {
                  const invPassed = ev.invariant_check_results?.all_passed;
                  return (
                    <tr key={ev.id} className="border-b border-line/30">
                      <td className="py-1.5 pr-2 font-mono text-ink-3">{ev.created_at?.slice(11, 19) || "—"}</td>
                      <td className="py-1.5 pr-2 text-ink-2">{ev.event_type?.replace(/_/g, " ") || "—"}</td>
                      <td className="py-1.5 pr-2 font-mono text-ink-3">{ev.benchmark_report_id?.slice(0, 6) || "—"}</td>
                      <td className="py-1.5 pr-2">
                        {ev.status && <StatusBadge status={ev.status} />}
                      </td>
                      <td className="py-1.5 pr-2 text-right font-mono text-ink-3">
                        {ev.executed_agents?.length || "—"}/{ev.requested_agents?.length || "—"}
                      </td>
                      <td className="py-1.5 pr-2 font-mono text-ink-4 text-[9px]">{ev.result_fingerprint?.slice(0, 12) || "—"}</td>
                      <td className="py-1.5">
                        {invPassed === true && <span className="text-[9px] font-medium text-pos">passed</span>}
                        {invPassed === false && <span className="text-[9px] font-medium text-breach">failed</span>}
                        {invPassed == null && <span className="text-[9px] text-ink-4">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-ink-4 mt-2">Offline benchmark forensic audit trail — not used by production decisions.</p>
        </section>
      )}

      {/* Audit Trail — Selected Benchmark */}
      {selectedBenchmark && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="history" size={14} className="text-ink-3" />
            <h4 className="text-[12px] font-semibold text-ink">Audit Trail — Selected Benchmark</h4>
            <span className="text-[10px] text-ink-4 font-mono ml-auto">{selectedBenchmark.id.slice(0, 8)}...</span>
          </div>
          {selectedBenchAudit.length > 0 ? (
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
                  {selectedBenchAudit.map((ev) => (
                    <tr key={ev.id} className="border-b border-line/30">
                      <td className="py-1.5 pr-2 font-mono text-ink-3">{ev.created_at?.slice(11, 19) || "—"}</td>
                      <td className="py-1.5 pr-2 text-ink-2">{ev.event_type?.replace(/_/g, " ") || "—"}</td>
                      <td className="py-1.5 pr-2">{ev.status ? <StatusBadge status={ev.status} /> : "—"}</td>
                      <td className="py-1.5 pr-2 text-right font-mono text-ink-3">{ev.executed_agents?.length || "—"}/{ev.requested_agents?.length || "—"}</td>
                      <td className="py-1.5 pr-2 font-mono text-ink-4 text-[9px]">{ev.result_fingerprint?.slice(0, 12) || "—"}</td>
                      <td className="py-1.5">
                        {ev.invariant_check_results?.all_passed === true && <span className="text-[9px] font-medium text-pos">passed</span>}
                        {ev.invariant_check_results?.all_passed === false && <span className="text-[9px] font-medium text-breach">failed</span>}
                        {ev.invariant_check_results == null && <span className="text-[9px] text-ink-4">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-[11px] text-ink-3 mb-3">No audit events recorded for this benchmark. Audit trail is available for benchmark runs created after Phase 7G.</p>
          )}
          {/* Governance: fingerprint + invariants */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px] pt-3 border-t border-line">
            <div>
              <p className="text-[10px] text-ink-4 mb-0.5">Result fingerprint</p>
              {selectedBenchmark.result_fingerprint ? (
                <p className="font-mono text-ink-3 text-[10px] break-all">{selectedBenchmark.result_fingerprint}</p>
              ) : (
                <p className="text-ink-4 text-[10px]">No result fingerprint — this benchmark likely predates Phase 7G governance.</p>
              )}
            </div>
            <div>
              <p className="text-[10px] text-ink-4 mb-0.5">Invariant checks</p>
              {selectedBenchmark.invariant_check_results ? (
                <div className="flex flex-wrap gap-1">
                  {Object.entries(selectedBenchmark.invariant_check_results).filter(([k]) => k !== "all_passed").map(([k, v]) => (
                    <span key={k} className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${v ? "bg-pos-soft text-pos-soft-ink" : "bg-breach-soft text-breach-soft-ink"}`}>
                      {k.replace(/_/g, " ")}: {v ? "pass" : "FAIL"}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-ink-4 text-[10px]">No invariant data — this benchmark likely predates Phase 7G governance.</p>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Benchmark Trend Table */}
      {benchmarks.length > 1 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Icon name="trend-up" size={15} className="text-ink-3" />
            <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark Trend</h3>
            <span className="text-[10px] text-ink-4 ml-auto">Across {benchmarks.length} reports — not live performance</span>
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
                {benchmarks.slice(0, 5).flatMap((b) =>
                  Object.entries(b.metrics_by_agent || {}).map(([agent, m]) => (
                    <tr key={`${b.id}-${agent}`} className="border-b border-line/30">
                      <td className="py-1.5 pr-2 text-ink-3 font-mono">{b.id.slice(0, 6)}</td>
                      <td className="py-1.5 pr-2 text-ink-3">{b.start_date?.slice(5)} — {b.end_date?.slice(5)}</td>
                      <td className="py-1.5 pr-2 text-ink-2">{agent.replace(/_/g, " ")}</td>
                      <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{m.total_return != null ? `${(m.total_return * 100).toFixed(2)}%` : "—"}</td>
                      <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{m.total_reward?.toFixed(4) ?? "—"}</td>
                      <td className="py-1.5 pr-2 text-right font-mono text-ink-2">{m.max_drawdown != null ? `${(m.max_drawdown * 100).toFixed(2)}%` : "—"}</td>
                      <td className="py-1.5 text-right font-mono text-ink-3">{m.total_turnover?.toFixed(2) ?? "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ── Publication Queue ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <Icon name="decision" size={15} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Publication Queue</h3>
          <div className="flex items-center gap-1 ml-4">
            {QUEUE_FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => handleQueueFilter(f.key)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  queueFilter === f.key
                    ? "bg-primary text-primary-ink"
                    : "text-ink-3 hover:bg-surface-3"
                }`}
              >
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
                    <span className="text-ink-4 text-[10px] ml-1">{q.version} · {q.submitted_ago}</span>
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
                        <button
                          onClick={() => handleQueueAction(q.id!, "approve")}
                          disabled={actionLoading === q.id}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-pos-soft text-pos-soft-ink hover:opacity-80 transition-opacity disabled:opacity-40"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleQueueAction(q.id!, "defer")}
                          disabled={actionLoading === q.id}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-caution-soft text-caution-soft-ink hover:opacity-80 transition-opacity disabled:opacity-40"
                        >
                          Defer
                        </button>
                        <button
                          onClick={() => handleQueueAction(q.id!, "challenge")}
                          disabled={actionLoading === q.id}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-breach-soft text-breach-soft-ink hover:opacity-80 transition-opacity disabled:opacity-40"
                        >
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
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-gap">
        {/* ── Data Feeds ── */}
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
        </section>

        {/* ── Engine Health ── */}
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
        </section>
      </div>

      {/* ── Policy / Integrations / Universe strip ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gap">
        {/* Policy Rules */}
        {ops.policy && (
          <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
          </section>
        )}

        {/* Integrations */}
        {ops.integrations_summary && (
          <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
          </section>
        )}

        {/* Universe */}
        {ops.universe && (
          <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
          </section>
        )}
      </div>

      {/* ── Breach Watch ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-gap">
        {/* ── Incidents ── */}
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
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
        </section>

        {/* ── Audit Trail ── */}
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Icon name="history" size={15} className="text-ink-3" />
            <h3 className="text-[13px] font-semibold text-ink">Audit Trail</h3>
            <div className="flex items-center gap-1 ml-4">
              {AUDIT_SCOPES.map((s) => (
                <button
                  key={s.key}
                  onClick={() => handleAuditScope(s.key)}
                  className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                    auditScope === s.key
                      ? "bg-primary text-primary-ink"
                      : "text-ink-3 hover:bg-surface-3"
                  }`}
                >
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
        </section>
      </div>

      </>}

      {/* ── Guided Research Workflow Wizard Modal (Phase 8M.2) ── */}
      {wizardOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm">
          <div className="bg-surface border border-line rounded-xl shadow-xl w-full max-w-[700px] max-h-[90vh] overflow-y-auto p-6 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-[16px] font-semibold text-ink">Guided Research Workflow</h2>
                <p className="text-[10px] text-ink-4">Research-only, offline-only. Does not imply production suitability.</p>
              </div>
              <button onClick={() => setWizardOpen(false)} className="text-ink-3 hover:text-ink text-[18px] px-2">×</button>
            </div>

            {/* Stepper */}
            <div className="flex gap-1">
              {["Research Data", "Experiment", "Comparison", "Readiness"].map((label, i) => (
                <button key={label} onClick={() => { setWizardStep(i); setWzError(null); setWzSuccess(null); setWzVerifyResult(null); }}
                  className={`flex-1 py-1.5 rounded-md text-[10px] font-medium transition-colors ${
                    wizardStep === i ? "bg-primary text-primary-ink" :
                    (i === 0 && wzExportId) || (i === 1 && wzExpIds.length > 0) || (i === 2 && wzCmpId) || (i === 3 && wzRdId)
                      ? "bg-pos/10 text-pos" : "bg-surface-2 text-ink-3"
                  }`}>
                  {i + 1}. {label}
                </button>
              ))}
            </div>

            {wzError && <div className="p-2 rounded-md bg-breach/10 border border-breach/20 text-[10px] text-breach break-words">{wzError}</div>}
            {wzSuccess && <div className="p-2 rounded-md bg-pos/10 border border-pos/20 text-[10px] text-pos">{wzSuccess}</div>}

            {/* ═══ Step 1: Research Data ═══ */}
            {wizardStep === 0 && (
              <div className="space-y-3">
                <h3 className="text-[13px] font-semibold text-ink">Step 1: Select or Create Dataset Export</h3>
                <p className="text-[10px] text-ink-4">Choose an existing governed dataset export or create a new one.</p>

                {dsExportHistory.length > 0 && (
                  <div className="space-y-1 max-h-[150px] overflow-y-auto">
                    {dsExportHistory.slice(0, 10).map(exp => (
                      <button key={exp.export_id} onClick={() => { setWzExportId(exp.export_id); setWzSuccess(`Selected export ${exp.export_id.slice(0, 8)}`); setWzError(null); setWzVerifyResult(null); }}
                        className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                          wzExportId === exp.export_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                        }`}>
                        <span className="font-mono text-ink-2">{exp.export_id?.slice(0, 8)}</span>
                        <span className="text-ink font-medium truncate max-w-[120px]">{exp.name}</span>
                        <span className="text-ink-3">{exp.row_count} rows</span>
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                          exp.lifecycle_state === "active" ? "bg-pos/10 text-pos" : "bg-caution/10 text-caution"
                        }`}>{exp.lifecycle_state}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Create new export */}
                <details className="border border-line/30 rounded-md">
                  <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">Create new dataset export</summary>
                  <div className="p-2 space-y-2">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <input type="text" value={wzNewExpName} onChange={e => setWzNewExpName(e.target.value)} placeholder="Export name"
                        className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <select value={wzNewExpFmt} onChange={e => setWzNewExpFmt(e.target.value as "jsonl" | "json")}
                        className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none">
                        <option value="jsonl">JSONL</option><option value="json">JSON</option>
                      </select>
                      <input type="date" value={wzNewExpStart} onChange={e => setWzNewExpStart(e.target.value)}
                        className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <input type="date" value={wzNewExpEnd} onChange={e => setWzNewExpEnd(e.target.value)}
                        className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                    </div>
                    <div className="flex flex-wrap gap-3 text-[9px] text-ink-3">
                      <label className="flex items-center gap-1 cursor-pointer"><input type="checkbox" checked={wzNewExpFeat} onChange={e => setWzNewExpFeat(e.target.checked)} className="rounded" /> Features</label>
                      <label className="flex items-center gap-1 cursor-pointer"><input type="checkbox" checked={wzNewExpTgt} onChange={e => setWzNewExpTgt(e.target.checked)} className="rounded" /> Targets</label>
                      <label className="flex items-center gap-1 cursor-pointer"><input type="checkbox" checked={wzNewExpWarn} onChange={e => setWzNewExpWarn(e.target.checked)} className="rounded" /> Warnings</label>
                    </div>
                    <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                      <input type="checkbox" checked={wzNewExpAck} onChange={e => setWzNewExpAck(e.target.checked)} className="rounded" />
                      Research-only offline export (required)
                    </label>
                    <button disabled={wzLoading || !wzNewExpAck || !wzNewExpName.trim()} onClick={async () => {
                      setWzLoading(true); setWzError(null); setWzSuccess(null);
                      try {
                        const res = await createFinrlxDatasetExport({
                          name: wzNewExpName.trim(), start_date: wzNewExpStart, end_date: wzNewExpEnd,
                          format: wzNewExpFmt, include_features: wzNewExpFeat, include_targets: wzNewExpTgt,
                          include_warnings: wzNewExpWarn, research_acknowledgement: true,
                        });
                        if (res.data?.export_id) {
                          setWzExportId(res.data.export_id);
                          setWzSuccess(`Export ${res.data.export_id.slice(0, 8)} created (${res.data.row_count} rows, checksum: ${res.data.checksum?.slice(0, 8)})`);
                          setWzNewExpAck(false);
                          refreshExportHistory();
                        }
                      } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Export failed"); }
                      finally { setWzLoading(false); }
                    }} className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40">
                      {wzLoading ? "Exporting..." : "Create Export"}
                    </button>
                  </div>
                </details>

                {/* Verify + Expert link */}
                <div className="flex flex-wrap items-center gap-2">
                  {wzExportId && (
                    <button disabled={wzLoading} onClick={async () => {
                      setWzLoading(true); setWzVerifyResult(null); setWzError(null);
                      try {
                        const res = await verifyFinrlxDatasetExport(wzExportId);
                        setWzVerifyResult(res.data as unknown as Record<string, unknown>);
                      } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Verify failed"); }
                      finally { setWzLoading(false); }
                    }} className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40">
                      Verify selected export
                    </button>
                  )}
                  <button onClick={() => { setWizardOpen(false); setAdminTab("research-data"); }}
                    className="text-[10px] text-primary hover:underline">Open in Expert Tab →</button>
                </div>
                {wzVerifyResult && (
                  <div className="p-2 rounded-md bg-surface-3 text-[9px] space-y-0.5">
                    <div>Artifact: <span className={(wzVerifyResult as Record<string, unknown>).artifact_exists ? "text-pos" : "text-breach"}>{(wzVerifyResult as Record<string, unknown>).artifact_exists ? "exists" : "missing"}</span></div>
                    {Array.isArray((wzVerifyResult as Record<string, unknown>).warnings) && ((wzVerifyResult as Record<string, unknown>).warnings as string[]).length > 0 && (
                      <div className="text-caution">{((wzVerifyResult as Record<string, unknown>).warnings as string[]).join("; ")}</div>
                    )}
                  </div>
                )}

                {wzExportId && <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">Selected: <span className="font-mono">{wzExportId.slice(0, 16)}</span></div>}
                {!wzExportId && <p className="text-[9px] text-caution">Select or create an export to proceed.</p>}
              </div>
            )}

            {/* ═══ Step 2: Experiment ═══ */}
            {wizardStep === 1 && (
              <div className="space-y-3">
                <h3 className="text-[13px] font-semibold text-ink">Step 2: Select or Create Experiment</h3>
                <p className="text-[10px] text-ink-4">Select existing experiments or create a new one. For comparison, you need at least 2 experiments with results.</p>
                {!wzExportId && <p className="text-[9px] text-caution">Go back to Step 1 and select an export first.</p>}

                {expList.length > 0 && (
                  <div className="space-y-1 max-h-[120px] overflow-y-auto">
                    {expList.slice(0, 10).map(exp => (
                      <button key={exp.experiment_id} onClick={() => { setWzExpIds(prev => prev.includes(exp.experiment_id) ? prev.filter(id => id !== exp.experiment_id) : [...prev, exp.experiment_id]); setWzError(null); }}
                        className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                          wzExpIds.includes(exp.experiment_id) ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                        }`}>
                        <span className="font-mono text-ink-2">{exp.experiment_id?.slice(0, 8)}</span>
                        <span className="text-ink font-medium truncate max-w-[120px]">{exp.name}</span>
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                          exp.lifecycle_state === "completed" ? "bg-pos/10 text-pos" : "bg-surface-3 text-ink-4"
                        }`}>{exp.lifecycle_state}</span>
                        {exp.result_summary && <span className="text-ink-4">has results</span>}
                      </button>
                    ))}
                  </div>
                )}

                {/* Create experiment */}
                {wzExportId && (
                  <details className="border border-line/30 rounded-md">
                    <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">Create new experiment (export {wzExportId.slice(0, 8)})</summary>
                    <div className="p-2 space-y-2">
                      <input type="text" value={wzExpName} onChange={e => setWzExpName(e.target.value)} placeholder="Experiment name"
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <input type="text" value={wzExpHyp} onChange={e => setWzExpHyp(e.target.value)} placeholder="Hypothesis (optional)"
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                        <input type="checkbox" checked={wzExpAck} onChange={e => setWzExpAck(e.target.checked)} className="rounded" />
                        Research-only offline experiment (required)
                      </label>
                      <button disabled={wzLoading || !wzExpAck || !wzExpName.trim()} onClick={async () => {
                        setWzLoading(true); setWzError(null); setWzSuccess(null);
                        try {
                          const res = await createFinrlxResearchExperiment({ name: wzExpName.trim(), linked_export_id: wzExportId, hypothesis: wzExpHyp, research_acknowledgement: true });
                          if (res.data?.experiment_id) { setWzExpIds(prev => [...prev, res.data.experiment_id]); setWzSuccess(`Experiment ${res.data.experiment_id.slice(0, 8)} created.`); setWzExpAck(false); refreshExperiments(); }
                        } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Failed"); } finally { setWzLoading(false); }
                      }} className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40">
                        {wzLoading ? "Creating..." : "Create Experiment"}
                      </button>
                    </div>
                  </details>
                )}

                {/* Import results */}
                {wzExpIds.length > 0 && (
                  <details className="border border-line/30 rounded-md">
                    <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">Import metadata-only results</summary>
                    <div className="p-2 space-y-2">
                      <p className="text-[9px] text-ink-4">Metadata-only — no files, no code, no production influence.</p>
                      <select value={wzResExpId} onChange={e => setWzResExpId(e.target.value)}
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink font-mono focus:border-primary focus:outline-none">
                        <option value="">Select experiment</option>
                        {wzExpIds.map(id => <option key={id} value={id}>{id.slice(0, 16)}</option>)}
                      </select>
                      <input type="text" value={wzResSum} onChange={e => setWzResSum(e.target.value)} placeholder="Result summary"
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <textarea value={wzResMetrics} onChange={e => setWzResMetrics(e.target.value)} rows={2} placeholder='{"sharpe_ratio": 1.2, "max_drawdown": -0.05}'
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink font-mono focus:border-primary focus:outline-none resize-y" />
                      <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                        <input type="checkbox" checked={wzResAck} onChange={e => setWzResAck(e.target.checked)} className="rounded" />
                        Metadata-only offline result import (required)
                      </label>
                      <button disabled={wzLoading || !wzResAck || !wzResExpId} onClick={async () => {
                        setWzLoading(true); setWzError(null); setWzSuccess(null);
                        let metrics: Record<string, number | string> = {};
                        try { metrics = JSON.parse(wzResMetrics); } catch { setWzError("Invalid JSON in result metrics."); setWzLoading(false); return; }
                        try {
                          const res = await importFinrlxResearchExperimentResults(wzResExpId, { acknowledgement: true, result_summary: wzResSum, result_metrics: metrics });
                          if (res.data) { setWzSuccess("Results imported (metadata-only)."); setWzResAck(false); refreshExperiments(); }
                        } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Import failed"); } finally { setWzLoading(false); }
                      }} className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40">
                        {wzLoading ? "Importing..." : "Import Results"}
                      </button>
                    </div>
                  </details>
                )}

                {/* Verify + Expert link */}
                <div className="flex flex-wrap items-center gap-2">
                  {wzExpIds.length === 1 && (
                    <button disabled={wzLoading} onClick={async () => {
                      setWzLoading(true); setWzVerifyResult(null); setWzError(null);
                      try {
                        const res = await verifyFinrlxResearchExperiment(wzExpIds[0]);
                        setWzVerifyResult(res.data as unknown as Record<string, unknown>);
                      } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Verify failed"); } finally { setWzLoading(false); }
                    }} className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40">
                      Verify experiment
                    </button>
                  )}
                  <button onClick={() => { setWizardOpen(false); setAdminTab("experiments"); }} className="text-[10px] text-primary hover:underline">Open in Expert Tab →</button>
                </div>
                {wzVerifyResult && wizardStep === 1 && (
                  <div className="p-2 rounded-md bg-surface-3 text-[9px]">
                    Status: <span className={(wzVerifyResult as Record<string, unknown>).healthy ? "text-pos" : "text-caution"}>{(wzVerifyResult as Record<string, unknown>).healthy ? "healthy" : "warnings"}</span>
                    {Array.isArray((wzVerifyResult as Record<string, unknown>).warnings) && ((wzVerifyResult as Record<string, unknown>).warnings as string[]).length > 0 && (
                      <span className="text-caution ml-1">{((wzVerifyResult as Record<string, unknown>).warnings as string[]).join("; ")}</span>
                    )}
                  </div>
                )}

                {wzExpIds.length > 0 && <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">Selected: {wzExpIds.length} experiment{wzExpIds.length !== 1 ? "s" : ""} ({wzExpIds.map(id => id.slice(0, 8)).join(", ")})</div>}
                {wzExpIds.length === 1 && <p className="text-[9px] text-caution">Need at least 2 experiments for comparison in the next step.</p>}
              </div>
            )}

            {/* ═══ Step 3: Comparison ═══ */}
            {wizardStep === 2 && (
              <div className="space-y-3">
                <h3 className="text-[13px] font-semibold text-ink">Step 3: Create or Select Comparison</h3>
                <p className="text-[10px] text-ink-4">Compare experiments using imported result metadata. Numeric metric sorting only — does not imply production suitability.</p>

                {cmpList.length > 0 && (
                  <div className="space-y-1 max-h-[120px] overflow-y-auto">
                    {cmpList.slice(0, 8).map(cmp => (
                      <button key={cmp.comparison_id} onClick={() => { setWzCmpId(cmp.comparison_id); setWzSuccess(`Selected comparison ${cmp.comparison_id.slice(0, 8)}`); setWzError(null); setWzVerifyResult(null); }}
                        className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                          wzCmpId === cmp.comparison_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                        }`}>
                        <span className="font-mono text-ink-2">{cmp.comparison_id?.slice(0, 8)}</span>
                        <span className="text-ink font-medium truncate max-w-[120px]">{cmp.name}</span>
                        <span className="text-ink-3">{cmp.experiment_ids?.length} exp</span>
                        <span className="text-ink-4">{cmp.comparison_summary?.metric_names?.length || 0} metrics</span>
                        {(cmp.warnings?.length || 0) > 0 && <span className="text-caution">{cmp.warnings?.length} warn</span>}
                      </button>
                    ))}
                  </div>
                )}

                {wzExpIds.length >= 2 && (
                  <details className="border border-line/30 rounded-md" open={!wzCmpId}>
                    <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">Create comparison from {wzExpIds.length} experiments</summary>
                    <div className="p-2 space-y-2">
                      <input type="text" value={wzCmpName} onChange={e => setWzCmpName(e.target.value)} placeholder="Comparison name"
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                        <input type="checkbox" checked={wzCmpAck} onChange={e => setWzCmpAck(e.target.checked)} className="rounded" />
                        Research-only offline comparison (required)
                      </label>
                      <button disabled={wzLoading || !wzCmpAck || !wzCmpName.trim()} onClick={async () => {
                        setWzLoading(true); setWzError(null); setWzSuccess(null);
                        try {
                          const res = await createFinrlxExperimentComparison({ name: wzCmpName.trim(), experiment_ids: wzExpIds, research_acknowledgement: true });
                          if (res.data?.comparison_id) { setWzCmpId(res.data.comparison_id); setWzSuccess(`Comparison ${res.data.comparison_id.slice(0, 8)} created.`); setWzCmpAck(false); refreshComparisons(); }
                        } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Failed"); } finally { setWzLoading(false); }
                      }} className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40">
                        {wzLoading ? "Creating..." : "Create Comparison"}
                      </button>
                    </div>
                  </details>
                )}
                {wzExpIds.length < 2 && <p className="text-[9px] text-caution">Go back to Step 2 and select at least 2 experiments.</p>}

                <div className="flex flex-wrap items-center gap-2">
                  {wzCmpId && (
                    <button disabled={wzLoading} onClick={async () => {
                      setWzLoading(true); setWzVerifyResult(null); setWzError(null);
                      try { const res = await verifyFinrlxExperimentComparison(wzCmpId); setWzVerifyResult(res.data as unknown as Record<string, unknown>); }
                      catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Verify failed"); } finally { setWzLoading(false); }
                    }} className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40">
                      Verify comparison
                    </button>
                  )}
                  <button onClick={() => { setWizardOpen(false); setAdminTab("comparisons"); }} className="text-[10px] text-primary hover:underline">Open in Expert Tab →</button>
                </div>
                {wzVerifyResult && wizardStep === 2 && (
                  <div className="p-2 rounded-md bg-surface-3 text-[9px]">
                    Status: <span className={(wzVerifyResult as Record<string, unknown>).healthy ? "text-pos" : "text-caution"}>{(wzVerifyResult as Record<string, unknown>).healthy ? "healthy" : "warnings"}</span>
                    {Array.isArray((wzVerifyResult as Record<string, unknown>).warnings) && ((wzVerifyResult as Record<string, unknown>).warnings as string[]).length > 0 && (
                      <span className="text-caution ml-1">{((wzVerifyResult as Record<string, unknown>).warnings as string[]).join("; ")}</span>
                    )}
                  </div>
                )}

                {wzCmpId && <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">Selected: <span className="font-mono">{wzCmpId.slice(0, 16)}</span></div>}
              </div>
            )}

            {/* ═══ Step 4: Readiness Review ═══ */}
            {wizardStep === 3 && (
              <div className="space-y-3">
                <h3 className="text-[13px] font-semibold text-ink">Step 4: Readiness Review</h3>
                <p className="text-[10px] text-ink-4">Assess research evidence completeness. &quot;Research review ready&quot; does not mean production-ready.</p>
                {!wzCmpId && <p className="text-[9px] text-caution">Go back to Step 3 and select or create a comparison first.</p>}

                {rdList.length > 0 && (
                  <div className="space-y-1 max-h-[120px] overflow-y-auto">
                    {rdList.slice(0, 8).map(rv => (
                      <button key={rv.readiness_id} onClick={() => { setWzRdId(rv.readiness_id); setWzSuccess(`Selected readiness ${rv.readiness_id.slice(0, 8)}`); setWzError(null); setWzVerifyResult(null); setWzRdState(rv.readiness_state); }}
                        className={`w-full text-left flex flex-wrap items-center gap-2 text-[10px] py-1.5 px-2 rounded-md border transition-colors ${
                          wzRdId === rv.readiness_id ? "border-primary bg-primary/5" : "border-line/30 hover:bg-surface-2"
                        }`}>
                        <span className="font-mono text-ink-2">{rv.readiness_id?.slice(0, 8)}</span>
                        <span className="text-ink font-medium truncate max-w-[120px]">{rv.name}</span>
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${
                          rv.readiness_state === "research_review_ready" ? "bg-pos/10 text-pos" : rv.readiness_state === "needs_more_evidence" ? "bg-caution/10 text-caution" : "bg-surface-3 text-ink-4"
                        }`}>{rv.readiness_state?.replace(/_/g, " ")}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Create readiness */}
                {wzCmpId && (
                  <details className="border border-line/30 rounded-md" open={!wzRdId}>
                    <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">Create readiness review (comparison {wzCmpId.slice(0, 8)})</summary>
                    <div className="p-2 space-y-2">
                      <input type="text" value={wzRdName} onChange={e => setWzRdName(e.target.value)} placeholder="Review name"
                        className="w-full px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                        <input type="checkbox" checked={wzRdAck} onChange={e => setWzRdAck(e.target.checked)} className="rounded" />
                        Research-only readiness review — does not imply production suitability (required)
                      </label>
                      <button disabled={wzLoading || !wzRdAck || !wzRdName.trim()} onClick={async () => {
                        setWzLoading(true); setWzError(null); setWzSuccess(null);
                        try {
                          const res = await createFinrlxResearchReadiness({ name: wzRdName.trim(), linked_comparison_id: wzCmpId, research_acknowledgement: true });
                          if (res.data?.readiness_id) { setWzRdId(res.data.readiness_id); setWzSuccess(`Readiness ${res.data.readiness_id.slice(0, 8)} created. Suggested: ${res.data.suggested_readiness_state?.replace(/_/g, " ")}`); setWzRdAck(false); refreshReadiness(); }
                        } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Failed"); } finally { setWzLoading(false); }
                      }} className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40">
                        {wzLoading ? "Creating..." : "Create Readiness Review"}
                      </button>
                    </div>
                  </details>
                )}

                {/* State update */}
                {wzRdId && (
                  <details className="border border-line/30 rounded-md">
                    <summary className="text-[10px] text-ink-3 font-medium cursor-pointer px-2 py-1.5 hover:bg-surface-2 rounded-md">Update readiness state</summary>
                    <div className="p-2 space-y-2">
                      <p className="text-[9px] text-ink-4">Research review ready does not mean production-ready.</p>
                      <div className="flex flex-wrap gap-2">
                        <select value={wzRdState} onChange={e => setWzRdState(e.target.value)}
                          className="px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none">
                          <option value="draft">draft</option>
                          <option value="needs_more_evidence">needs more evidence</option>
                          <option value="research_review_ready">research review ready</option>
                          <option value="archived">archived</option>
                        </select>
                        <input type="text" value={wzRdStateReason} onChange={e => setWzRdStateReason(e.target.value)} placeholder="Reason (optional)"
                          className="flex-1 min-w-[100px] px-2 py-1 rounded-md border border-line bg-surface text-[10px] text-ink focus:border-primary focus:outline-none" />
                      </div>
                      <label className="flex items-center gap-1.5 text-[9px] text-ink-2 cursor-pointer">
                        <input type="checkbox" checked={wzRdStateAck} onChange={e => setWzRdStateAck(e.target.checked)} className="rounded" />
                        I acknowledge this state change (research review only)
                      </label>
                      <button disabled={wzLoading || !wzRdStateAck} onClick={async () => {
                        setWzLoading(true); setWzError(null); setWzSuccess(null);
                        try {
                          await updateFinrlxResearchReadinessState(wzRdId, { readiness_state: wzRdState as ReadinessState, acknowledgement: true, reason: wzRdStateReason || undefined });
                          setWzSuccess(`State updated to ${wzRdState.replace(/_/g, " ")}.`); setWzRdStateAck(false); refreshReadiness();
                        } catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Update failed"); } finally { setWzLoading(false); }
                      }} className="px-3 py-1 rounded-md bg-primary text-primary-ink text-[10px] font-medium disabled:opacity-40">
                        {wzLoading ? "Updating..." : "Update State"}
                      </button>
                    </div>
                  </details>
                )}

                {/* Verify + Expert */}
                <div className="flex flex-wrap items-center gap-2">
                  {wzRdId && (
                    <button disabled={wzLoading} onClick={async () => {
                      setWzLoading(true); setWzVerifyResult(null); setWzError(null);
                      try { const res = await verifyFinrlxResearchReadiness(wzRdId); setWzVerifyResult(res.data as unknown as Record<string, unknown>); }
                      catch (e: unknown) { setWzError(e instanceof Error ? e.message : "Verify failed"); } finally { setWzLoading(false); }
                    }} className="px-2 py-1 rounded-md text-[9px] font-medium bg-surface-3 text-ink-2 hover:bg-surface-3/80 disabled:opacity-40">
                      Verify readiness
                    </button>
                  )}
                  <button onClick={() => { setWizardOpen(false); setAdminTab("readiness"); }} className="text-[10px] text-primary hover:underline">Open in Expert Tab →</button>
                </div>
                {wzVerifyResult && wizardStep === 3 && (
                  <div className="p-2 rounded-md bg-surface-3 text-[9px]">
                    Status: <span className={(wzVerifyResult as Record<string, unknown>).healthy ? "text-pos" : "text-caution"}>{(wzVerifyResult as Record<string, unknown>).healthy ? "healthy" : "warnings"}</span>
                    {Array.isArray((wzVerifyResult as Record<string, unknown>).warnings) && ((wzVerifyResult as Record<string, unknown>).warnings as string[]).length > 0 && (
                      <span className="text-caution ml-1">{((wzVerifyResult as Record<string, unknown>).warnings as string[]).join("; ")}</span>
                    )}
                  </div>
                )}

                {wzRdId && <div className="p-2 rounded-md bg-pos/5 border border-pos/20 text-[10px] text-pos">Selected: <span className="font-mono">{wzRdId.slice(0, 16)}</span></div>}
              </div>
            )}

            {/* Navigation */}
            <div className="flex items-center justify-between pt-3 border-t border-line">
              <button disabled={wizardStep === 0} onClick={() => { setWizardStep(s => s - 1); setWzError(null); setWzSuccess(null); setWzVerifyResult(null); }}
                className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-surface-2 text-ink-3 hover:bg-surface-3 disabled:opacity-30 transition-colors">
                ← Back
              </button>
              <div className="flex items-center gap-1.5">
                {[0, 1, 2, 3].map(i => (
                  <span key={i} className={`w-2 h-2 rounded-full ${wizardStep === i ? "bg-primary" : "bg-surface-3"}`} />
                ))}
              </div>
              {wizardStep < 3 ? (
                <button onClick={() => { setWizardStep(s => s + 1); setWzError(null); setWzSuccess(null); setWzVerifyResult(null); }}
                  className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-primary text-primary-ink hover:opacity-90 transition-opacity">
                  Next →
                </button>
              ) : (
                <button onClick={() => setWizardOpen(false)}
                  className="px-3 py-1.5 rounded-md text-[11px] font-medium bg-pos text-white hover:opacity-90 transition-opacity">
                  Done
                </button>
              )}
            </div>

            {/* Safety disclaimer */}
            <div className="flex flex-wrap gap-1.5 pt-2 border-t border-line/30">
              {["research-only", "offline-only", "no production influence", "not eligible for promotion"].map(flag => (
                <span key={flag} className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-pos/10 text-pos">{flag}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Incident drawer */}
      {drawerIncident && (
        <IncidentDrawer incident={drawerIncident} onClose={() => setDrawerIncident(null)} />
      )}
    </div>
  );
}
