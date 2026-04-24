import { HealthSummary } from "@/services/api";

const TONE: Record<string, string> = {
  ok: "text-pos",
  issue: "text-breach",
};

export function HealthPanel({ health }: { health: HealthSummary }) {
  const items = [
    { label: "Source Freshness", ok: health.source_freshness_ok },
    { label: "Feature Health", ok: health.feature_health_ok },
    { label: "Model Health", ok: health.model_health_ok },
    { label: "Publication Health", ok: health.publication_health_ok },
  ];

  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <h3 className="text-[13px] font-semibold text-ink mb-3">System Health</h3>
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.label} className="flex items-center justify-between text-[12.5px]">
            <span className="text-ink-2">{item.label}</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${item.ok ? "bg-pos" : "bg-breach"}`} />
              <span className={item.ok ? TONE.ok : TONE.issue}>{item.ok ? "OK" : "Issue"}</span>
            </div>
          </div>
        ))}
      </div>
      {health.open_incidents > 0 && (
        <p className="mt-2 text-[11px] text-caution">{health.open_incidents} open incident{health.open_incidents > 1 ? "s" : ""}</p>
      )}
    </div>
  );
}
