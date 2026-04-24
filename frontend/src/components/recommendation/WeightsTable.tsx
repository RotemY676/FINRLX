"use client";

import { WeightEntry } from "@/services/api";
import { usePaneContext } from "@/components/shell/ContextPane";

function stanceColor(stance: string | null): string {
  switch (stance) {
    case "overweight": return "text-pos";
    case "underweight": return "text-breach";
    default: return "text-ink-3";
  }
}

export function WeightsTable({ weights }: { weights: WeightEntry[] }) {
  const { openPane } = usePaneContext();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-line text-[11px] text-ink-4 uppercase tracking-wider">
            <th className="text-left py-2 pr-3 font-medium">Ticker</th>
            <th className="text-left py-2 pr-3 font-medium">Name</th>
            <th className="text-right py-2 pr-3 font-medium">Weight</th>
            <th className="text-right py-2 pr-3 font-medium">Delta</th>
            <th className="text-left py-2 font-medium">Stance</th>
          </tr>
        </thead>
        <tbody>
          {weights.map((w) => (
            <tr
              key={w.asset_id}
              className="border-b border-line/50 hover:bg-surface-3 cursor-pointer transition-colors"
              onClick={() =>
                openPane(`${w.ticker} · ${w.name}`, (
                  <div className="space-y-4">
                    <div>
                      <p className="text-[11px] text-ink-4">Target Weight</p>
                      <p className="text-[20px] font-mono font-semibold text-ink">{(w.target_weight * 100).toFixed(1)}%</p>
                    </div>
                    {w.previous_weight != null && (
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <p className="text-[11px] text-ink-4">Previous</p>
                          <p className="text-[13px] font-mono text-ink">{(w.previous_weight * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                          <p className="text-[11px] text-ink-4">Change</p>
                          <p className={`text-[13px] font-mono ${w.delta && w.delta > 0 ? "text-pos" : w.delta && w.delta < 0 ? "text-breach" : "text-ink-3"}`}>
                            {w.delta != null ? `${w.delta > 0 ? "+" : ""}${(w.delta * 100).toFixed(1)}%` : "—"}
                          </p>
                        </div>
                      </div>
                    )}
                    <div>
                      <p className="text-[11px] text-ink-4">Stance</p>
                      <p className={`text-[13px] font-medium ${stanceColor(w.stance)}`}>{w.stance || "—"}</p>
                    </div>
                    {w.rationale && (
                      <div>
                        <p className="text-[11px] text-ink-4">Rationale</p>
                        <p className="text-[12.5px] text-ink-2">{w.rationale}</p>
                      </div>
                    )}
                  </div>
                ))
              }
            >
              <td className="py-2 pr-3 font-mono font-semibold text-ink">{w.ticker}</td>
              <td className="py-2 pr-3 text-ink-2">{w.name}</td>
              <td className="py-2 pr-3 text-right font-mono">{(w.target_weight * 100).toFixed(1)}%</td>
              <td className={`py-2 pr-3 text-right font-mono ${
                w.delta != null && w.delta > 0 ? "text-pos" : w.delta != null && w.delta < 0 ? "text-breach" : "text-ink-3"
              }`}>
                {w.delta != null ? `${w.delta > 0 ? "+" : ""}${(w.delta * 100).toFixed(1)}%` : "—"}
              </td>
              <td className={`py-2 ${stanceColor(w.stance)}`}>{w.stance || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
