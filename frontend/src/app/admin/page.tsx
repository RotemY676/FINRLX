"use client";

import { useEffect, useState, useCallback } from "react";
import {
  fetchOps, fetchOpsQueue, fetchOpsAudit,
  approveQueueItem, deferQueueItem, challengeQueueItem,
  fetchMLOpsSummary,
  OpsData, OpsQueueItem, OpsAuditEntry, OpsIncident, MLOpsSummary,
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

  useEffect(() => {
    Promise.all([fetchOps(), fetchMLOpsSummary().catch(() => null)])
      .then(([opsRes, mlRes]) => {
        setOps(opsRes.data);
        setFilteredQueue(opsRes.data.queue);
        setFilteredAudit(opsRes.data.audit);
        if (mlRes) setMlSummary(mlRes.data);
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
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_environments}</p>
              <p className="text-[10px] text-ink-4">environments</p>
            </div>
            <div>
              <p className="text-[14px] font-semibold text-ink font-mono">{ops.rl.total_runs}</p>
              <p className="text-[10px] text-ink-4">simulation runs</p>
            </div>
            <div>
              <p className="text-[14px] font-semibold text-ink">{ops.rl.latest_run_status || "—"}</p>
              <p className="text-[10px] text-ink-4">latest status</p>
            </div>
            <div>
              <p className="text-[14px] font-semibold text-ink">{ops.rl.latest_agent_type?.replace(/_/g, " ") || "—"}</p>
              <p className="text-[10px] text-ink-4">agent type</p>
            </div>
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
