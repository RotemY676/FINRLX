"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import {
  fetchOps, fetchOpsQueue, fetchOpsAudit,
  approveQueueItem, deferQueueItem, challengeQueueItem,
  fetchMLOpsSummary, fetchRLBenchmarks, fetchRLBenchmark,
  fetchRLBenchmarkAudit, fetchRLBenchmarkAuditForReport,
  fetchFinRLXStatus, fetchFinRLXDependencies,
  fetchFinRLXCandidates,
  listFinrlxDatasetExports, listFinrlxResearchExperiments,
  listFinrlxExperimentComparisons, listFinrlxResearchReadiness,
  OpsData, OpsQueueItem, OpsAuditEntry, OpsIncident, MLOpsSummary,
  FinRLXDependencyStatus, FinRLXCandidate,
  DatasetExportRegistryEntry,
  ResearchExperiment, ExperimentComparison, ReadinessReview,
  RLBenchmarkReport, RLBenchmarkAuditEvent, FinRLXAdapterStatus,
} from "@/services/api";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface PipelineIds {
  exportId: string;
  experimentIds: string[];
  comparisonId: string;
  readinessId: string;
}

export interface AdminContextValue {
  /* core ops */
  ops: OpsData | null;
  mlSummary: MLOpsSummary | null;
  finrlxStatus: FinRLXAdapterStatus | null;
  finrlxDeps: FinRLXDependencyStatus | null;

  /* pipeline stepper */
  activeStep: number;
  setActiveStep: (step: number) => void;
  pipelineIds: PipelineIds;
  setPipelineId: <K extends keyof PipelineIds>(key: K, value: PipelineIds[K]) => void;

  /* benchmarks */
  benchmarks: RLBenchmarkReport[];
  selectedBenchmark: RLBenchmarkReport | null;
  selectBenchmark: (b: RLBenchmarkReport) => Promise<void>;
  selectedBenchAudit: RLBenchmarkAuditEvent[];
  benchAuditEvents: RLBenchmarkAuditEvent[];

  /* imported candidates */
  importedCandidates: FinRLXCandidate[];

  /* registry lists */
  dsExportHistory: DatasetExportRegistryEntry[];
  expList: ResearchExperiment[];
  cmpList: ExperimentComparison[];
  rdList: ReadinessReview[];

  /* refresh helpers */
  refreshExportHistory: () => void;
  refreshExperiments: () => void;
  refreshComparisons: () => void;
  refreshReadiness: () => void;

  /* queue state */
  filteredQueue: OpsQueueItem[];
  filteredAudit: OpsAuditEntry[];
  queueFilter: string;
  auditScope: string;
  actionLoading: string | null;

  /* queue actions */
  handleQueueFilter: (filter: string) => Promise<void>;
  handleAuditScope: (scope: string) => Promise<void>;
  handleQueueAction: (id: string, action: "approve" | "defer" | "challenge") => Promise<void>;

  /* incident drawer */
  drawerIncident: OpsIncident | null;
  setDrawerIncident: (incident: OpsIncident | null) => void;

  /* status */
  loading: boolean;
  error: string | null;
}

/* ------------------------------------------------------------------ */
/*  Context                                                            */
/* ------------------------------------------------------------------ */

const AdminContext = createContext<AdminContextValue | null>(null);

/* ------------------------------------------------------------------ */
/*  Provider                                                           */
/* ------------------------------------------------------------------ */

