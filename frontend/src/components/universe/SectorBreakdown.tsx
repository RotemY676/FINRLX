import { UniverseAsset } from "@/services/api";

interface SectorRow {
  sector: string;
  count: number;
  pct: number;
}

function summarize(assets: UniverseAsset[]): SectorRow[] {
  const total = assets.length;
  if (total === 0) return [];
  const counts = new Map<string, number>();
  for (const a of assets) {
    const key = a.sector ?? "Unclassified";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const rows = Array.from(counts.entries()).map(([sector, count]) => ({
    sector,
    count,
    pct: count / total,
  }));
  rows.sort((a, b) => b.count - a.count);
  return rows;
}

export function SectorBreakdown({ assets }: { assets: UniverseAsset[] }) {
  const rows = summarize(assets);
  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[13px] font-semibold text-ink">Sector breakdown</h3>
        <span className="text-[11px] text-ink-4">{assets.length} assets</span>
      </div>
      {rows.length === 0 ? (
        <p className="text-[12.5px] text-ink-3">No assets in this universe.</p>
      ) : (
        <div className="space-y-2">
          {rows.map((r) => (
            <div key={r.sector}>
              <div className="flex items-center justify-between text-[12.5px] mb-0.5">
                <span className="text-ink-2 truncate">{r.sector}</span>
                <span className="font-mono text-ink-3">
                  {r.count} · {(r.pct * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1 bg-surface-3 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full"
                  style={{ width: `${r.pct * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
