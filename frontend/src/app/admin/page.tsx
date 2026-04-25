"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchOps, fetchOpsQueue, fetchOpsAudit,
  approveQueueItem, deferQueueItem, challengeQueueItem,
  fetchMLOpsSummary, fetchRLBenchmarks, runRLBenchmark,
  OpsData, OpsQueueItem, OpsAuditEntry, OpsIncident, MLOpsSummary,
  RLBenchmarkReport,
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

  useEffect(() => {
    Promise.all([
      fetchOps(),
      fetchMLOpsSummary().catch(() => null),
      fetchRLBenchmarks().catch(() => null),
    ])
      .then(([opsRes, mlRes, benchRes]) => {
        setOps(opsRes.data);
        setFilteredQueue(opsRes.data.queue);
        setFilteredAudit(opsRes.data.audit);
        if (mlRes) setMlSummary(mlRes.data);
        if (benchRes && benchRes.data) {
          setBenchmarks(benchRes.data);
          if (benchRes.data.length > 0) setSelectedBenchmark(benchRes.data[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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
    <div className="space-y-gap max-w-[1400px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Ops Command Center</h1>
        <p className="text-[12px] text-ink-3 mt-0.5">
          {filteredQueue.length} queued · {ops.breaches.filter(b => b.severity === "breach").length} breaches · {ops.incidents.length} incidents
        </p>
      </div>

      {/* ── KPI Strip ── */}
      {ops.system_kpis.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
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
          <div className="flex items-center gap-2 mb-4">
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
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
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
          <div className="flex items-center gap-2 mb-3">
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
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 text-center">
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

      {/* ── Run Offline Benchmark ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-3">
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
              It will not create live recommendations, execute trades, influence production decisions, or affect publication workflow.
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
                setBenchRunSuccess(`Benchmark ${report.id.slice(0, 8)}... ${report.status} — ${report.executed_agents?.length || 0} agents`);
                // Refresh benchmarks and select the new one
                const refreshed = await fetchRLBenchmarks().catch(() => null);
                if (refreshed && refreshed.data) {
                  setBenchmarks(refreshed.data);
                  setSelectedBenchmark(report);
                }
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
        {benchRunSuccess && (
          <div className="mt-3 rounded-lg border border-pos bg-pos-soft p-3 text-[11px] text-pos-soft-ink">
            <Icon name="check" size={12} className="inline mr-1" />{benchRunSuccess}
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
          <div className="flex items-center gap-2 mb-2">
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
          <div className="flex items-center gap-2 mb-3">
            <Icon name="history" size={15} className="text-accent" />
            <h3 className="text-[13px] font-semibold text-ink">Offline Benchmark History</h3>
            <span className="text-[10px] text-ink-4 ml-auto">{benchmarks.length} report{benchmarks.length !== 1 ? "s" : ""}</span>
          </div>
          <div className="space-y-1">
            {benchmarks.slice(0, 8).map((b) => (
              <div
                key={b.id}
                onClick={() => setSelectedBenchmark(b)}
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
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-4">
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
                  }. Not a live signal.
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

      {/* Benchmark Trend Table */}
      {benchmarks.length > 1 && (
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-3">
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
        <div className="flex items-center gap-2 mb-4">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
        {/* ── Data Feeds ── */}
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-4">
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
          <div className="flex items-center gap-2 mb-4">
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gap">
        {/* Policy Rules */}
        {ops.policy && (
          <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Icon name="risk" size={14} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Policy Rules</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
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
            <div className="flex items-center gap-2 mb-3">
              <Icon name="database" size={14} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Integrations</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
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
            <div className="flex items-center gap-2 mb-3">
              <Icon name="universe" size={14} className="text-ink-3" />
              <h3 className="text-[13px] font-semibold text-ink">Universe</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
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
        <div className="flex items-center gap-2 mb-4">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
        {/* ── Incidents ── */}
        <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
          <div className="flex items-center gap-2 mb-4">
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
          <div className="flex items-center gap-2 mb-4">
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

      {/* Incident drawer */}
      {drawerIncident && (
        <IncidentDrawer incident={drawerIncident} onClose={() => setDrawerIncident(null)} />
      )}
    </div>
  );
}
