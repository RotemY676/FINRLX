import { RiskOverlayView } from "@/services/api";
import { StageCard } from "./StageCard";

export function RiskOverlayStage({ data }: { data: RiskOverlayView | null }) {
  return (
    <StageCard
      title="Risk Overlay"
      subtitle={data?.portfolio_risk_score != null ? `Score: ${(data.portfolio_risk_score * 100).toFixed(0)}` : undefined}
      available={!!data}
    >
      {data && (
        <div className="space-y-qp-3">
          {data.rationale && (
            <p className="text-qp-body text-qp-text-secondary">{data.rationale}</p>
          )}
          {data.adjustments.length > 0 && (
            <div>
              <p className="text-qp-small text-qp-text-muted mb-qp-1">Adjustments:</p>
              {data.adjustments.map((a, i) => (
                <div key={i} className="flex items-center gap-qp-2 text-qp-body">
                  <span className="font-mono w-12">{a.ticker}</span>
                  <span className={`font-mono ${a.delta < 0 ? "text-qp-red-600" : "text-qp-green-600"}`}>
                    {a.delta > 0 ? "+" : ""}{(a.delta * 100).toFixed(1)}%
                  </span>
                  {a.reason && (
                    <span className="text-qp-text-muted text-qp-small">{a.reason}</span>
                  )}
                </div>
              ))}
            </div>
          )}
          {data.constraints_applied.length > 0 && (
            <div className="flex flex-wrap gap-qp-1">
              {data.constraints_applied.map((c) => (
                <span key={c} className="px-qp-2 py-0.5 bg-qp-border rounded-qp-sm text-qp-small text-qp-text-secondary">
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </StageCard>
  );
}
