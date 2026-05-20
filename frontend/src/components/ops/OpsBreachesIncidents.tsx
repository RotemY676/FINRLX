import { OpsBreach, OpsIncident } from "@/services/api";

const SEVERITY_STYLE: Record<string, string> = {
  breach: "bg-breach-soft text-breach-soft-ink",
  high: "bg-breach-soft text-breach-soft-ink",
  mid: "bg-caution-soft text-caution-soft-ink",
};

export function OpsBreachesIncidents({
  breaches,
  incidents,
}: {
  breaches: OpsBreach[];
  incidents: OpsIncident[];
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-baseline justify-between mb-3">
          <h3 className="text-[13px] font-semibold text-ink">Policy breaches</h3>
          <span className="text-[11px] text-ink-4">{breaches.length} active</span>
        </div>
        {breaches.length === 0 ? (
          <p className="text-[12.5px] text-ink-3">No active breaches.</p>
        ) : (
          <ul className="space-y-2" role="list">
            {breaches.map((b, i) => (
              <li key={i} className="flex flex-col md:flex-row md:items-center md:justify-between gap-1 md:gap-2 text-[12.5px]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${SEVERITY_STYLE[b.severity] ?? SEVERITY_STYLE.mid}`}>
                    {b.severity}
                  </span>
                  <span className="text-ink-2 truncate">{b.label}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0 text-[11px] text-ink-4">
                  <span className="font-mono">{(b.utilization * 100).toFixed(0)}%</span>
                  <span>·</span>
                  <span>{b.trend}</span>
                  {b.related && <span className="font-mono text-ink-3">· {b.related}</span>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <div className="flex items-baseline justify-between mb-3">
          <h3 className="text-[13px] font-semibold text-ink">Open incidents</h3>
          <span className="text-[11px] text-ink-4">{incidents.length} open</span>
        </div>
        {incidents.length === 0 ? (
          <p className="text-[12.5px] text-ink-3">No open incidents.</p>
        ) : (
          <ul className="space-y-2" role="list">
            {incidents.map((inc) => (
              <li key={inc.id} className="text-[12.5px]">
                <div className="flex items-center flex-wrap gap-2">
                  <span className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${SEVERITY_STYLE[inc.severity] ?? SEVERITY_STYLE.mid}`}>
                    {inc.severity}
                  </span>
                  <span className="text-ink-2 font-medium">{inc.title}</span>
                  <span className="text-[11px] text-ink-4">· {inc.started}</span>
                </div>
                <p className="text-[11px] text-ink-3 mt-0.5">
                  owner {inc.owner} · status {inc.status} · {inc.affected_recs} affected
                </p>
                {inc.note && <p className="text-[11px] text-ink-4 mt-0.5">{inc.note}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
