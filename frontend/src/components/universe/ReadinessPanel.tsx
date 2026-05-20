import { UniverseReadiness } from "@/services/api";

export function ReadinessPanel({ readiness }: { readiness: UniverseReadiness }) {
  const ready = readiness.readiness_status === "ready";
  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[13px] font-semibold text-ink">Readiness</h3>
        <span
          className={`text-[11px] font-medium px-2 py-0.5 rounded-md ${
            ready ? "bg-pos-soft text-pos-soft-ink" : "bg-caution-soft text-caution-soft-ink"
          }`}
        >
          {ready ? "Ready" : "Incomplete"}
        </span>
      </div>
      {readiness.warnings.length === 0 ? (
        <p className="text-[12.5px] text-ink-3">All coverage thresholds met.</p>
      ) : (
        <ul className="space-y-1">
          {readiness.warnings.map((w, i) => (
            <li key={i} className="text-[12px] text-caution-soft-ink flex items-start gap-2">
              <span aria-hidden="true">•</span>
              <span>{w}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
