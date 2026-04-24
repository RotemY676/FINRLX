import { SelectionRunView } from "@/services/api";
import { StageCard } from "./StageCard";

export function SelectionStage({ data }: { data: SelectionRunView | null }) {
  return (
    <StageCard title="Selection" subtitle={`${data?.included.length ?? 0} included`} available={!!data}>
      {data && (
        <div className="space-y-qp-3">
          {data.rationale && (
            <p className="text-qp-body text-qp-text-secondary">{data.rationale}</p>
          )}
          <div className="flex flex-wrap gap-qp-1">
            {data.included.map((a) => (
              <span key={a.asset_id} className="px-qp-2 py-0.5 bg-qp-green-400/10 text-qp-green-600 rounded-qp-sm text-qp-small font-mono">
                {a.ticker}
              </span>
            ))}
          </div>
          {data.excluded.length > 0 && (
            <div>
              <p className="text-qp-small text-qp-text-muted mb-qp-1">Excluded:</p>
              <div className="flex flex-wrap gap-qp-1">
                {data.excluded.map((a) => (
                  <span key={a.asset_id} className="px-qp-2 py-0.5 bg-qp-red-400/10 text-qp-red-600 rounded-qp-sm text-qp-small font-mono">
                    {a.ticker}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </StageCard>
  );
}
