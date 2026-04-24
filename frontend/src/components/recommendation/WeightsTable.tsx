"use client";

import { WeightEntry } from "@/services/api";
import { usePaneContext } from "@/components/shell/ContextPane";

function stanceColor(stance: string | null): string {
  switch (stance) {
    case "overweight": return "text-qp-green-600";
    case "underweight": return "text-qp-red-600";
    default: return "text-qp-text-secondary";
  }
}

function WeightBar({ weight }: { weight: number }) {
  const pct = Math.round(weight * 100);
  return (
    <div className="flex items-center gap-qp-2">
      <div className="w-20 h-1.5 bg-qp-border rounded-full overflow-hidden">
        <div
          className="h-full bg-qp-blue-500 rounded-full"
          style={{ width: `${Math.min(pct * 5, 100)}%` }}
        />
      </div>
      <span className="text-qp-small font-mono w-10 text-right">{pct}%</span>
    </div>
  );
}

export function WeightsTable({ weights }: { weights: WeightEntry[] }) {
  const { openPane } = usePaneContext();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-qp-body">
        <thead>
          <tr className="border-b border-qp-border text-qp-small text-qp-text-muted">
            <th className="text-left py-qp-2 pr-qp-3">Ticker</th>
            <th className="text-left py-qp-2 pr-qp-3">Name</th>
            <th className="text-right py-qp-2 pr-qp-3">Weight</th>
            <th className="text-right py-qp-2 pr-qp-3">Delta</th>
            <th className="text-left py-qp-2">Stance</th>
          </tr>
        </thead>
        <tbody>
          {weights.map((w) => (
            <tr
              key={w.asset_id}
              className="border-b border-qp-border/50 hover:bg-qp-bg-hover cursor-pointer transition-colors duration-qp"
              onClick={() =>
                openPane(`${w.ticker} Detail`, (
                  <div className="space-y-qp-4">
                    <div>
                      <p className="text-qp-small text-qp-text-muted">Asset</p>
                      <p className="text-qp-body font-medium">{w.name} ({w.ticker})</p>
                    </div>
                    <div>
                      <p className="text-qp-small text-qp-text-muted">Target Weight</p>
                      <p className="text-qp-h2 font-mono">{(w.target_weight * 100).toFixed(1)}%</p>
                    </div>
                    {w.previous_weight != null && (
                      <div>
                        <p className="text-qp-small text-qp-text-muted">Previous Weight</p>
                        <p className="text-qp-body font-mono">{(w.previous_weight * 100).toFixed(1)}%</p>
                      </div>
                    )}
                    {w.delta != null && (
                      <div>
                        <p className="text-qp-small text-qp-text-muted">Change</p>
                        <p className={`text-qp-body font-mono ${w.delta > 0 ? "text-qp-green-600" : w.delta < 0 ? "text-qp-red-600" : ""}`}>
                          {w.delta > 0 ? "+" : ""}{(w.delta * 100).toFixed(1)}%
                        </p>
                      </div>
                    )}
                    <div>
                      <p className="text-qp-small text-qp-text-muted">Stance</p>
                      <p className={`text-qp-body font-medium ${stanceColor(w.stance)}`}>
                        {w.stance || "—"}
                      </p>
                    </div>
                    {w.rationale && (
                      <div>
                        <p className="text-qp-small text-qp-text-muted">Rationale</p>
                        <p className="text-qp-body text-qp-text-secondary">{w.rationale}</p>
                      </div>
                    )}
                  </div>
                ))
              }
            >
              <td className="py-qp-2 pr-qp-3 font-mono font-medium">{w.ticker}</td>
              <td className="py-qp-2 pr-qp-3 text-qp-text-secondary">{w.name}</td>
              <td className="py-qp-2 pr-qp-3 text-right">
                <WeightBar weight={w.target_weight} />
              </td>
              <td className={`py-qp-2 pr-qp-3 text-right font-mono ${
                w.delta != null && w.delta > 0 ? "text-qp-green-600" : w.delta != null && w.delta < 0 ? "text-qp-red-600" : ""
              }`}>
                {w.delta != null ? `${w.delta > 0 ? "+" : ""}${(w.delta * 100).toFixed(1)}%` : "—"}
              </td>
              <td className={`py-qp-2 ${stanceColor(w.stance)}`}>
                {w.stance || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
