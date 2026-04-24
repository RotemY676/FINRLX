import { ConfidenceTriplet } from "@/services/api";

function ConfidenceBar({
  label,
  value,
}: {
  label: string;
  value: number | null;
}) {
  const pct = value != null ? Math.round(value * 100) : null;
  const color =
    pct == null
      ? "bg-qp-border"
      : pct >= 80
        ? "bg-qp-green-500"
        : pct >= 60
          ? "bg-qp-amber-500"
          : "bg-qp-red-500";

  return (
    <div className="flex items-center gap-qp-3">
      <span className="text-qp-small text-qp-text-secondary w-24 shrink-0">
        {label}
      </span>
      <div className="flex-1 h-2 bg-qp-border rounded-full overflow-hidden">
        {pct != null && (
          <div
            className={`h-full rounded-full ${color}`}
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
      <span className="text-qp-small font-mono text-qp-text-primary w-10 text-right">
        {pct != null ? `${pct}%` : "n/a"}
      </span>
    </div>
  );
}

export function ConfidenceBlock({
  confidence,
}: {
  confidence: ConfidenceTriplet;
}) {
  return (
    <div className="space-y-qp-2">
      <h3 className="text-qp-h3 mb-qp-3">Trust Decomposition</h3>
      <ConfidenceBar label="Model" value={confidence.model_confidence} />
      <ConfidenceBar label="Data" value={confidence.data_confidence} />
      <ConfidenceBar label="Operational" value={confidence.operational_confidence} />
    </div>
  );
}
