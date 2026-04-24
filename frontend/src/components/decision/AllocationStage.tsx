import { AllocationView } from "@/services/api";
import { StageCard } from "./StageCard";

export function AllocationStage({ data }: { data: AllocationView | null }) {
  return (
    <StageCard title="Allocation" subtitle={data?.method ?? undefined} available={!!data}>
      {data && (
        <div className="space-y-qp-3">
          {data.rationale && (
            <p className="text-qp-body text-qp-text-secondary">{data.rationale}</p>
          )}
          <div className="space-y-qp-1">
            {data.entries
              .sort((a, b) => b.weight - a.weight)
              .map((e) => (
                <div key={e.asset_id} className="flex items-center gap-qp-2">
                  <span className="text-qp-small font-mono w-12">{e.ticker}</span>
                  <div className="flex-1 h-1.5 bg-qp-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-qp-blue-400 rounded-full"
                      style={{ width: `${Math.min(e.weight * 500, 100)}%` }}
                    />
                  </div>
                  <span className="text-qp-small font-mono w-10 text-right">
                    {(e.weight * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </StageCard>
  );
}
