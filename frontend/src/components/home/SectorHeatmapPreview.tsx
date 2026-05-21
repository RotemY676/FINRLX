import { PanelEmpty, PanelShell } from "./HomePanelStates";

import type { SectorTiltRow } from "./homeTypes";

interface Props {
  rows: SectorTiltRow[];
}

/**
 * Sector tilt panel — *not* a market-wide heatmap. The data is the regime
 * model's sector posture, so the panel is labeled "sector tilt" rather than
 * "market heatmap" to avoid pretending we have a market scanner.
 */
export function SectorHeatmapPreview({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <PanelShell icon="universe" title="Sector tilt" subtitle="Regime sector posture">
        <PanelEmpty
          message="No regime sector data."
          hint="Sector posture appears here when the regime model has fresh data."
        />
      </PanelShell>
    );
  }

  const maxAbs = rows.reduce((m, r) => Math.max(m, Math.abs(r.tiltPct)), 0) || 1;

  return (
    <PanelShell icon="universe" title="Sector tilt" subtitle="Regime sector posture">
      <div className="space-y-1.5">
        {rows.map((r) => {
          const pct = (Math.abs(r.tiltPct) / maxAbs) * 100;
          const isPos = r.tiltPct >= 0;
          return (
            <div
              key={r.sector}
              className="grid grid-cols-[80px_1fr_56px] items-center gap-2 text-[12px]"
            >
              <span className="text-ink-2 truncate">{r.sector}</span>
              <div className="relative h-3 rounded-sm bg-surface-3 overflow-hidden">
                <span
                  className={`absolute top-0 h-full ${isPos ? "bg-pos" : "bg-breach"}`}
                  style={{
                    width: `${pct / 2}%`,
                    left: isPos ? "50%" : undefined,
                    right: isPos ? undefined : "50%",
                  }}
                  aria-hidden="true"
                />
                <span
                  className="absolute top-0 bottom-0 left-1/2 w-px bg-line-strong"
                  aria-hidden="true"
                />
              </div>
              <span
                className={`text-right font-mono text-[11px] ${
                  isPos ? "text-pos" : "text-breach"
                }`}
              >
                {isPos ? "+" : ""}
                {r.tiltPct.toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-[10.5px] text-ink-4 leading-snug">
        Tilts come from the regime model, not a market-wide scanner.
      </p>
    </PanelShell>
  );
}
