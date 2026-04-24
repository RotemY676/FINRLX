import { AllocationView } from "@/services/api";
import { StageCard } from "./StageCard";

export function AllocationStage({ data }: { data: AllocationView | null }) {
  return (
    <StageCard title="Allocation" subtitle={data?.method ?? undefined} available={!!data}>
      {data && (
        <div className="space-y-3">
          {data.rationale && <p className="text-[12.5px] text-ink-2">{data.rationale}</p>}
          <div className="space-y-1">
            {data.entries.sort((a, b) => b.weight - a.weight).map((e) => (
              <div key={e.asset_id} className="flex items-center gap-2">
                <span className="text-[11px] font-mono w-10 text-ink-2">{e.ticker}</span>
                <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(e.weight * 500, 100)}%` }} />
                </div>
                <span className="text-[11px] font-mono w-8 text-right text-ink-2">{(e.weight * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </StageCard>
  );
}
