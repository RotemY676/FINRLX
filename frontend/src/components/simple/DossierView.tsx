"use client";

/**
 * LEAP S5 — Simple Mode dossier components (SIMPLE_MODE_SPEC §J2).
 * Reuse-first (D14): existing token classes only; three new components in one
 * module (SummaryBar, VerdictCards, TournamentScoreboard) to stay inside the
 * spec's <=4-new-components budget together with the page's TickerHero.
 */

import { useState } from "react";

import { track } from "@/lib/analytics";
import {
  STANCE_HOVER_LABEL,
  stanceTone,
  toSimpleStance,
  type SimpleStance,
} from "@/lib/simpleStance";

/* ── payload shapes (subset of E.4 used by the UI) ─────────────────────── */

export interface DossierPayload {
  ticker: string;
  generated_at: string;
  config_version: string;
  freshness: { latest_bar: string; bars: number; news_source_available: boolean };
  summary: {
    latest_close: number;
    stance: string;
    composite_score: number;
    avg_confidence: number;
    regime: string;
    stance_kind: string;
  };
  sections: {
    technical: {
      available: boolean;
      features: Record<string, number | null>;
      regime: { label: string; detail: string; kind: string };
      composite: { stance: string; composite_score: number; avg_confidence: number };
    };
    news_sentiment: {
      available: boolean;
      note: string | null;
      counts: Record<string, number>;
      annotations_status?: string;
      items_7d: Array<{
        date: string;
        title: string;
        sentiment: string;
        compound: number;
        why_this_matters?: string;
        annotation_meta?: { model: string; generated_at: string; freshness_stamp: string };
      }>;
    };
    fundamentals: { available: boolean; note: string };
    model_insight: TournamentPayload;
  };
  price_series: Array<{ date: string; close: number }>;
  disclaimers: string[];
  served_from_cache?: boolean;
  served_from_persistence?: boolean;
}

export interface TournamentPayload {
  candidates: Array<{
    key: string;
    name: string;
    kind: string;
    train_sharpe: number;
    val_sharpe: number;
    divergence: number;
    penalty: number;
    score: number;
  }>;
  winner:
    | (TournamentPayload["candidates"][number] & { rationale: string })
    | null;
  rl: { status: string; note?: string; candidates?: string[] };
  rationale?: string;
}

/* ── small primitives (token classes from globals.css only) ────────────── */

function toneClasses(tone: "pos" | "neutral" | "caution" | "breach"): string {
  switch (tone) {
    case "pos":
      return "bg-pos-soft text-pos-soft-ink";
    case "caution":
      return "bg-caution-soft text-caution-soft-ink";
    case "breach":
      return "bg-breach-soft text-breach-soft-ink";
    default:
      return "bg-surface-2 text-ink-2";
  }
}

