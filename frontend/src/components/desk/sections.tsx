"use client";

/**
 * LEAP A5 — the Analyst Desk sections (§5 of the research report).
 * Every component takes its D42 section payload; provenance and honest
 * degradation are rendered, never assumed. Stance wording flows through
 * lib/simpleStance so the binding vocabulary holds on the desk too.
 */

import {
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { STANCE_HOVER_LABEL, stanceTone, toSimpleStance } from "@/lib/simpleStance";

import { CountIn, Pill, SectionDegraded } from "./primitives";

/* ── 1. Command header ─────────────────────────────────────────────────── */

export function HeaderSection({ payload }: { payload: any }) {
  const s = payload?.summary;
  if (!s) return <SectionDegraded reason="no_summary" />;
  const simple = toSimpleStance(s.stance);
  const tone = stanceTone(simple);
  return (
    <div data-testid="desk-header" className="flex flex-wrap items-center gap-4">
      <div>
        <div className="text-2xl font-semibold text-ink">{payload.ticker}</div>
        <div className="text-xs text-ink-4">
          latest close · <CountIn value={Number(s.latest_close ?? 0)} />
        </div>
      </div>
      <Pill tone={tone} title={STANCE_HOVER_LABEL}>
        {simple}
      </Pill>
      <Pill tone="neutral">regime: {s.regime}</Pill>
      <Pill tone="neutral" title="ensemble composite score">
        score <CountIn value={Number(s.composite_score ?? 0)} />
      </Pill>
      <span className="ml-auto text-xs text-ink-4">
        bars through {payload?.freshness?.latest_bar} · {payload?.config_version}
      </span>
      <p className="w-full text-sm text-ink-2">{s.stance_kind}</p>
    </div>
  );
}

/* ── 2. Master chart: price + regime bands + event markers ─────────────── */

const BAND_COLORS: Record<string, string> = {
  uptrend: "var(--pos-soft)",
  downtrend: "var(--caution-soft)",
  "risk-off": "var(--breach-soft)",
  neutral: "transparent",
};
const MARKER_GLYPH: Record<string, string> = {
  news: "N",
  filing: "F",
  insider: "I",
  rebalance: "R",
};

export function ChartSection({ payload }: { payload: any }) {
  const series: { date: string; close: number }[] = payload?.price_series ?? [];
  if (!series.length) return <SectionDegraded reason="no_price_series" />;
  const bands: any[] = payload?.regime_bands ?? [];
  const markers: any[] = payload?.event_markers ?? [];
  const closeByDate = new Map(series.map((p) => [p.date, p.close]));
  return (
    <div data-testid="desk-chart">
      <div className="h-72 w-full">
        <ResponsiveContainer>
          <LineChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <XAxis dataKey="date" hide />
            <YAxis domain={["auto", "auto"]} width={56}
              tick={{ fontSize: 11, fill: "var(--ink-4)" }} />
            <Tooltip
              formatter={(v: any) => [Number(v).toFixed(2), "close"]}
              labelClassName="text-xs"
            />
            {bands.map((b, i) =>
              b.label === "neutral" ? null : (
                <ReferenceLine
                  key={`b${i}`}
                  x={b.start}
                  stroke={BAND_COLORS[b.label] ?? "transparent"}
                  strokeWidth={2}
                  label={{ value: b.label, position: "top", fontSize: 9, fill: "var(--ink-4)" }}
                />
              ),
            )}
            {markers.slice(0, 40).map((m, i) => {
              const y = closeByDate.get(m.date);
              return y === undefined ? null : (
                <ReferenceDot
                  key={`m${i}`}
                  x={m.date}
                  y={y}
                  r={4}
                  fill="var(--primary)"
                  stroke="var(--surface)"
                  label={{ value: MARKER_GLYPH[m.type] ?? "•", fontSize: 8, fill: "var(--primary-ink)" }}
                />
              );
            })}
            <Line type="monotone" dataKey="close" dot={false} strokeWidth={1.6}
              stroke="var(--primary)" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <ul data-testid="marker-legend" className="mt-2 flex flex-wrap gap-2 text-xs text-ink-2">
        <li>Regime shading: colored guides mark band starts (label shown).</li>
        {["news", "filing", "insider", "rebalance"].map((t) => (
          <li key={t}>
            <span className="font-mono">{MARKER_GLYPH[t]}</span> = {t} marker
            {" "}({markers.filter((m) => m.type === t).length})
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── 3. Signal matrix heat grid ─────────────────────────────────────────── */

function pctTone(p: number | null | undefined): "pos" | "neutral" | "caution" {
  if (p === null || p === undefined) return "neutral";
  if (p >= 0.8 || p <= 0.2) return "caution"; // extreme vs own history
  return "pos";
}

export function SignalMatrixSection({ payload }: { payload: any }) {
  const rows: any[] = payload?.signal_matrix ?? [];
  if (!rows.length) return <SectionDegraded reason="no_matrix" />;
  return (
    <div data-testid="desk-signals" className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {rows.map((r) => (
        <div key={r.key} data-testid={`signal-${r.key}`}
          className="rounded-lg border border-line bg-surface-2 p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-ink-2">{r.name}</span>
            {r.percentile !== undefined && (
              <Pill tone={pctTone(r.percentile)}
                title="percentile vs this signal's own trailing history">
                {r.percentile === null ? r.percentile_note : `p${Math.round(r.percentile * 100)}`}
              </Pill>
            )}
          </div>
          <div className="mt-1 font-mono text-lg text-ink">
            {typeof r.value === "number" ? r.value.toFixed(4) : "—"}
          </div>
          {Array.isArray(r.sparkline) && (
            <Sparkline values={r.sparkline} />
          )}
          <p className="mt-1 text-xs text-ink-4">{r.read}</p>
        </div>
      ))}
    </div>
  );
}

function Sparkline({ values }: { values: (number | null)[] }) {
  const pts = values.filter((v): v is number => typeof v === "number");
  if (pts.length < 2) return null;
  const min = Math.min(...pts), max = Math.max(...pts);
  const norm = (v: number) => (max === min ? 12 : 24 - ((v - min) / (max - min)) * 24);
  const step = 120 / (pts.length - 1);
  const d = pts.map((v, i) => `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${norm(v).toFixed(1)}`).join(" ");
  return (
    <svg viewBox="0 0 120 24" className="mt-1 h-6 w-full" aria-hidden="true">
      <path d={d} fill="none" stroke="var(--ink-4)" strokeWidth="1" />
    </svg>
  );
}

/* ── 4+5. Tournament arena + RL lab ─────────────────────────────────────── */

export function TournamentSection({ payload }: { payload: any }) {
  if (!payload || payload.status !== "complete")
    return <SectionDegraded note={payload?.note ?? "Tournament pending"} />;
  const candidates: any[] = payload.candidates ?? [];
  const winnerKey = payload.winner?.key;
  const maxScore = Math.max(...candidates.map((c) => c.score), 0.001);
  return (
    <div data-testid="desk-tournament" className="space-y-4">
      <ol className="space-y-2">
        {candidates.map((c) => (
          <li key={c.key} data-testid={`cand-${c.key}`}
            className={`rounded-lg border p-3 ${c.key === winnerKey ? "border-primary bg-pos-soft" : "border-line bg-surface-2"}`}>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-ink">{c.name}</span>
              <Pill tone="neutral">{c.kind}</Pill>
              {c.imported_from_artifact && (
                <Pill tone="caution" title="trained in the isolated research environment">
                  research artifact
                </Pill>
              )}
              {c.key === winnerKey && <Pill tone="pos">selected</Pill>}
              <span className="ml-auto font-mono text-sm text-ink-2">
                score {c.score?.toFixed(3)}
              </span>
            </div>
            <div className="mt-2 h-1.5 w-full rounded bg-surface">
              <div className="h-1.5 rounded bg-primary"
                style={{ width: `${Math.max((c.score / maxScore) * 100, 2)}%` }} />
            </div>
            <div className="mt-1 flex gap-4 text-xs text-ink-4">
              <span>val Sharpe {c.val_sharpe}</span>
              <span>train {c.train_sharpe}</span>
              <span>divergence {c.divergence}</span>
              <span>penalty −{c.penalty}</span>
            </div>
          </li>
        ))}
      </ol>
      {Array.isArray(payload.split_windows) && payload.split_windows.length > 0 && (
        <div data-testid="split-viz">
          <h3 className="text-xs font-semibold uppercase text-ink-4">
            Walk-forward validation windows
          </h3>
          <ul className="mt-1 space-y-1">
            {payload.split_windows.map((w: any) => (
              <li key={w.split} className="flex items-center gap-2 text-xs">
                <span className="w-12 text-ink-4">split {w.split}</span>
                <span className="rounded bg-surface-2 px-2 py-0.5 text-ink-2">
                  train {w.train.start} → {w.train.end}
                </span>
                <span className="rounded bg-pos-soft px-2 py-0.5 text-pos-soft-ink">
                  validate {w.validation.start} → {w.validation.end}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="text-xs text-ink-4">{payload.winner?.rationale}</p>
    </div>
  );
}

export function RLLabSection({ payload }: { payload: any }) {
  if (!payload) return <SectionDegraded reason="no_rl_status" />;
  return (
    <div data-testid="desk-rl" className="space-y-2 text-sm">
      <div className="flex items-center gap-2">
        <Pill tone={payload.status === "artifact_merged" ? "pos" : "neutral"}>
          {payload.status?.replaceAll("_", " ")}
        </Pill>
        {payload.recipe && <Pill tone="neutral">{payload.recipe}</Pill>}
      </div>
      <p className="text-ink-2">{payload.note}</p>
      {Array.isArray(payload.selection_history) && payload.selection_history.length > 0 && (
        <div data-testid="rl-selection-strip">
          <h3 className="text-xs font-semibold uppercase text-ink-4">Per-period best agent</h3>
          <div className="mt-1 flex flex-wrap gap-1">
            {payload.selection_history.map((s: any, i: number) => (
              <Pill key={i} tone={s.turbulence_gate ? "breach" : "neutral"}
                title={s.turbulence_gate ? "turbulence circuit-breaker active" : undefined}>
                {s.period}: {s.selected} ({s.val_sharpe})
              </Pill>
            ))}
          </div>
        </div>
      )}
      {Array.isArray(payload.turbulence_events) && payload.turbulence_events.length > 0 && (
        <p className="text-xs text-ink-4">
          Turbulence events: {payload.turbulence_events.map((e: any) => `${e.date} (${e.action})`).join(", ")}
        </p>
      )}
    </div>
  );
}

/* ── 6. News & social tape ─────────────────────────────────────────────── */

export function NewsSocialSection({ payload }: { payload: any }) {
  if (!payload) return <SectionDegraded reason="no_payload" />;
  const items: any[] = payload.items_7d ?? [];
  const social = payload.social ?? {};
  const div = payload.divergence ?? {};
  const fingpt = payload.fingpt_lane ?? {};
  return (
    <div data-testid="desk-news" className="grid gap-4 lg:grid-cols-2">
      <div>
        <h3 className="text-xs font-semibold uppercase text-ink-4">Media lane (7d)</h3>
        {!payload.available && <SectionDegraded note={payload.note} />}
        <ul className="mt-1 space-y-1">
          {items.map((n, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="text-xs text-ink-4">{String(n.date).slice(0, 10)}</span>
              <span className="flex-1 text-ink">{n.title}</span>
              <Pill tone={n.compound > 0.05 ? "pos" : n.compound < -0.05 ? "caution" : "neutral"}>
                lex {n.compound}
              </Pill>
              {typeof n.sentiment_llm === "number" && (
                <Pill tone={n.agreement ? "pos" : "caution"}
                  title={n.agreement ? "lanes agree" : "lanes disagree"}>
                  llm {n.sentiment_llm}
                </Pill>
              )}
            </li>
          ))}
          {items.length === 0 && <li className="text-sm text-ink-4">No items in the window.</li>}
        </ul>
        <p className="mt-1 text-xs text-ink-4" data-testid="fingpt-status">
          FinGPT lane: {fingpt.status?.replaceAll("_", " ")}
          {typeof fingpt.agreement_rate === "number" && ` · agreement ${Math.round(fingpt.agreement_rate * 100)}%`}
        </p>
      </div>
      <div>
        <h3 className="text-xs font-semibold uppercase text-ink-4">Social / forums lane</h3>
        {social.available ? (
          social.scored ? (
            <div className="mt-1 space-y-1 text-sm text-ink-2" data-testid="social-scored">
              {social.reddit && (
                <p>Reddit 7d: {social.reddit.mentions_7d} mentions · avg score {social.reddit.avg_score}</p>
              )}
              {social.twitter && (
                <p>Twitter 7d: {social.twitter.mentions_7d} mentions · avg score {social.twitter.avg_score}</p>
              )}
            </div>
          ) : (
            <div className="mt-1 text-sm text-ink-2" data-testid="social-mentions">
              <Pill tone="caution" title="no sentiment scores in this lane">{social.label}</Pill>
              <p className="mt-1">
                {social.trending
                  ? `Trending #${social.rank} on tracked forums — ${social.mentions_24h} mentions / 24h.`
                  : social.read}
              </p>
            </div>
          )
        ) : (
          <SectionDegraded reason={social.reason} note="Social lane unavailable" />
        )}
        <div className="mt-3" data-testid="divergence">
          <Pill tone={div.status === "diverged" ? "breach" : div.status === "aligned" ? "pos" : "neutral"}>
            media↔social: {div.status?.replaceAll("_", " ")}
          </Pill>
          <p className="mt-1 text-xs text-ink-4">{div.read ?? div.reason}</p>
        </div>
      </div>
    </div>
  );
}

/* ── 7–9. Filings · Insider · Fundamentals ─────────────────────────────── */

export function FilingsSection({ payload }: { payload: any }) {
  if (!payload?.available)
    return <SectionDegraded reason={payload?.tone?.reason} note="No filings source configured" />;
  const tone = payload.tone ?? {};
  const sim = payload.similarity ?? {};
  return (
    <div data-testid="desk-filings" className="grid gap-4 sm:grid-cols-2 text-sm">
      {tone.available && (
        <div>
          <h3 className="text-xs font-semibold uppercase text-ink-4">
            {tone.form} tone · filed {tone.filed_date}
          </h3>
          <ul className="mt-1 space-y-0.5 text-ink-2">
            {Object.entries(tone.tone ?? {}).map(([k, v]) => (
              <li key={k} className="flex justify-between">
                <span>{k}</span>
                <span className="font-mono">{v === null ? "—" : String(v)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-1 text-xs text-ink-4">{tone.method}</p>
        </div>
      )}
      {sim.available && (
        <div data-testid="similarity-delta">
          <h3 className="text-xs font-semibold uppercase text-ink-4">
            Disclosure-language similarity (YoY)
          </h3>
          <div className="mt-1 font-mono text-2xl text-ink">
            {typeof sim.cosine_all === "number" ? sim.cosine_all.toFixed(3) : "—"}
          </div>
          <p className="text-xs text-ink-4">{sim.read}</p>
        </div>
      )}
    </div>
  );
}

export function InsiderSection({ payload }: { payload: any }) {
  if (!payload?.available)
    return <SectionDegraded reason={payload?.reason} note="No insider-data source configured" />;
  const latest = Number(payload.latest_mspr ?? 0);
  return (
    <div data-testid="desk-insider" className="text-sm">
      <div className="flex items-center gap-3">
        <span className="text-xs text-ink-4">MSPR (latest month)</span>
        <span className="font-mono text-2xl text-ink"><CountIn value={latest} decimals={1} /></span>
        <Pill tone={latest > 20 ? "pos" : latest < -20 ? "caution" : "neutral"}>
          {latest > 20 ? "insider buying tilt" : latest < -20 ? "insider selling tilt" : "balanced"}
        </Pill>
      </div>
      <div className="mt-2 flex items-end gap-1" aria-hidden="true">
        {(payload.series_12m ?? []).map((r: any, i: number) => (
          <div key={i} title={`${r.year}-${r.month}: ${r.mspr}`}
            className={`w-3 rounded-sm ${r.mspr >= 0 ? "bg-pos-soft" : "bg-caution-soft"}`}
            style={{ height: `${Math.min(Math.abs(r.mspr), 100) / 2 + 4}px` }} />
        ))}
      </div>
      <p className="mt-2 text-xs text-ink-4" data-testid="insider-caveat">{payload.caveat}</p>
    </div>
  );
}

export function FundamentalsSection({ payload }: { payload: any }) {
  if (!payload?.available)
    return <SectionDegraded note={payload?.note ?? "No fundamentals source reachable"} />;
  const x = payload.xbrl ?? {};
  const trend = (rows: any[]) => rows?.map((r) => `${r.fy}: ${fmt(r.value)}`).join(" · ");
  const fmt = (v: any) =>
    typeof v === "number"
      ? Math.abs(v) >= 1e9
        ? `${(v / 1e9).toFixed(1)}B`
        : Math.abs(v) >= 1e6
          ? `${(v / 1e6).toFixed(1)}M`
          : String(v)
      : "—";
  return (
    <div data-testid="desk-fundamentals" className="space-y-2 text-sm text-ink-2">
      {x.available ? (
        <>
          <p className="text-xs text-ink-4">
            SEC XBRL · {x.entity} · CIK {x.cik}
          </p>
          <RatioRow label="Revenue (FY)" text={trend(x.revenue)} />
          <RatioRow label="Net margin" text={x.net_margin?.map((r: any) =>
            `${r.fy}: ${r.value === null ? "—" : (r.value * 100).toFixed(1) + "%"}`).join(" · ")} />
          <RatioRow label="Leverage (L/E)" text={x.leverage_liab_over_equity?.map((r: any) =>
            `${r.fy}: ${r.value ?? "—"}`).join(" · ")} />
          <RatioRow label="Share dilution YoY" text={x.dilution_yoy?.map((r: any) =>
            `${r.fy}: ${r.value === null ? "—" : (r.value * 100).toFixed(1) + "%"}`).join(" · ")} />
        </>
      ) : (
        <SectionDegraded reason={x.reason} note="SEC XBRL unavailable" />
      )}
      {payload.snapshot?.available && (
        <p className="text-xs text-ink-4">Provider snapshot attached (Finnhub).</p>
      )}
    </div>
  );
}

function RatioRow({ label, text }: { label: string; text?: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      <span className="w-40 text-xs font-medium uppercase text-ink-4">{label}</span>
      <span className="font-mono text-xs">{text || "—"}</span>
    </div>
  );
}

/* ── 10. Risk ──────────────────────────────────────────────────────────── */

export function RiskSection({ payload }: { payload: any }) {
  const rows: any[] = payload?.signal_matrix ?? [];
  const bands: any[] = payload?.regime_bands ?? [];
  if (!rows.length && !bands.length) return <SectionDegraded reason="no_risk_inputs" />;
  return (
    <div data-testid="desk-risk" className="space-y-3 text-sm">
      <div className="grid gap-3 sm:grid-cols-3">
        {rows.map((r) => (
          <div key={r.key} className="rounded-lg border border-line bg-surface-2 p-3">
            <div className="text-xs text-ink-4">{r.name}</div>
            <div className="font-mono text-lg text-ink">
              {typeof r.value === "number" ? r.value.toFixed(4) : "—"}
            </div>
            {r.percentile !== null && r.percentile !== undefined && (
              <div className="text-xs text-ink-4">p{Math.round(r.percentile * 100)} vs own history</div>
            )}
          </div>
        ))}
      </div>
      <div data-testid="regime-timeline">
        <h3 className="text-xs font-semibold uppercase text-ink-4">Regime timeline</h3>
        <div className="mt-1 flex h-3 w-full overflow-hidden rounded">
          {bands.map((b, i) => (
            <div key={i} title={`${b.label}: ${b.start} → ${b.end}`}
              className={
                b.label === "uptrend" ? "bg-pos-soft grow" :
                b.label === "downtrend" ? "bg-caution-soft grow" :
                b.label === "risk-off" ? "bg-breach-soft grow" : "bg-surface-2 grow"
              } />
          ))}
        </div>
        <p className="mt-1 text-xs text-ink-4">
          Rule-based research overlay — the same rule as the live regime label, not a prediction.
        </p>
      </div>
    </div>
  );
}
