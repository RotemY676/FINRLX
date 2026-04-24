import { HealthSummary } from "@/services/api";

function HealthDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${
        ok ? "bg-qp-green-500" : "bg-qp-red-500"
      }`}
    />
  );
}

export function HealthPanel({ health }: { health: HealthSummary }) {
  const items = [
    { label: "Source Freshness", ok: health.source_freshness_ok },
    { label: "Feature Health", ok: health.feature_health_ok },
    { label: "Model Health", ok: health.model_health_ok },
    { label: "Publication Health", ok: health.publication_health_ok },
  ];

  return (
    <div className="bg-qp-bg-card border border-qp-border rounded-qp p-qp-6">
      <h3 className="text-qp-h3 mb-qp-4">System Health</h3>
      <div className="space-y-qp-2">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between text-qp-body"
          >
            <span className="text-qp-text-secondary">{item.label}</span>
            <div className="flex items-center gap-qp-2">
              <HealthDot ok={item.ok} />
              <span className={item.ok ? "text-qp-green-600" : "text-qp-red-600"}>
                {item.ok ? "OK" : "Issue"}
              </span>
            </div>
          </div>
        ))}
      </div>
      {health.open_incidents > 0 && (
        <p className="mt-qp-3 text-qp-small text-qp-amber-600">
          {health.open_incidents} open incident{health.open_incidents > 1 ? "s" : ""}
        </p>
      )}
    </div>
  );
}
