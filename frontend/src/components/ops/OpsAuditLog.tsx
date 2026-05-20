import { OpsAuditEntry } from "@/services/api";
import { Icon } from "@/components/icons/Icon";

export function OpsAuditLog({ entries }: { entries: OpsAuditEntry[] }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-[13px] font-semibold text-ink">Audit trail</h3>
        <span className="text-[11px] text-ink-4">{entries.length} recent</span>
      </div>
      {entries.length === 0 ? (
        <p className="text-[12.5px] text-ink-3">No audit entries yet.</p>
      ) : (
        <ul className="space-y-1.5" role="list">
          {entries.map((e, i) => (
            <li key={i} className="flex items-start gap-2 text-[12px]">
              <span aria-hidden="true" className={`mt-1 ${e.ok ? "text-pos" : "text-breach"}`}>
                <Icon name={e.ok ? "check" : "alert-triangle"} size={11} />
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-ink-2">
                  <b className="text-ink">{e.actor}</b> {e.action}{" "}
                  <span className="text-ink-3">{e.target}</span>
                </p>
                <p className="text-[11px] text-ink-4">
                  {e.when} · {e.scope}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
