"use client";

/**
 * Dossier visuals — dynamic, decision-relevant graphics for the detail screen.
 *
 * Design constraints this file obeys, all pre-existing in the repo:
 *  - Zero fiction (K1): every pixel is driven by a real payload value. Nothing
 *    is smoothed, extrapolated or invented. Where a value is missing the
 *    component says so instead of drawing a plausible shape.
 *  - Bounded vocabulary: files under components/simple are scanned by
 *    simpleStance.test.ts for engine words. Only research language here.
 *  - Tokens only (D14): colours come from globals.css custom properties, so
 *    light/dark themes and the WCAG-tuned palette apply automatically.
 *  - CSP: pure inline SVG, no external assets, no new dependencies.
 *  - prefers-reduced-motion: every animation is opt-out.
 *
 * The engine ensemble block is the reason this file exists. The dossier has
 * always carried per-engine score/confidence/stance, and the UI rendered none
 * of it — the reader saw a verdict with no way to see how it was reached.
 */

import { useEffect, useMemo, useRef, useState } from "react";

import {
  STANCE_HOVER_LABEL,
  stanceTone,
  toSimpleStance,
} from "@/lib/simpleStance";

/* ── shared helpers ───────────────────────────────────────────────────── */

/** Honours the OS "reduce motion" setting; static render on the server. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches);
    // Safari <14 only supports the deprecated listener API.
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else mq.addListener(onChange);
    return () => {
      if (mq.removeEventListener) mq.removeEventListener("change", onChange);
      else mq.removeListener(onChange);
    };
  }, []);
  return reduced;
}

/** Drives a 0→1 progress value once the element is on screen. */
function useEnterProgress(reduced: boolean, durationMs = 750): [number, (el: HTMLDivElement | null) => void] {
  const [t, setT] = useState(reduced ? 1 : 0);
  const started = useRef(false);
  const setRef = (el: HTMLDivElement | null) => {
    if (!el || started.current) return;
    if (reduced) {
      setT(1);
      started.current = true;
      return;
    }
    // IntersectionObserver is unavailable in jsdom/happy-dom and old Safari;
    // animating immediately is the correct fallback, never "stay invisible".
    if (typeof IntersectionObserver === "undefined") {
      started.current = true;
      run();
      return;
    }
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting) && !started.current) {
        started.current = true;
        io.disconnect();
        run();
      }
    }, { threshold: 0.15 });
    io.observe(el);
  };

  function run() {
    const start = performance.now();
    const step = (now: number) => {
      const p = Math.min(1, (now - start) / durationMs);
      // easeOutCubic — settles rather than snapping.
      setT(1 - Math.pow(1 - p, 3));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  useEffect(() => {
    if (reduced) setT(1);
  }, [reduced]);

  return [t, setRef];
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

function toneVar(tone: "pos" | "neutral" | "caution"): string {
  if (tone === "pos") return "var(--pos)";
  if (tone === "caution") return "var(--caution)";
  return "var(--ink-3)";
}

/* ── EnsembleDial ─────────────────────────────────────────────────────────
   The composite score on its real scale (-1..+1) with the engine's actual
   decision thresholds drawn as zones, so the reader can see how close the
   reading is to changing category — a number alone hides that entirely. */

// Mirrors STANCE_BUY_THRESHOLD / STANCE_SELL_THRESHOLD in
// backend/app/services/single_ticker_analysis.py. If those move, move these.
export const CONSTRUCTIVE_AT = 0.3;
export const CAUTIOUS_AT = -0.25;

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 180) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arcPath(cx: number, cy: number, r: number, fromDeg: number, toDeg: number) {
  const a = polar(cx, cy, r, fromDeg);
  const b = polar(cx, cy, r, toDeg);
  const large = Math.abs(toDeg - fromDeg) > 180 ? 1 : 0;
  return `M ${a.x} ${a.y} A ${r} ${r} 0 ${large} 1 ${b.x} ${b.y}`;
}

/** score (-1..1) → dial angle (0..180) */
const scoreToDeg = (s: number) => ((clamp(s, -1, 1) + 1) / 2) * 180;

/** Distance from the score to the nearest category boundary it has not crossed. */
export function nearestBoundary(score: number): { edge: number; gap: number; toward: string } | null {
  if (!Number.isFinite(score)) return null;
  const candidates = [
    { edge: CAUTIOUS_AT, toward: score > CAUTIOUS_AT ? "cautious" : "neutral" },
    { edge: CONSTRUCTIVE_AT, toward: score < CONSTRUCTIVE_AT ? "constructive" : "neutral" },
  ];
  let best = candidates[0];
  let bestGap = Math.abs(score - best.edge);
  for (const c of candidates.slice(1)) {
    const gap = Math.abs(score - c.edge);
    if (gap < bestGap) {
      best = c;
      bestGap = gap;
    }
  }
  return { edge: best.edge, gap: bestGap, toward: best.toward };
}

/** How close the reading is to changing category — subtraction, not inference. */
export function ThresholdProximity({ score }: { score: number }) {
  const near = nearestBoundary(score);
  if (!near) return null;
  // Deliberately not phrased as movement ("close to constructive") — that would
  // imply drift the system has not measured. It states a distance.
  const unstable = near.gap < 0.05;
  return (
    <p
      data-testid="threshold-proximity"
      className={
        unstable
          ? "mt-2 rounded border border-caution bg-caution-soft px-2 py-1 text-xs text-caution-soft-ink"
          : "mt-2 text-xs text-ink-2"
      }
    >
      {near.gap.toFixed(2)} from the {near.edge > 0 ? "+" : ""}
      {near.edge} boundary with <strong>{near.toward}</strong>.
      {unstable && " At this distance the label is sensitive to small revisions."}
    </p>
  );
}

export function EnsembleDial({
  score,
  confidence,
  stance,
}: {
  score: number;
  confidence: number;
  stance: string;
}) {
  const reduced = useReducedMotion();
  const [t, setRef] = useEnterProgress(reduced);
  const simple = toSimpleStance(stance);
  const tone = stanceTone(simple);

  const W = 260;
  const H = 150;
  const cx = W / 2;
  const cy = 132;
  const r = 104;

  const target = scoreToDeg(score);
  const animated = 0 + (target - 0) * t;
  const needle = polar(cx, cy, r - 16, animated);
  const confPct = Math.round(clamp(confidence, 0, 1) * 100);

  return (
    <div
      ref={setRef}
      className="rounded-lg border border-line bg-surface p-4"
      data-testid="ensemble-dial"
    >
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-ink-2">
        Ensemble reading
      </h3>
      <div className="flex flex-col items-center">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full max-w-[280px]"
          role="img"
          aria-label={`Ensemble score ${score.toFixed(2)} on a scale of minus one to one, ${simple}, confidence ${confPct} percent`}
        >
          <title>{`Ensemble score ${score.toFixed(2)} (${simple})`}</title>
          {/* zones — drawn at the engine's real thresholds */}
          <path d={arcPath(cx, cy, r, 0, scoreToDeg(CAUTIOUS_AT))}
            stroke="var(--caution)" strokeWidth={12} fill="none" opacity={0.28} strokeLinecap="round" />
          <path d={arcPath(cx, cy, r, scoreToDeg(CAUTIOUS_AT), scoreToDeg(CONSTRUCTIVE_AT))}
            stroke="var(--line-strong)" strokeWidth={12} fill="none" opacity={0.55} />
          <path d={arcPath(cx, cy, r, scoreToDeg(CONSTRUCTIVE_AT), 180)}
            stroke="var(--pos)" strokeWidth={12} fill="none" opacity={0.28} strokeLinecap="round" />

          {/* travelled arc */}
          <path
            d={arcPath(cx, cy, r, 0, Math.max(0.01, animated))}
            stroke={toneVar(tone)}
            strokeWidth={12}
            fill="none"
            strokeLinecap="round"
          />

          {/* threshold ticks */}
          {[CAUTIOUS_AT, CONSTRUCTIVE_AT].map((v) => {
            const p1 = polar(cx, cy, r - 10, scoreToDeg(v));
            const p2 = polar(cx, cy, r + 10, scoreToDeg(v));
            return (
              <line key={v} x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="var(--ink-4)" strokeWidth={1.5} />
            );
          })}

          <line x1={cx} y1={cy} x2={needle.x} y2={needle.y}
            stroke="var(--ink)" strokeWidth={2.5} strokeLinecap="round" />
          <circle cx={cx} cy={cy} r={5} fill="var(--ink)" />

          <text x={cx} y={cy - 42} textAnchor="middle"
            className="fill-ink" style={{ fontSize: 30, fontWeight: 700, fontFamily: "var(--font-mono)" }}>
            {(score * t).toFixed(2)}
          </text>
          <text x={cx} y={cy - 22} textAnchor="middle"
            className="fill-ink-2" style={{ fontSize: 12 }}>
            {simple}
          </text>
          <text x={12} y={cy + 12} className="fill-ink-4" style={{ fontSize: 10 }}>-1.0</text>
          <text x={W - 24} y={cy + 12} className="fill-ink-4" style={{ fontSize: 10 }}>+1.0</text>
        </svg>

        <div className="mt-2 w-full" title={STANCE_HOVER_LABEL}>
          <div className="mb-1 flex items-baseline justify-between text-xs text-ink-2">
            <span>Ensemble confidence</span>
            <span className="font-mono text-ink">{confPct}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
            <div
              className="h-full rounded-full"
              style={{
                width: `${confPct * t}%`,
                background: "var(--primary)",
                transition: reduced ? "none" : "width 120ms linear",
              }}
            />
          </div>
        </div>
        {/* How far this reading sits from changing category. A score of 0.29
            and one of 0.85 both render as the same word; only the distance
            distinguishes a reading that is one revision away from one that is
            settled. Pure subtraction on two real numbers. */}
        <ThresholdProximity score={score} />
        <p className="mt-2 text-xs text-ink-4">
          Zones mark the engine&apos;s own thresholds ({CAUTIOUS_AT} / +{CONSTRUCTIVE_AT}).
          Research overlay, not a prediction.
        </p>
      </div>
    </div>
  );
}

/* ── EngineVotes ──────────────────────────────────────────────────────────
   Every engine's vote on one shared axis. This is the "why" behind the dial:
   a split ensemble and a unanimous one can produce the same composite, and
   only this view distinguishes them. */

export interface EngineOutput {
  score: number;
  confidence: number;
  stance: string;
  risk_level?: string;
  drivers?: string[];
  caveats?: string[];
}

const ENGINE_LABELS: Record<string, string> = {
  technical_momentum: "Technical momentum",
  risk_quality: "Risk & quality",
  news_sentiment: "News sentiment",
};

export function EngineVotes({ engines }: { engines: Record<string, EngineOutput> }) {
  const reduced = useReducedMotion();
  const [t, setRef] = useEnterProgress(reduced, 850);
  const [openKey, setOpenKey] = useState<string | null>(null);
  const rows = useMemo(
    () => Object.entries(engines ?? {}).filter(([, v]) => v && typeof v.score === "number"),
    [engines],
  );
  if (!rows.length) return null;

  return (
    <div ref={setRef} className="rounded-lg border border-line bg-surface p-4" data-testid="engine-votes">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-ink-2">
        How the ensemble voted
      </h3>
      <p className="mb-3 text-xs text-ink-4">
        Each engine scores on the same −1…+1 axis. Bar length is the score; the
        dot is that engine&apos;s confidence weight in the blend.
      </p>
      <ul className="space-y-3">
        {rows.map(([key, e]) => {
          const simple = toSimpleStance(e.stance);
          const tone = stanceTone(simple);
          const s = clamp(e.score, -1, 1) * t;
          const halfPct = Math.abs(s) * 50;
          const conf = clamp(e.confidence ?? 0, 0, 1);
          const drivers = e.drivers ?? [];
          const caveats = e.caveats ?? [];
          const hasWhy = drivers.length > 0 || caveats.length > 0;
          const open = openKey === key;
          return (
            <li key={key}>
              <div className="mb-1 flex flex-wrap items-baseline gap-x-2 text-xs">
                <span className="font-medium text-ink">{ENGINE_LABELS[key] ?? key}</span>
                <span className="text-ink-2">{simple}</span>
                {e.risk_level && <span className="text-ink-4">risk: {e.risk_level}</span>}
                {/* Caveat count is visible BEFORE expanding: a limitation the
                    reader has to click to discover is a limitation hidden. */}
                {caveats.length > 0 && (
                  <span className="rounded bg-caution-soft px-1.5 text-[10px] text-caution-soft-ink">
                    {caveats.length} caveat{caveats.length > 1 ? "s" : ""}
                  </span>
                )}
                <span className="ml-auto font-mono text-ink">{e.score.toFixed(2)}</span>
              </div>
              <div className="relative h-5 w-full rounded bg-surface-2">
                {/* centre line = zero */}
                <div className="absolute inset-y-0 left-1/2 w-px bg-line-strong" />
                <div
                  className="absolute inset-y-1 rounded"
                  style={{
                    left: s >= 0 ? "50%" : `${50 - halfPct}%`,
                    width: `${halfPct}%`,
                    background: toneVar(tone),
                    opacity: 0.35 + 0.65 * conf,
                    transition: reduced ? "none" : "width 120ms linear, left 120ms linear",
                  }}
                />
                {/* confidence marker along the same axis */}
                <div
                  className="absolute top-1/2 h-2 w-2 -translate-y-1/2 rounded-full border border-surface"
                  style={{
                    left: `calc(${50 + clamp(e.score, -1, 1) * 50 * t}% - 4px)`,
                    background: "var(--ink)",
                    opacity: 0.25 + 0.75 * conf,
                  }}
                  title={`confidence ${Math.round(conf * 100)}%`}
                />
              </div>

              {/* The engine's own reasoning. Both fields have always been in
                  the payload and rendered nowhere, so a reader could see three
                  lanes disagree with no material for adjudicating between them.
                  Server strings render verbatim — the client never rewrites
                  server honesty. */}
              {hasWhy && (
                <>
                  <button
                    type="button"
                    aria-expanded={open}
                    aria-controls={`engine-why-${key}`}
                    onClick={() => setOpenKey((cur) => (cur === key ? null : key))}
                    className="mt-1 inline-flex min-h-11 items-center text-xs text-primary underline"
                  >
                    {open ? "Hide reasoning" : "Why this vote"}
                  </button>
                  {open && (
                    <div
                      id={`engine-why-${key}`}
                      data-testid={`engine-why-${key}`}
                      className="mt-1 rounded border border-line bg-surface-2 p-2 text-xs"
                    >
                      {drivers.length > 0 && (
                        <>
                          <p className="font-medium text-ink">Drivers</p>
                          <ul className="mb-1 list-disc pl-4 text-ink-2">
                            {drivers.map((d) => <li key={d}>{d}</li>)}
                          </ul>
                        </>
                      )}
                      {caveats.length > 0 && (
                        <div className="border-l-2 border-caution pl-2">
                          <p className="font-medium text-ink">Caveats</p>
                          <ul className="list-disc pl-4 text-ink-2">
                            {caveats.map((c) => <li key={c}>{c}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ul>
      <div className="mt-2 flex justify-between text-[10px] text-ink-4">
        <span>−1.0</span><span>0</span><span>+1.0</span>
      </div>
    </div>
  );
}

/* ── SentimentSplit ───────────────────────────────────────────────────────
   Proportional 7-day headline mix. Counts are integers from the payload; the
   bar is a ratio of those integers and nothing else. */

const SENTIMENT_TONE: Record<string, string> = {
  positive: "var(--pos)",
  negative: "var(--breach)",
  neutral: "var(--ink-4)",
};

export function SentimentSplit({ counts }: { counts: Record<string, number> }) {
  const reduced = useReducedMotion();
  const [t, setRef] = useEnterProgress(reduced, 600);
  const entries = Object.entries(counts ?? {}).filter(([, n]) => typeof n === "number" && n > 0);
  const total = entries.reduce((a, [, n]) => a + n, 0);
  if (!total) return null;

  return (
    <div ref={setRef} data-testid="sentiment-split">
      <div className="mb-1 flex items-baseline justify-between text-xs text-ink-2">
        <span>7-day headline mix</span>
        <span className="font-mono text-ink">{total}</span>
      </div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-surface-2" role="img"
        aria-label={entries.map(([k, n]) => `${n} ${k}`).join(", ")}>
        {entries.map(([label, n]) => (
          <div
            key={label}
            title={`${label}: ${n}`}
            style={{
              width: `${(n / total) * 100 * t}%`,
              background: SENTIMENT_TONE[label.toLowerCase()] ?? "var(--ink-4)",
              transition: reduced ? "none" : "width 120ms linear",
            }}
          />
        ))}
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-ink-2">
        {entries.map(([label, n]) => (
          <span key={label} className="inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full"
              style={{ background: SENTIMENT_TONE[label.toLowerCase()] ?? "var(--ink-4)" }} />
            {label} {n}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── PriceArea ────────────────────────────────────────────────────────────
   The close series as a gradient area with its real extremes marked. The
   line is drawn point-to-point: no smoothing, because a smoothed curve
   invents prices between sessions. */

export function PriceArea({
  series,
  latestBar,
  ticker,
}: {
  series: Array<{ date: string; close: number }>;
  latestBar: string;
  ticker: string;
}) {
  const reduced = useReducedMotion();
  const [t, setRef] = useEnterProgress(reduced, 900);

  const geom = useMemo(() => {
    const pts = (series ?? []).filter((p) => typeof p.close === "number" && Number.isFinite(p.close));
    if (pts.length < 2) return null;
    const W = 600;
    const H = 180;
    const padY = 14;
    const closes = pts.map((p) => p.close);
    const lo = Math.min(...closes);
    const hi = Math.max(...closes);
    const span = hi - lo || 1;
    const x = (i: number) => (i / (pts.length - 1)) * W;
    const y = (v: number) => padY + (1 - (v - lo) / span) * (H - padY * 2);
    const line = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(2)} ${y(p.close).toFixed(2)}`).join(" ");
    const area = `${line} L ${W} ${H} L 0 ${H} Z`;
    const loI = closes.indexOf(lo);
    const hiI = closes.indexOf(hi);
    const first = closes[0];
    const last = closes[closes.length - 1];
    return {
      W, H, line, area, lo, hi, first, last,
      loPt: { x: x(loI), y: y(lo) },
      hiPt: { x: x(hiI), y: y(hi) },
      lastPt: { x: x(pts.length - 1), y: y(last) },
      changePct: ((last / first - 1) * 100),
      n: pts.length,
    };
  }, [series]);

  if (!geom) return null;
  const up = geom.changePct >= 0;
  const stroke = up ? "var(--pos)" : "var(--breach)";

  return (
    <div ref={setRef} className="rounded-lg border border-line bg-surface p-4" data-testid="price-area">
      <div className="mb-2 flex flex-wrap items-baseline gap-x-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-ink-2">
          Price · {geom.n} sessions
        </h3>
        <span className="font-mono text-sm" style={{ color: stroke }}>
          {up ? "+" : ""}{geom.changePct.toFixed(1)}%
        </span>
        <span className="ml-auto text-xs text-ink-4">through {latestBar}</span>
      </div>
      <svg viewBox={`0 0 ${geom.W} ${geom.H}`} className="h-44 w-full sm:h-56" role="img"
        aria-label={`${ticker} closing price over ${geom.n} sessions, ${up ? "up" : "down"} ${Math.abs(geom.changePct).toFixed(1)} percent, low ${geom.lo}, high ${geom.hi}`}>
        <title>{`${ticker} closing prices, ${geom.n} sessions through ${latestBar}`}</title>
        <defs>
          <linearGradient id="finrlx-price-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={stroke} stopOpacity={0.28} />
            <stop offset="100%" stopColor={stroke} stopOpacity={0} />
          </linearGradient>
          <clipPath id="finrlx-price-reveal">
            <rect x="0" y="0" width={geom.W * t} height={geom.H} />
          </clipPath>
        </defs>
        <g clipPath="url(#finrlx-price-reveal)">
          <path d={geom.area} fill="url(#finrlx-price-fill)" />
          <path d={geom.line} fill="none" stroke={stroke} strokeWidth={2}
            strokeLinejoin="round" strokeLinecap="round" />
        </g>
        {t > 0.98 && (
          <>
            <circle cx={geom.hiPt.x} cy={geom.hiPt.y} r={3.5} fill="var(--pos)" />
            <circle cx={geom.loPt.x} cy={geom.loPt.y} r={3.5} fill="var(--breach)" />
            <circle cx={geom.lastPt.x} cy={geom.lastPt.y} r={4} fill={stroke}
              stroke="var(--surface)" strokeWidth={2} />
          </>
        )}
      </svg>
      <div className="mt-1 flex justify-between font-mono text-[11px] text-ink-4">
        <span>low {geom.lo.toFixed(2)}</span>
        <span>last {geom.last.toFixed(2)}</span>
        <span>high {geom.hi.toFixed(2)}</span>
      </div>
    </div>
  );
}
