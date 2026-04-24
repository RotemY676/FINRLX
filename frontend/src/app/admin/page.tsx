"use client";

import { useEffect, useState } from "react";
import { fetchOps, OpsData } from "@/services/api";
import { Icon } from "@/components/icons/Icon";
import { StatusBadge } from "@/components/recommendation/StatusBadge";
import { PageLoading } from "@/components/feedback/PageLoading";
import { PageError } from "@/components/feedback/PageError";

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

export default function AdminPage() {
  const [ops, setOps] = useState<OpsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOps()
      .then((res) => setOps(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <PageLoading label="Loading Ops Command Center..." />;
  if (error) return <PageError title="Ops Error" message={error} hint="Ensure the backend is running and seeded." />;
  if (!ops) return null;

  return (
    <div className="space-y-gap max-w-[1400px]">
      <div>
        <h1 className="text-[20px] font-semibold text-ink">Ops Command Center</h1>
        <p className="text-[12px] text-ink-3 mt-0.5">
          {ops.queue.length} queued · {ops.breaches.filter(b => b.severity === "breach").length} breaches · {ops.incidents.length} incidents
        </p>
      </div>

      {/* ── Publication Queue ── */}
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Icon name="decision" size={15} className="text-primary" />
          <h3 className="text-[13px] font-semibold text-ink">Publication Queue</h3>
          <span className="text-[11px] text-ink-4 ml-auto">{ops.queue.length} pending</span>
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
                <th className="text-left py-2 font-medium">Priority</th>
              </tr>
            </thead>
            <tbody>
              {ops.queue.map((q) => (
                <tr key={q.recommendation_id} className="border-b border-line/50 hover:bg-surface-3 transition-colors">
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
                  <td className={`py-2 text-[11px] font-medium ${PRIORITY_STYLE[q.priority] || ""}`}>{q.priority}</td>
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
              <div key={inc.id} className="border border-line/50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[11px] text-ink-4">{inc.id}</span>
                  <span className={`text-[11px] ${SEVERITY_STYLE[inc.severity] || ""}`}>{inc.severity}</span>
                  <StatusBadge status={inc.status === "investigating" ? "provisional" : inc.status === "monitoring" ? "staged" : "published"} />
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
          </div>
          <div className="space-y-1.5">
            {ops.audit.map((a, i) => (
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
    </div>
  );
}
