"use client";

import { useMemo } from "react";
import {
  Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

/** PROGRAM LEAP S5 — dossier rendering (extracted so the page keeps a
 * single default export as Next.js requires). */

export interface Dossier {
  ticker: string;
  generated_at: string;
  freshness: { latest_bar: string; bars: number; news_source_available: boolean };
  summary: {
    latest_close: number | null;
    stance: string;
    composite_score: number;
    avg_confidence: number;
    regime: string;
    stance_kind: string;
  };
  sections: {
    technical: {
      regime: { label: string; detail: string; kind: string };
      composite: { drivers: string[]; caveats: string[] };
      engines: Record<string, { score?: number; confidence?: number }>;
    };
    news_sentiment: {
      available: boolean;
      note: string | null;
      counts: Record<string, number>;
      items_7d: { date: string; title: string; sentiment: string; compound: number }[];
    };
    fundamentals: { available: boolean; note: string };
    model_insight: {
      status: string;
      note?: string;
      n_splits?: number;
      deflation_penalty?: number;
      candidates: {
        key: string; name: string; kind: string;
        train_sharpe: number; val_sharpe: number;
        divergence: number; score: number;
      }[];
      winner: { name: string; kind: string; score: number; rationale: string } | null;
      rl: { status: string; note: string };
    };
  };
  price_series: { date: string; close: number }[];
  stages: { stage: string; ms: number }[];
  disclaimers: string[];
  served_from_cache: boolean;
}

const STANCE_STYLE: Record<string, string> = {
  buy: "bg-pos-soft text-pos",
  hold: "bg-surface-3 text-ink-2",
  sell: "bg-breach-soft text-breach",
};

function StanceBadge({ stance }: { stance: string }) {
  return (
    <span
      className={`rounded-full px-3 py-1 text-sm font-medium ${STANCE_STYLE[stance] ?? "bg-surface-3 text-ink-2"}`}
      data-testid="stance-badge"
    >
      research stance: {stance}
    </span>
  );
}

function Card({ title, children, testId }: { title: string; children: React.ReactNode; testId?: string }) {
  return (
    <section
      className="rounded-xl border border-line bg-surface p-4 md:p-5"
      data-testid={testId}
    >
      <h2 className="mb-3 text-base font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}

export function DossierView({ dossier }: { dossier: Dossier }) {
  const mi = dossier.sections.model_insight;
  const news = dossier.sections.news_sentiment;
  const tech = dossier.sections.technical;
  const chartData = useMemo(
    () => dossier.price_series.map((p) => ({ ...p, label: p.date.slice(5) })),
    [dossier.price_series],
  );

  return (
    <div className="mt-6 space-y-4" data-testid="dossier">
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-line bg-surface p-4">
        <span className="text-2xl font-semibold text-ink" data-testid="dossier-ticker">
          {dossier.ticker}
        </span>
        {dossier.summary.latest_close != null && (
          <span className="text-xl text-ink-2">{dossier.summary.latest_close.toFixed(2)}</span>
        )}
        <StanceBadge stance={dossier.summary.stance} />
        <span className="rounded-full bg-surface-3 px-3 py-1 text-sm text-ink-2">
          regime: {dossier.summary.regime}
        </span>
        <span className="ml-auto text-xs text-ink-3" data-testid="freshness">
          data through {dossier.freshness.latest_bar}
          {dossier.served_from_cache ? " · cached" : ""}
        </span>
      </div>

      <Card title="Price — last 12 months" testId="card-price">
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={40} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} width={52} />
              <Tooltip formatter={(v: number) => v.toFixed(2)} labelFormatter={(l) => `date ${l}`} />
              <Line type="monotone" dataKey="close" dot={false} strokeWidth={1.5} stroke="currentColor" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Technical read" testId="card-technical">
          <p className="text-sm text-ink-2">
            {tech.regime.label} — {tech.regime.detail}
          </p>
          <p className="mt-1 text-xs text-ink-3">{tech.regime.kind}</p>
          {tech.composite.drivers.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-sm text-ink-2">
                Evidence ({tech.composite.drivers.length} drivers
                {tech.composite.caveats.length ? `, ${tech.composite.caveats.length} caveats` : ""})
              </summary>
              <ul className="mt-2 space-y-1 text-xs text-ink-3">
                {tech.composite.drivers.map((d) => <li key={d}>▲ {d}</li>)}
                {tech.composite.caveats.map((c) => <li key={c}>△ {c}</li>)}
              </ul>
            </details>
          )}
        </Card>

        <Card title="News and sentiment" testId="card-news">
          {news.available ? (
            <>
              <p className="text-sm text-ink-2">
                Last 7 days:{" "}
                {Object.entries(news.counts).map(([k, v]) => `${v} ${k}`).join(" · ") || "no items"}
              </p>
              <ul className="mt-3 space-y-2">
                {news.items_7d.slice(0, 5).map((n) => (
                  <li key={`${n.date}-${n.title}`} className="text-xs text-ink-3">
                    <span className="text-ink-2">{n.sentiment}</span> · {n.date.slice(0, 10)} — {n.title}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-caution" data-testid="news-degraded">
              {news.note}
            </p>
          )}
        </Card>

        <Card title="Fundamentals" testId="card-fundamentals">
          <p className="text-sm text-ink-3">{dossier.sections.fundamentals.note}</p>
        </Card>

        <Card title="Model insight — selected automatically" testId="card-model">
          {mi.status === "complete" && mi.winner ? (
            <>
              <p className="text-sm text-ink" data-testid="tournament-winner">
                {mi.winner.name}
                <span className="ml-2 rounded bg-surface-3 px-1.5 py-0.5 text-xs text-ink-2">
                  {mi.winner.kind}
                </span>
              </p>
              <p className="mt-2 text-xs text-ink-3">{mi.winner.rationale}</p>
              <details className="mt-3">
                <summary className="cursor-pointer text-sm text-ink-2">
                  Full scoreboard ({mi.candidates.length} candidates,{" "}
                  {mi.n_splits} walk-forward splits)
                </summary>
                <table className="mt-2 w-full text-left text-xs" data-testid="scoreboard">
                  <thead>
                    <tr className="text-ink-3">
                      <th className="py-1 pr-2 font-normal">candidate</th>
                      <th className="py-1 pr-2 font-normal">val sharpe</th>
                      <th className="py-1 pr-2 font-normal">train−val gap</th>
                      <th className="py-1 font-normal">score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mi.candidates.map((c) => (
                      <tr key={c.key} className="text-ink-2">
                        <td className="py-1 pr-2">{c.name}</td>
                        <td className="py-1 pr-2">{c.val_sharpe.toFixed(2)}</td>
                        <td className="py-1 pr-2">{c.divergence.toFixed(2)}</td>
                        <td className="py-1">{c.score.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="mt-2 text-xs text-ink-3">
                  Scores are validation Sharpe minus an overfitting-divergence
                  penalty and a multiple-testing deflation of{" "}
                  {mi.deflation_penalty}. Ties favor simpler models.
                </p>
              </details>
              <p className="mt-3 text-xs text-ink-3" data-testid="rl-status">
                RL candidates: {mi.rl.status.replaceAll("_", " ")} — {mi.rl.note}
              </p>
            </>
          ) : (
            <p className="text-sm text-caution" data-testid="tournament-insufficient">
              {mi.note ?? "Model tournament unavailable for this ticker."}
            </p>
          )}
        </Card>
      </div>

      <p className="text-xs text-ink-3" data-testid="disclaimers">
        {dossier.disclaimers.join(" ")}
      </p>
    </div>
  );
}

