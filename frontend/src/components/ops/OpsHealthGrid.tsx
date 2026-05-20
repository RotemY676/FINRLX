import { OpsFeed, OpsEngine } from "@/services/api";

const STATUS_STYLE: Record<string, string> = {
  ok: "bg-pos",
  warn: "bg-caution",
  degraded: "bg-caution",
  stale: "bg-caution",
};

function StatusDot({ status }: { status: string }) {
  return (
    <span
      className={`w-2 h-2 rounded-full ${STATUS_STYLE[status] ?? "bg-breach"} shrink-0`}
      aria-label={status}
    />
  );
}

export function OpsHealthGrid({
  feeds,
  engines,
}: {
  feeds: OpsFeed[];
  engines: OpsEngine[];
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
      {/* Feeds */}
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h3 className="text-[13px] font-semibold text-ink mb-3">Data feeds</h3>
        {feeds.length === 0 ? (
          <p className="text-[12.5px] text-ink-3">No feeds configured.</p>
        ) : (
          <ul className="space-y-2" role="list">
            {feeds.map((f) => (
              <li key={f.name} className="flex items-center gap-3 text-[12.5px]">
                <StatusDot status={f.status} />
                <span className="text-ink-2 flex-1 truncate">{f.name}</span>
                <span className="text-ink-3 font-mono text-[11px] shrink-0">{f.lag}</span>
                <span className="text-ink-4 font-mono text-[11px] shrink-0">{f.coverage}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Engines */}
      <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <h3 className="text-[13px] font-semibold text-ink mb-3">Engines</h3>
        {engines.length === 0 ? (
          <p className="text-[12.5px] text-ink-3">No engines configured.</p>
        ) : (
          <ul className="space-y-2" role="list">
            {engines.map((e) => (
              <li key={e.name} className="flex items-center gap-3 text-[12.5px]">
                <StatusDot status={e.status} />
                <span className="text-ink-2 flex-1 truncate">{e.name}</span>
                <span className="text-ink-3 font-mono text-[11px] shrink-0">{e.latency}</span>
                <span
                  className={`font-mono text-[11px] shrink-0 ${
                    Math.abs(e.drift) > 0.05 ? "text-caution" : "text-ink-4"
                  }`}
                >
                  drift {(e.drift * 100).toFixed(1)}%
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
