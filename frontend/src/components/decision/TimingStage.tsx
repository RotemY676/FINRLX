import { TimingView } from "@/services/api";
import { StageCard } from "./StageCard";

const U_STYLE: Record<string, string> = {
  immediate: "text-breach bg-breach-soft",
  soon: "text-caution-soft-ink bg-caution-soft",
  wait: "text-primary-soft-ink bg-primary-soft",
  defer: "text-ink-3 bg-surface-3",
};

export function TimingStage({ data }: { data: TimingView | null }) {
  return (
    <StageCard title="Timing" available={!!data}>
      {data && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            {data.urgency && (
              <span className={`px-2.5 py-1 rounded-md text-[12.5px] font-medium ${U_STYLE[data.urgency] || ""}`}>{data.urgency}</span>
            )}
            {data.horizon_days != null && <span className="text-[12.5px] text-ink-2">{data.horizon_days} day horizon</span>}
          </div>
          {data.rationale && <p className="text-[12.5px] text-ink-2">{data.rationale}</p>}
        </div>
      )}
    </StageCard>
  );
}