export function AdminProvider({ children }: { children: ReactNode }) {
  /* ── core ops ── */
  const [ops, setOps] = useState<OpsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /* ── ML / FinRLX status ── */
  const [mlSummary, setMlSummary] = useState<MLOpsSummary | null>(null);
  const [finrlxStatus, setFinrlxStatus] = useState<FinRLXAdapterStatus | null>(null);
  const [finrlxDeps, setFinrlxDeps] = useState<FinRLXDependencyStatus | null>(null);

  /* ── pipeline stepper ── */
  const [activeStep, setActiveStep] = useState(0);
  const [pipelineIds, _setPipelineIds] = useState<PipelineIds>({
    exportId: "",
    experimentIds: [],
    comparisonId: "",
    readinessId: "",
  });

  const setPipelineId = useCallback(
    <K extends keyof PipelineIds>(key: K, value: PipelineIds[K]) => {
      _setPipelineIds((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  /* ── benchmarks ── */
  const [benchmarks, setBenchmarks] = useState<RLBenchmarkReport[]>([]);
  const [selectedBenchmark, setSelectedBenchmark] = useState<RLBenchmarkReport | null>(null);
  const [selectedBenchAudit, setSelectedBenchAudit] = useState<RLBenchmarkAuditEvent[]>([]);
  const [benchAuditEvents, setBenchAuditEvents] = useState<RLBenchmarkAuditEvent[]>([]);

  /* ── imported candidates ── */
  const [importedCandidates, setImportedCandidates] = useState<FinRLXCandidate[]>([]);

  /* ── registry lists ── */
  const [dsExportHistory, setDsExportHistory] = useState<DatasetExportRegistryEntry[]>([]);
  const [expList, setExpList] = useState<ResearchExperiment[]>([]);
  const [cmpList, setCmpList] = useState<ExperimentComparison[]>([]);
  const [rdList, setRdList] = useState<ReadinessReview[]>([]);

  /* ── queue / audit ── */
  const [queueFilter, setQueueFilter] = useState("all");
  const [filteredQueue, setFilteredQueue] = useState<OpsQueueItem[]>([]);
  const [auditScope, setAuditScope] = useState("all");
  const [filteredAudit, setFilteredAudit] = useState<OpsAuditEntry[]>([]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  /* ── incident drawer ── */
  const [drawerIncident, setDrawerIncident] = useState<OpsIncident | null>(null);

  /* ================================================================ */
  /*  Callbacks                                                        */
  /* ================================================================ */

  const selectBenchmark = useCallback(async (b: RLBenchmarkReport) => {
    setSelectedBenchmark(b);
    setSelectedBenchAudit([]);
    try {
      const res = await fetchRLBenchmarkAuditForReport(b.id);
      if (res.data) setSelectedBenchAudit(res.data);
    } catch {
      /* audit unavailable for old benchmarks */
    }
  }, []);

  /* ── refresh helpers ── */

  const refreshExportHistory = useCallback(() => {
    listFinrlxDatasetExports()
      .then((r) => { if (r.data) setDsExportHistory(r.data); })
      .catch(() => {});
  }, []);

  const refreshExperiments = useCallback(() => {
    listFinrlxResearchExperiments()
      .then((r) => { if (r.data) setExpList(r.data); })
      .catch(() => {});
  }, []);

  const refreshComparisons = useCallback(() => {
    listFinrlxExperimentComparisons()
      .then((r) => { if (r.data) setCmpList(r.data); })
      .catch(() => {});
  }, []);

  const refreshReadiness = useCallback(() => {
    listFinrlxResearchReadiness()
      .then((r) => { if (r.data) setRdList(r.data); })
      .catch(() => {});
  }, []);

  /* ── queue actions ── */

  const handleQueueFilter = useCallback(
    async (filter: string) => {
      setQueueFilter(filter);
      try {
        const res = await fetchOpsQueue(filter);
        setFilteredQueue(res.data);
      } catch {
        if (ops) {
          setFilteredQueue(
            filter === "all" ? ops.queue : ops.queue.filter((q) => q.priority === filter),
          );
        }
      }
    },
    [ops],
  );

  const handleAuditScope = useCallback(
    async (scope: string) => {
      setAuditScope(scope);
      try {
        const res = await fetchOpsAudit(scope);
        setFilteredAudit(res.data);
      } catch {
        if (ops) setFilteredAudit(ops.audit);
      }
    },
    [ops],
  );

  const handleQueueAction = useCallback(
    async (id: string, action: "approve" | "defer" | "challenge") => {
      setActionLoading(id);
      try {
        const fn =
          action === "approve"
            ? approveQueueItem
            : action === "defer"
              ? deferQueueItem
              : challengeQueueItem;
        await fn(id);
        const res = await fetchOpsQueue(queueFilter);
        setFilteredQueue(res.data);
        const opsRes = await fetchOps();
        setOps(opsRes.data);
      } catch {
        /* silently fail */
      } finally {
        setActionLoading(null);
      }
    },
    [queueFilter],
  );

  /* ================================================================ */
  /*  Initial data load                                                */
  /* ================================================================ */

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

        /* secondary fetches — non-blocking */
        fetchFinRLXDependencies()
          .then((r) => { if (r.data) setFinrlxDeps(r.data); })
          .catch(() => {});

        fetchFinRLXCandidates()
          .then((r) => {
            if (r.data) setImportedCandidates(r.data.filter((c) => c.imported_from_artifact));
          })
          .catch(() => {});

        listFinrlxDatasetExports()
          .then((r) => { if (r.data) setDsExportHistory(r.data); })
          .catch(() => {});

        listFinrlxResearchExperiments()
          .then((r) => { if (r.data) setExpList(r.data); })
          .catch(() => {});

        listFinrlxExperimentComparisons()
          .then((r) => { if (r.data) setCmpList(r.data); })
          .catch(() => {});

        listFinrlxResearchReadiness()
          .then((r) => { if (r.data) setRdList(r.data); })
          .catch(() => {});
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectBenchmark]);

  /* ================================================================ */
  /*  Context value                                                    */
  /* ================================================================ */

  const value: AdminContextValue = {
    ops,
    mlSummary,
    finrlxStatus,
    finrlxDeps,

    activeStep,
    setActiveStep,
    pipelineIds,
    setPipelineId,

    benchmarks,
    selectedBenchmark,
    selectBenchmark,
    selectedBenchAudit,
    benchAuditEvents,

    importedCandidates,

    dsExportHistory,
    expList,
    cmpList,
    rdList,

    refreshExportHistory,
    refreshExperiments,
    refreshComparisons,
    refreshReadiness,

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

    loading,
    error,
  };

  return <AdminContext.Provider value={value}>{children}</AdminContext.Provider>;
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

export function useAdmin(): AdminContextValue {
  const ctx = useContext(AdminContext);
  if (!ctx) {
    throw new Error("useAdmin must be used within <AdminProvider>");
  }
  return ctx;
}
