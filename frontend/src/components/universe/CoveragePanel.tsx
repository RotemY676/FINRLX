import { UniverseCoverage } from "@/services/api";

const DOMAIN_LABELS: Record<keyof UniverseCoverage["coverage"], string> = {
  market_bars: "Market bars",
  features: "Features",
  signals: "Signals",
  model_predictions: "Model predictions",
};

function pctBarTone(pct: number): string {
  if (pct >= 0.9) return "bg-pos";
  if (pct >= 0.5) return "bg-caution";
  return "bg-breach";
}

export function CoveragePanel({ coverage }: { coverage: UniverseCoverage }) {
  const domains = Object.keys(DOMAIN_LABELS) as (keyof UniverseCoverage["coverage"])[];

  return (
    <div className="rounded-lg border border-line bg-surface p-pad shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[13px] font-semibold text-ink">Coverage</h3>
        <span className="text-[11px] text-ink-4">{coverage.asset_count} assets</span>
      </div>
      <div className="space-y-3">
        {domains.map((d) => {
          const v = coverage.coverage[d];
          return (
            <div key={d}>
              <div className="flex items-center justify-between text-[12.5px] mb-1">
                <span className="text-ink-2">{DOMAIN_LABELS[d]}</span>
                <span className="font-mono text-ink-3">
                  {v.covered}/{v.total} · {(v.pct * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${pctBarTone(v.pct)}`}
                  style={{ width: `${Math.min(100, v.pct * 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
