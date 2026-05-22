"use client";

/**
 * Phase 16.1 — Fundamentals panel for /research/[ticker].
 *
 * Replaces the prior "coming later" placeholder card. Consumes
 * /api/v1/research/fundamentals/{ticker} which:
 *   - always returns 200 with a structurally-complete envelope
 *   - tags `source="stub"` and carries `coverage_note` when no
 *     provider is configured (Phase 16.0 default state)
 *   - tags `source="finnhub"` (or other provider) when activated
 *
 * Tiles only render when a numeric value is present. Empty fields
 * collapse — never invent a number to fill the grid. Every tile
 * carries a unit + the provenance footer ships `source` + `as_of`.
 *
 * Owned by skills:
 *   - finrlx-fintech-dashboard-patterns (every tile = label + value +
 *     unit; provenance footer; semantic palette)
 *   - fintech-disclaimer-and-marketing-guard (copy is neutral —
 *     "P/E (TTM)" not "Cheap" or "Expensive")
 *   - recommendation-object-provenance (no derived "score" anywhere —
 *     raw metrics only)
 *   - finrlx-ai-ux-governance (no AI verdicts, no "Buy/Sell" hints)
 */
import { useEffect, useState } from "react";

import { fetchFundamentals, type FundamentalsData } from "@/services/api";
import { Icon } from "@/components/icons/Icon";

interface Props {
  ticker: string;
}

interface MetricSpec {
  key: keyof FundamentalsData;
  label: string;
  format: (v: number) => string;
}

const VALUATION: ReadonlyArray<MetricSpec> = [
  { key: "pe_ratio_ttm", label: "P/E (TTM)", format: fmtMultiple },
  { key: "forward_pe", label: "Forward P/E", format: fmtMultiple },
  { key: "price_to_book", label: "P/B", format: fmtMultiple },
  { key: "price_to_sales_ttm", label: "P/S (TTM)", format: fmtMultiple },
  { key: "ev_to_ebitda", label: "EV / EBITDA", format: fmtMultiple },
];

const PROFITABILITY: ReadonlyArray<MetricSpec> = [
  { key: "gross_margin_ttm", label: "Gross margin", format: fmtPct },
  { key: "operating_margin_ttm", label: "Op. margin", format: fmtPct },
  { key: "net_margin_ttm", label: "Net margin", format: fmtPct },
];

const GROWTH: ReadonlyArray<MetricSpec> = [
  { key: "revenue_ttm_usd", label: "Revenue (TTM)", format: fmtUSD },
  { key: "revenue_growth_yoy", label: "Revenue YoY", format: fmtPctSigned },
  { key: "eps_ttm", label: "EPS (TTM)", format: fmtUSDPerShare },
  { key: "dividend_yield", label: "Dividend yield", format: fmtPct },
];

export function FundamentalsPanel({ ticker }: Props) {
  const [data, setData] = useState<FundamentalsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchFundamentals(ticker)
      .then((res) => {
        if (!cancelled) setData(res.data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (error) {
    return (
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <PanelHeader />
        <p className="text-body-sm text-breach-soft-ink mt-2">
          Fundamentals unreachable: {error}
        </p>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="rounded-lg border border-line bg-surface p-pad shadow-sm">
        <PanelHeader />
        <p className="text-body-sm text-ink-3 mt-2">Loading fundamentals…</p>
      </section>
    );
  }

  const isStub = data.source === "stub";
  const hasAnyMetric = [...VALUATION, ...PROFITABILITY, ...GROWTH].some(
    (m) => data[m.key] != null,
  );

  return (
    <section
      aria-labelledby="fundamentals-heading"
      className="rounded-lg border border-line bg-surface p-pad shadow-sm"
    >
      <PanelHeader sector={data.sector} industry={data.industry} />

      {/* Stub state — no real data; explain what's missing and what to do. */}
      {isStub || data.coverage_note ? (
        <div className="mt-3 rounded-md border border-dashed border-line bg-surface-2 p-3">
          <p className="text-body-sm text-ink-2">
            {data.coverage_note ?? "No fundamentals data for this ticker."}
          </p>
        </div>
      ) : null}

      {/* Real data — three sections.  Every section hides if all its
          metrics are null, so a partial-coverage provider doesn't leave
          empty headings. */}
      {!isStub && hasAnyMetric && (
        <>
          <MetricGroup label="Valuation" data={data} specs={VALUATION} />
          <MetricGroup label="Profitability" data={data} specs={PROFITABILITY} />
          <MetricGroup label="Growth & income" data={data} specs={GROWTH} />
        </>
      )}

      {/* Provenance footer — required by finrlx-fintech-dashboard-patterns */}
      <Provenance source={data.source} asOf={data.as_of} cachedAt={data.cached_at} />
    </section>
  );
}

function PanelHeader({
  sector,
  industry,
}: {
  sector?: string | null;
  industry?: string | null;
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Icon name="layers" size={14} className="text-ink-3" />
      <h2 id="fundamentals-heading" className="text-card-title text-ink">
        Fundamentals
      </h2>
      {sector && (
        <span className="ml-auto text-meta text-ink-3 font-mono uppercase tracking-wider">
          {industry ?? sector}
        </span>
      )}
    </div>
  );
}

function MetricGroup({
  label,
  data,
  specs,
}: {
  label: string;
  data: FundamentalsData;
  specs: ReadonlyArray<MetricSpec>;
}) {
  const visible = specs.filter((s) => typeof data[s.key] === "number");
  if (visible.length === 0) return null;
  return (
    <div className="mt-4">
      <p className="text-meta text-ink-4 uppercase tracking-wider mb-2">{label}</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {visible.map((s) => (
          <Tile key={s.key as string} label={s.label} value={s.format(data[s.key] as number)} />
        ))}
      </div>
    </div>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-surface-2 p-3">
      <p className="text-meta text-ink-4">{label}</p>
      <p className="text-card-title font-mono text-ink mt-0.5 tabular-nums">{value}</p>
    </div>
  );
}

function Provenance({
  source,
  asOf,
  cachedAt,
}: {
  source: string;
  asOf: string | null;
  cachedAt: string | null;
}) {
  return (
    <p className="text-meta text-ink-4 mt-4 pt-3 border-t border-line">
      Source <span className="font-mono">{source}</span>
      {asOf && (
        <>
          {" "}
          · as of <span className="font-mono">{asOf.slice(0, 10)}</span>
        </>
      )}
      {cachedAt && (
        <>
          {" "}
          · cached <span className="font-mono">{cachedAt.slice(0, 16).replace("T", " ")}</span>
        </>
      )}
    </p>
  );
}

// ── Formatters ──────────────────────────────────────────────────────────

function fmtMultiple(v: number): string {
  return `${v.toFixed(1)}×`;
}

function fmtPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function fmtPctSigned(v: number): string {
  const pct = v * 100;
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

function fmtUSD(v: number): string {
  if (Math.abs(v) >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  return `$${v.toFixed(0)}`;
}

function fmtUSDPerShare(v: number): string {
  return `$${v.toFixed(2)}`;
}
