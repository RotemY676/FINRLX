import { SelectionRunView } from "@/services/api";
import { StageCard } from "./StageCard";

export function SelectionStage({ data }: { data: SelectionRunView | null }) {
  return (
    <StageCard title="Selection" subtitle={`${data?.included.length ?? 0} included`} available={!!data}>
      {data && (
        <div className="space-y-3">
          {data.rationale && <p className="text-[12.5px] text-ink-2">{data.rationale}</p>}
          <div className="flex flex-wrap gap-1">
            {data.included.map((a) => (
              <span key={a.asset_id} className="px-2 py-0.5 bg-pos-soft text-pos-soft-ink rounded-md text-[11px] font-mono">{a.ticker}</span>
            ))}
          </div>
          {data.excluded.length > 0 && (
            <div>
              <p className="text-[11px] text-ink-4 mb-1">Excluded:</p>
              <div className="flex flex-wrap gap-1">
                {data.excluded.map((a) => (
                  <span key={a.asset_id} className="px-2 py-0.5 bg-breach-soft text-breach-soft-ink rounded-md text-[11px] font-mono">{a.ticker}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </StageCard>
  );
}
