import { TimingView } from "@/services/api";
import { StageCard } from "./StageCard";

const URGENCY_COLORS: Record<string, string> = {
  immediate: "text-qp-red-600 bg-qp-red-400/10",
  soon: "text-qp-amber-600 bg-qp-amber-400/10",
  wait: "text-qp-blue-600 bg-qp-blue-50",
  defer: "text-qp-text-muted bg-qp-border/50",
};

export function TimingStage({ data }: { data: TimingView | null }) {
  return (
    <StageCard title="Timing" available={!!data}>
      {data && (
        <div className="space-y-qp-3">
          <div className="flex items-center gap-qp-3">
            {data.urgency && (
              <span className={`px-qp-3 py-qp-1 rounded-qp-sm text-qp-body font-medium ${
                URGENCY_COLORS[data.urgency] || ""
              }`}>
                {data.urgency}
              </span>
            )}
            {data.horizon_days != null && (
              <span className="text-qp-body text-qp-text-secondary">
                {data.horizon_days} day horizon
              </span>
            )}
          </div>
          {data.rationale && (
            <p className="text-qp-body text-qp-text-secondary">{data.rationale}</p>
          )}
        </div>
      )}
    </StageCard>
  );
}
