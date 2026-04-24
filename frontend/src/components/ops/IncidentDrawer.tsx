"use client";

import { Icon } from "@/components/icons/Icon";
import { OpsIncident } from "@/services/api";

const SEVERITY_BG: Record<string, string> = {
  "sev-1": "bg-breach text-white",
  "sev-2": "bg-caution text-white",
  "sev-3": "bg-surface-3 text-ink-2",
  "sev-4": "bg-surface-3 text-ink-3",
};

// Illustrative timeline events (in production, these would come from the API)
const TIMELINE = [
  { time: "14m ago", dot: "bg-caution", text: "Latency spike detected on options flow ingest — 14m lag vs 200ms SLO" },
  { time: "13m ago", dot: "bg-caution", text: "Auto down-weight triggered: Flow/options engine confidence capped at 0.49" },
  { time: "12m ago", dot: "bg-breach", text: "Incident INC-003 opened automatically — sev-2" },
  { time: "10m ago", dot: "bg-pos", text: "M. Alvarez acknowledged — investigating vendor feed" },
  { time: "5m ago", dot: "bg-pos", text: "Partial recovery: lag dropped to 8m, still above SLO" },
];

const AFFECTED_RECS = [
  { rec: "REC-NVDA-L", impact: "Flow −0.14", capped: "0.74 → 0.68", status: "monitoring" },
  { rec: "REC-XOM-S", impact: "Flow −0.09", capped: "0.68 → 0.63", status: "re-scoring" },
  { rec: "REC-MSFT-T", impact: "Flow −0.05", capped: "0.62 → 0.59", status: "monitoring" },
];

interface IncidentDrawerProps {
  incident: OpsIncident;
  onClose: () => void;
}

export function IncidentDrawer({ incident, onClose }: IncidentDrawerProps) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-md bg-surface border-l border-line shadow-lg overflow-y-auto">
        {/* Header */}
        <div className="p-pad border-b border-line">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${SEVERITY_BG[incident.severity] || "bg-surface-3 text-ink-3"}`}>
              {incident.severity}
            </span>
            <span className="font-mono text-[11px] text-ink-4">{incident.id}</span>
            <button
              onClick={onClose}
              className="ml-auto p-1 rounded-md hover:bg-surface-3 text-ink-3 transition-colors"
            >
              <Icon name="close" size={16} />
            </button>
          </div>
          <h2 className="text-[18px] font-display font-semibold text-ink">{incident.title}</h2>
          <p className="text-[12px] text-ink-3 mt-1">
            Started {incident.started} · Owner: {incident.owner} · {incident.status}
          </p>
        </div>

        {/* Impact */}
        <div className="p-pad border-b border-line">
          <h4 className="text-[12px] font-semibold text-ink mb-2 uppercase tracking-wider">Impact</h4>
          <p className="text-[12.5px] text-ink-2">{incident.note}</p>
          {incident.affected_recs > 0 && (
            <p className="text-[12px] text-caution mt-1">{incident.affected_recs} recommendations affected</p>
          )}
        </div>

        {/* Timeline */}
        <div className="p-pad border-b border-line">
          <h4 className="text-[12px] font-semibold text-ink mb-3 uppercase tracking-wider">Timeline</h4>
          <div className="space-y-3 relative">
            {/* Vertical line */}
            <div className="absolute left-[5px] top-2 bottom-2 w-px bg-line" />
            {TIMELINE.map((ev, i) => (
              <div key={i} className="flex items-start gap-3 relative">
                <span className={`w-[11px] h-[11px] rounded-full shrink-0 mt-0.5 z-10 ${ev.dot}`} />
                <div>
                  <span className="text-[10px] text-ink-4 font-mono">{ev.time}</span>
                  <p className="text-[12px] text-ink-2">{ev.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Affected recommendations */}
        <div className="p-pad border-b border-line">
          <h4 className="text-[12px] font-semibold text-ink mb-3 uppercase tracking-wider">Affected recommendations</h4>
          <div className="space-y-2">
            {AFFECTED_RECS.map((r) => (
              <div key={r.rec} className="flex items-center gap-3 text-[12px]">
                <span className="font-mono text-ink w-24 shrink-0">{r.rec}</span>
                <span className="text-breach font-mono">{r.impact}</span>
                <span className="text-ink-3 font-mono">{r.capped}</span>
                <span className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  r.status === "re-scoring" ? "bg-caution-soft text-caution-soft-ink" : "bg-surface-3 text-ink-3"
                }`}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="p-pad">
          <h4 className="text-[12px] font-semibold text-ink mb-3 uppercase tracking-wider">Actions</h4>
          <div className="flex items-center gap-2 flex-wrap">
            <button className="px-3 py-1.5 rounded-md bg-surface-3 text-ink-2 text-[12px] font-medium hover:bg-line transition-colors">
              Open runbook
            </button>
            <button className="px-3 py-1.5 rounded-md bg-surface-3 text-ink-2 text-[12px] font-medium hover:bg-line transition-colors">
              Page on-call
            </button>
            <button className="px-3 py-1.5 rounded-md bg-surface-3 text-ink-2 text-[12px] font-medium hover:bg-line transition-colors">
              Snooze 15m
            </button>
            <button className="px-3 py-1.5 rounded-md bg-primary text-primary-ink text-[12px] font-medium hover:opacity-90 transition-opacity">
              Mark resolved
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
