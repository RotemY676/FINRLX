import { RiskOverlayView } from "@/services/api";
import { StageCard } from "./StageCard";

export function RiskOverlayStage({ data }: { data: RiskOverlayView | null }) {
  return (
    <StageCard title="Risk Overlay" subtitle={data?.portfolio_risk_score != null ? `Score: ${(data.portfolio_risk_score * 100).toFixed(0)}` : undefined} available={!!data}>
      {data && (
        <div className="space-y-3">
          {data.rationale && <p className="text-[12.5px] text-ink-2">{data.rationale}</p>}
          {data.adjustments.length > 0 && (
            <div>
              <p className="text-[11px] text-ink-4 mb-1">Adjustments:</p>
              {data.adjustments.map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-[12.5px]">
                  <span className="font-mono w-10 text-ink">{a.ticker}</span>
                  <span className={`font-mono ${a.delta < 0 ? "text-breach" : "text-pos"}`}>{a.delta > 0 ? "+" : ""}{(a.delta * 100).toFixed(1)}%</span>
                  {a.reason && <span className="text-ink-4 text-[11px]">{a.reason}</span>}
                </div>
              ))}
            </div>
          )}
          {data.constraints_applied.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {data.constraints_applied.map((c) => (
                <span key={c} className="px-2 py-0.5 bg-surface-3 rounded-md text-[11px] text-ink-3">{c}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </StageCard>
  );
}
