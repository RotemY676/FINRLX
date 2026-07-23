"use client";

/**
 * Model lab — a dedicated, abstracted dashboard for comparing the models
 * behind a decision and reading one honest verdict.
 *
 * Every value here comes from the real walk-forward tournament in
 * `/autopilot/dossier` -> sections.model_insight. Nothing is simulated:
 *  - the candidates are the heuristic/ML strategies scored on real bars, plus
 *    RL agents (PPO/A2C) WHERE a research artifact exists for the ticker and
 *    matches the current walk-forward protocol;
 *  - the RL lane is shown honestly gated ("queued for the research worker")
 *    when no artifact is present, never with invented numbers;
 *  - the final verdict is a transparent rule (`model_decision.py`) over the
 *    real scores — and it reports "no active edge" when a passive benchmark
 *    wins, rather than dressing that up as a signal.
 *
 * Research language only; a hard "not advice" disclaimer is always shown.
 */

import { useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

/* ── payload shapes (subset of model_insight used here) ──────────────────── */

interface Candidate {
  key: string;
  name: string;
  kind: string; // heuristic | ml | benchmark | rl
  val_sharpe: number;
  train_sharpe: number;
  divergence: number;
  penalty: number;
  score: number;
  per_split_val_sharpe?: number[];
  imported_from_artifact?: boolean;
}

interface RlStatus {
  status: string; // artifact_merged | queued_for_research_run | artifact_rejected
  note?: string;
  recipe?: string;
  generated_at?: string;
  agents?: string[];
  reason?: string;
}

interface Verdict {
  verdict: "constructive" | "cautious" | "inconclusive";
  headline: string;
  reasons: string[];
  models_compared: number;
  winner_name: string | null;
  winner_score: number | null;
  winner_is_passive: boolean;
  rl_participated: boolean;
  disclaimer: string;
}

interface ModelInsight {
  status: string;
  n_splits: number;
  deflation_penalty: number;
  candidates: Candidate[];
  winner: (Candidate & { rationale?: string }) | null;
  rl: RlStatus;
  verdict: Verdict;
}

type View =
  | { kind: "idle" }
  | { kind: "loading"; ticker: string }
  | { kind: "ready"; ticker: string; insight: ModelInsight }
  | { kind: "nodata"; ticker: string }
  | { kind: "error"; ticker: string };

/* ── verdict tone ────────────────────────────────────────────────────────── */

function verdictTone(v: Verdict["verdict"]): string {
  if (v === "constructive") return "border-pos bg-pos-soft text-pos-soft-ink";
  if (v === "cautious") return "border-breach bg-breach-soft text-breach-soft-ink";
  return "border-caution bg-caution-soft text-caution-soft-ink";
}

function kindLabel(kind: string): string {
  return kind === "rl"
    ? "reinforcement learning"
    : kind === "ml"
      ? "machine learning"
      : kind === "benchmark"
        ? "passive benchmark"
        : "rule-based";
}

/* ── the verdict panel — the one honest read ─────────────────────────────── */

function VerdictPanel({ v }: { v: Verdict }) {
  return (
    <section
      data-testid="model-verdict"
      className={`rounded-lg border p-4 ${verdictTone(v.verdict)}`}
    >
      <div className="flex flex-wrap items-baseline gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide">
          {v.verdict.replace("_", " ")}
        </span>
        <span className="text-sm font-semibold">{v.headline}</span>
      </div>
      <ul className="mt-2 list-disc space-y-0.5 pl-5 text-sm">
        {v.reasons.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
      <div className="mt-2 flex flex-wrap gap-x-4 text-xs opacity-80">
        <span>{v.models_compared} models compared</span>
        {v.rl_participated && <span>RL agents competed</span>}
      </div>
      <p className="mt-2 text-xs opacity-80">{v.disclaimer}</p>
    </section>
  );
}

/* ── per-split consistency (reused idea from the dossier) ─────────────────── */

function SplitDots({ splits }: { splits?: number[] }) {
  if (!splits || splits.length === 0) return <span className="text-ink-4">—</span>;
  return (
    <span className="inline-flex gap-0.5" aria-hidden="true">
      {splits.map((s, i) => (
        <span
          key={i}
          title={`split ${i + 1}: ${s.toFixed(2)}`}
          className="inline-block h-3 w-3 rounded-sm text-center text-[8px] leading-3"
          style={{
            background: s > 0 ? "var(--pos)" : s < 0 ? "var(--breach)" : "var(--ink-4)",
            color: "var(--surface)",
          }}
        >
          {s > 0 ? "+" : s < 0 ? "−" : "·"}
        </span>
      ))}
    </span>
  );
}

/* ── RL lane status — honest gating ──────────────────────────────────────── */

function RlLaneBanner({ rl }: { rl: RlStatus }) {
  if (rl.status === "artifact_merged") {
    return (
      <div
        data-testid="rl-lane"
        className="rounded-lg border border-pos bg-pos-soft px-3 py-2 text-xs text-pos-soft-ink"
      >
        <strong>RL agents included.</strong> {(rl.agents ?? []).join(", ").toUpperCase()} from the
        research worker ({rl.recipe}), scored under the same walk-forward
        protocol and penalties as every other candidate.
      </div>
    );
  }
  if (rl.status === "artifact_rejected") {
    return (
      <div
        data-testid="rl-lane"
        className="rounded-lg border border-caution bg-caution-soft px-3 py-2 text-xs text-caution-soft-ink"
      >
        <strong>RL agents excluded ({rl.reason}).</strong> {rl.note}
      </div>
    );
  }
  return (
    <div
      data-testid="rl-lane"
      className="rounded-lg border border-line bg-surface-2 px-3 py-2 text-xs text-ink-2"
    >
      <strong>RL agents not yet trained for this ticker.</strong> {rl.note}
    </div>
  );
}

/* ── comparison table ────────────────────────────────────────────────────── */

function ComparisonTable({ insight }: { insight: ModelInsight }) {
  const winnerKey = insight.winner?.key;
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line bg-surface-2 text-left text-xs text-ink-2">
            <th className="px-3 py-2">Model</th>
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2 text-right">Validation Sharpe</th>
            <th className="px-3 py-2">Per-split</th>
            <th className="px-3 py-2 text-right">Penalty</th>
            <th className="px-3 py-2 text-right">Score</th>
          </tr>
        </thead>
        <tbody>
          {insight.candidates.map((c) => (
            <tr
              key={c.key}
              data-testid={`model-row-${c.key}`}
              className={`border-t border-line ${c.key === winnerKey ? "bg-pos-soft/40" : ""}`}
            >
              <td className="px-3 py-2">
                <span className="font-medium text-ink">{c.name}</span>
                {c.key === winnerKey && (
                  <span className="ml-2 rounded bg-pos-soft px-1.5 text-[10px] text-pos-soft-ink">
                    selected
                  </span>
                )}
                {c.imported_from_artifact && (
                  <span
                    className="ml-2 rounded border border-line px-1.5 text-[10px] text-ink-2"
                    title="trained in the isolated research worker"
                  >
                    research artifact
                  </span>
                )}
              </td>
              <td className="px-3 py-2 text-xs text-ink-2">{kindLabel(c.kind)}</td>
              <td className="px-3 py-2 text-right font-mono">{c.val_sharpe.toFixed(2)}</td>
              <td className="px-3 py-2"><SplitDots splits={c.per_split_val_sharpe} /></td>
              <td className="px-3 py-2 text-right font-mono text-ink-4">{c.penalty.toFixed(3)}</td>
              <td className="px-3 py-2 text-right font-mono font-semibold">{c.score.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── the screen ──────────────────────────────────────────────────────────── */

export function ModelLab() {
  const [input, setInput] = useState("");
  const [view, setView] = useState<View>({ kind: "idle" });

  async function compare(raw: string) {
    const ticker = raw.trim().toUpperCase();
    if (!ticker) return;
    setView({ kind: "loading", ticker });
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/autopilot/dossier?ticker=${encodeURIComponent(ticker)}`,
      );
      if (res.status === 400 || res.status === 502) {
        setView({ kind: "nodata", ticker });
        return;
      }
      if (!res.ok) {
        setView({ kind: "error", ticker });
        return;
      }
      const body = await res.json();
      const insight: ModelInsight | undefined = body?.data?.sections?.model_insight;
      if (!insight || insight.status !== "complete") {
        setView({ kind: "nodata", ticker });
        return;
      }
      setView({ kind: "ready", ticker, insight });
    } catch {
      setView({ kind: "error", ticker });
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4 px-4 py-6" data-testid="model-lab">
      <header>
        <h1 className="text-xl font-semibold text-ink">Model lab</h1>
        <p className="mt-1 text-sm text-ink-2">
          Compare every model behind a decision on the same walk-forward
          validation, and read one honest verdict. Research analysis, not
          investment advice.
        </p>
      </header>

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void compare(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ticker (e.g. AAPL)"
          aria-label="Ticker"
          className="w-full rounded-lg border border-line-strong bg-surface px-4 py-3 text-ink"
        />
        <button
          type="submit"
          className="min-h-11 rounded-lg bg-primary px-5 font-semibold text-primary-ink"
        >
          Compare
        </button>
      </form>

      {view.kind === "loading" && (
        <p className="py-10 text-center text-sm text-ink-2" aria-live="polite">
          Running the model tournament for {view.ticker}… this trains and
          walk-forward validates every candidate on real bars (~5–10s).
        </p>
      )}

      {view.kind === "ready" && (
        <>
          <VerdictPanel v={view.insight.verdict} />
          <RlLaneBanner rl={view.insight.rl} />
          <ComparisonTable insight={view.insight} />
          <p className="text-xs text-ink-4">
            {view.insight.n_splits} walk-forward splits · multiple-testing
            deflation penalty {view.insight.deflation_penalty} applied to every
            candidate. {view.insight.winner?.rationale}
          </p>
          <button
            type="button"
            className="text-sm text-primary underline"
            onClick={() => {
              setInput("");
              setView({ kind: "idle" });
            }}
          >
            Compare another ticker
          </button>
        </>
      )}

      {view.kind === "nodata" && (
        <p className="py-10 text-center text-sm text-ink-2">
          Not enough history to validate models for “{view.ticker}”.
        </p>
      )}
      {view.kind === "error" && (
        <p className="py-10 text-center text-sm text-ink-2">
          The comparison is temporarily unavailable — retry when ready.
        </p>
      )}
    </div>
  );
}