export function Chip({
  tone = "neutral",
  title,
  children,
}: {
  tone?: "pos" | "neutral" | "caution" | "breach";
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center rounded-full border border-line px-2.5 py-0.5 text-xs font-medium ${toneClasses(tone)}`}
    >
      {children}
    </span>
  );
}

/* ── staleness (SPEC §5; calendar-naive session lag is computed server-side
      in Pro surfaces; Simple Mode derives the visual tier from day lag) ── */

export function stalenessTier(latestBarIso: string, now = new Date()):
  | "fresh"
  | "stale"
  | "degraded" {
  const latest = new Date(`${latestBarIso}T00:00:00Z`).getTime();
  const days = Math.floor((now.getTime() - latest) / 86_400_000);
  if (days <= 3) return "fresh"; // weekend-tolerant day lag
  if (days <= 7) return "stale";
  return "degraded";
}

/* ── SummaryBar ────────────────────────────────────────────────────────── */

export function SummaryBar({ dossier }: { dossier: DossierPayload }) {
  const stance: SimpleStance = toSimpleStance(dossier.summary.stance);
  const tier = stalenessTier(dossier.freshness.latest_bar);
  return (
    <div className="sticky top-0 z-10 flex flex-wrap items-center gap-2 rounded-lg border border-line bg-surface px-4 py-3">
      <span className="text-lg font-semibold text-ink">{dossier.ticker}</span>
      <span className="text-ink">{dossier.summary.latest_close.toFixed(2)}</span>
      <Chip tone={stanceTone(stance)} title={STANCE_HOVER_LABEL}>
        stance: {stance}
      </Chip>
      <Chip title="Rule-based research overlay, not a prediction.">
        regime: {dossier.summary.regime}
      </Chip>
      <Chip tone={tier === "fresh" ? "neutral" : tier === "stale" ? "caution" : "breach"}>
        Data through {dossier.freshness.latest_bar}
      </Chip>
      <button
        type="button"
        className="ml-auto rounded-lg border border-line-strong px-3 py-1 text-sm text-ink"
        onClick={() => {
          void import("@/lib/exportDossier").then((m) => m.downloadDossierHtml(dossier));
        }}
      >
        Export
      </button>
    </div>
  );
}

export function DegradedBanner({ dossier }: { dossier: DossierPayload }) {
  if (stalenessTier(dossier.freshness.latest_bar) !== "degraded") return null;
  return (
    <div className="rounded-lg border border-line bg-breach-soft px-4 py-2 text-sm text-breach-soft-ink">
      Price data ends {dossier.freshness.latest_bar}; conclusions may be outdated.
    </div>
  );
}

/* ── VerdictCards (2x2) ────────────────────────────────────────────────── */

const FEATURE_READS: Array<{ key: string; label: string }> = [
  { key: "rsi_14", label: "RSI (14)" },
  { key: "macd_hist_12_26_9", label: "MACD histogram" },
  { key: "drawdown_20d", label: "20d drawdown" },
];

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-2">
        {title}
      </h3>
      {children}
    </div>
  );
}

export function VerdictCards({ dossier }: { dossier: DossierPayload }) {
  const [signalsOpen, setSignalsOpen] = useState(false);
  const tech = dossier.sections.technical;
  const news = dossier.sections.news_sentiment;
  const techStance = toSimpleStance(tech.composite.stance);
  const featureRows = FEATURE_READS.map((f) => ({
    label: f.label,
    value: tech.features[f.key],
  })).filter((r) => r.value !== null && r.value !== undefined);

  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
      <Card title="Technical">
        <Chip tone={stanceTone(techStance)} title={STANCE_HOVER_LABEL}>
          {techStance}
        </Chip>
        <table className="mt-2 w-full text-sm">
          <tbody>
            {featureRows.map((r) => (
              <tr key={r.label} className="border-t border-line">
                <td className="py-1 text-ink-2">{r.label}</td>
                <td className="py-1 text-right font-mono text-ink">
                  {typeof r.value === "number" ? r.value.toFixed(3) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button
          type="button"
          className="mt-2 text-sm text-primary underline"
          onClick={() => {
            setSignalsOpen((v) => !v);
            if (!signalsOpen) void track("leap.evidence_expanded", { card: "technical" });
          }}
        >
          {signalsOpen ? "Hide signals" : "All signals"}
        </button>
        {signalsOpen && (
          <table className="mt-2 w-full text-xs">
            <tbody>
              {Object.entries(tech.features).map(([k, v]) => (
                <tr key={k} className="border-t border-line">
                  <td className="py-0.5 text-ink-2">{k}</td>
                  <td className="py-0.5 text-right font-mono">
                    {typeof v === "number" ? v.toFixed(4) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Card title="News & sentiment">
        {news.available ? (
          <>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {Object.entries(news.counts).map(([label, n]) => (
                <Chip key={label}>{`7d ${label}: ${n}`}</Chip>
              ))}
            </div>
            <ul className="space-y-2 text-sm">
              {news.items_7d.slice(0, 4).map((item) => (
                <li key={`${item.date}-${item.title}`} className="border-t border-line pt-2">
                  <span className="text-ink">{item.title}</span>{" "}
                  <Chip>{item.sentiment}</Chip>
                  {item.why_this_matters && (
                    <p className="mt-1 text-ink-2">
                      Why it matters: {item.why_this_matters}
                      {item.annotation_meta && (
                        <span className="block text-xs text-ink-4">
                          Generated by {item.annotation_meta.model} · based on item from{" "}
                          {item.annotation_meta.freshness_stamp}
                        </span>
                      )}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="text-sm text-ink-2">{news.note}</p>
        )}
      </Card>

      <Card title="Fundamentals">
        <p className="text-sm text-ink-2">{dossier.sections.fundamentals.note}</p>
      </Card>

      <Card title="Model insight">
        <TournamentScoreboard tournament={dossier.sections.model_insight} />
      </Card>
    </div>
  );
}

/* ── TournamentScoreboard ──────────────────────────────────────────────── */

export function TournamentScoreboard({ tournament }: { tournament: TournamentPayload }) {
  const [open, setOpen] = useState(false);
  const winner = tournament.winner;
  if (!winner) {
    return (
      <p className="text-sm text-ink-2">
        {tournament.rationale ??
          "The tournament needs more history to validate candidates honestly."}
      </p>
    );
  }
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <Chip tone="pos">winner: {winner.name}</Chip>
        <Chip>{winner.kind === "ml" ? "machine-learning" : "rule-based"}</Chip>
      </div>
      <p className="mt-2 text-sm text-ink-2">
        {winner.name} — validation score {winner.score}, chosen over{" "}
        {tournament.candidates.length} candidates after walk-forward validation with
        overfitting penalties.
      </p>
      <button
        type="button"
        className="mt-2 text-sm text-primary underline"
        onClick={() => {
          setOpen((v) => !v);
          if (!open) void track("leap.scoreboard_opened");
        }}
      >
        {open ? "Hide the scoreboard" : "How this was chosen"}
      </button>
      {open && (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-ink-2">
                <th className="py-1">Candidate</th>
                <th>Kind</th>
                <th className="text-right">Train Sharpe</th>
                <th className="text-right">Validation Sharpe</th>
                <th className="text-right">Divergence</th>
                <th className="text-right">Penalty</th>
                <th className="text-right">Score</th>
              </tr>
            </thead>
            <tbody>
              {tournament.candidates.map((c) => (
                <tr key={c.key} className="border-t border-line font-mono">
                  <td className="py-1 font-sans">{c.name}</td>
                  <td className="font-sans">{c.kind === "ml" ? "machine-learning" : "rule-based"}</td>
                  <td className="text-right">{c.train_sharpe.toFixed(2)}</td>
                  <td className="text-right">{c.val_sharpe.toFixed(2)}</td>
                  <td className="text-right">{c.divergence.toFixed(2)}</td>
                  <td className="text-right">{c.penalty.toFixed(2)}</td>
                  <td className="text-right">{c.score.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-2 rounded border border-line bg-surface-2 p-2 text-xs text-ink-2">
            <div className="font-semibold">Reinforcement-learning candidates</div>
            <div>{tournament.rl?.note ?? tournament.rl?.status}</div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Price chart ───────────────────────────────────────────────────────────
   Honesty note: the dossier payload carries the CURRENT regime label, not
   per-period band data, so this chart draws no historical regime shading
   (fake bands would be invented data). Band series = DEBT-S5-2 (backend
   addition). The svg carries a <title> per the F3 accessibility lesson. */

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function DossierPriceChart({ dossier }: { dossier: DossierPayload }) {
  const data = dossier.price_series;
  if (!data || data.length < 2) return null;
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-ink-2">
        Price · {data.length} sessions
      </h3>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <title>{`${dossier.ticker} closing prices, ${data.length} sessions through ${dossier.freshness.latest_bar}`}</title>
            <XAxis dataKey="date" hide />
            <YAxis
              domain={["auto", "auto"]}
              width={56}
              tick={{ fontSize: 11 }}
              stroke="var(--ink-4)"
            />
            <Tooltip
              formatter={(value: number | string) => [String(value), "close"]}
              labelStyle={{ color: "var(--ink-2)" }}
            />
            <Line
              type="monotone"
              dataKey="close"
              stroke="var(--primary)"
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-xs text-ink-4">
        Current regime: {dossier.summary.regime} (rule-based research overlay, not a
        prediction).
      </p>
    </div>
  );
}

/* ── Disclaimers ───────────────────────────────────────────────────────── */

export function DisclaimerStrip({ disclaimers }: { disclaimers: string[] }) {
  return (
    <div className="border-t border-line pt-2 text-xs text-ink-2">
      {disclaimers.map((d) => (
        <p key={d}>{d}</p>
      ))}
    </div>
  );
}
