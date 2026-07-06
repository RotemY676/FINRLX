"use client";

/**
 * LEAP S6 — Compare (SIMPLE_MODE_SPEC J3).
 * 2-4 tickers side by side on the shared dossier dimensions from
 * GET /api/v1/autopilot/compare. Divergence markers carry measured values,
 * never judgments. v1 progress is one combined state (blocking endpoint —
 * DEBT-S5-1); per-ticker failures render in-column, others unaffected.
 * Raw payload stance words map through the lib/simpleStance boundary.
 */

import { useState } from "react";

import { Chip } from "@/components/simple/DossierView";
import { track } from "@/lib/analytics";
import { STANCE_HOVER_LABEL, stanceTone, toSimpleStance } from "@/lib/simpleStance";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

interface CompareColumn {
  ticker: string;
  latest_bar_date: string | null;
  stance: string | null;
  regime: string | null;
  composite_score: number | null;
  news_counts_7d: Record<string, number> | null;
  news_available: boolean | null;
  selected_model: string | null;
  selected_model_kind: string | null;
  selected_model_score: number | null;
  validation_sharpe: number | null;
}

interface ComparePayload {
  tickers: string[];
  columns: CompareColumn[];
  errors: Record<string, string>;
  divergence_highlights: Array<{ dimension: string; values: Record<string, unknown> }>;
  disclaimers: string[];
}

type ViewState =
  | { kind: "input" }
  | { kind: "loading"; tickers: string[] }
  | { kind: "result"; data: ComparePayload }
  | { kind: "error" };

function kindLabel(kind: string | null): string {
  if (!kind) return "—";
  return kind === "ml" ? "machine-learning" : "rule-based";
}

export default function ComparePage() {
  const [raw, setRaw] = useState("");
  const [state, setState] = useState<ViewState>({ kind: "input" });

  async function runCompare() {
    const tickers = raw
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter(Boolean);
    if (tickers.length < 2 || tickers.length > 4) return;
    setState({ kind: "loading", tickers });
    void track("leap.compare_started", { n: tickers.length });
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/autopilot/compare?tickers=${encodeURIComponent(tickers.join(","))}`,
      );
      if (!res.ok) {
        setState({ kind: "error" });
        return;
      }
      const body = (await res.json()) as { data: ComparePayload };
      setState({ kind: "result", data: body.data });
    } catch {
      setState({ kind: "error" });
    }
  }

  const diverges = (data: ComparePayload, dim: string) =>
    data.divergence_highlights.some((h) => h.dimension === dim);

  return (
    <main className="mx-auto max-w-5xl space-y-4 px-4 py-8">
      <h1 className="text-xl font-bold text-[var(--ink)]">Compare</h1>

      {(state.kind === "input" || state.kind === "error") && (
        <section className="max-w-md">
          <label htmlFor="cmp" className="text-sm text-[var(--ink-2)]">
            Add tickers (2-4), comma-separated
          </label>
          <form
            className="mt-1 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              void runCompare();
            }}
          >
            <input
              id="cmp"
              value={raw}
              onChange={(e) => setRaw(e.target.value)}
              placeholder="NVDA, AMD"
              className="w-full rounded-lg border border-[var(--line-strong)] bg-[var(--surface)] px-3 py-2 text-[var(--ink)]"
            />
            <button
              type="submit"
              className="rounded-lg bg-[var(--primary)] px-4 py-2 font-semibold text-[var(--primary-ink)]"
            >
              Compare
            </button>
          </form>
          {state.kind === "error" && (
            <p className="mt-3 text-sm text-[var(--ink)]">
              Comparison is temporarily unavailable. Your tickers are kept — retry when
              ready.
            </p>
          )}
        </section>
      )}

      {state.kind === "loading" && (
        <section aria-live="polite" className="py-12 text-sm text-[var(--ink-2)]">
          Building dossiers for {state.tickers.join(", ")}… First-time tickers take
          longer; results are cached afterward.
        </section>
      )}

      {state.kind === "result" && (
        <section className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="text-left text-[var(--ink-2)]">
                <th className="py-2 pr-3 font-medium">Dimension</th>
                {state.data.tickers.map((t) => (
                  <th key={t} className="py-2 pr-3 font-semibold text-[var(--ink)]">
                    {t}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <Row
                label="Research stance"
                diverged={diverges(state.data, "stance")}
                data={state.data}
                render={(c) => {
                  const s = toSimpleStance(c.stance);
                  return (
                    <Chip tone={stanceTone(s)} title={STANCE_HOVER_LABEL}>
                      {s}
                    </Chip>
                  );
                }}
              />
              <Row
                label="Regime"
                diverged={diverges(state.data, "regime")}
                data={state.data}
                render={(c) => c.regime ?? "—"}
              />
              <Row
                label="Composite score"
                data={state.data}
                render={(c) =>
                  typeof c.composite_score === "number" ? c.composite_score.toFixed(2) : "—"
                }
              />
              <Row
                label="Selected model"
                diverged={diverges(state.data, "selected_model")}
                data={state.data}
                render={(c) =>
                  c.selected_model ? `${c.selected_model} (${kindLabel(c.selected_model_kind)})` : "—"
                }
              />
              <Row
                label="Validation Sharpe"
                diverged={diverges(state.data, "validation_sharpe_spread")}
                data={state.data}
                render={(c) =>
                  typeof c.validation_sharpe === "number" ? c.validation_sharpe.toFixed(2) : "—"
                }
              />
              <Row
                label="Data through"
                data={state.data}
                render={(c) => c.latest_bar_date ?? "—"}
              />
            </tbody>
          </table>
          <p className="mt-2 text-xs text-[var(--ink-4)]">
            ◆ marks dimensions where the tickers differ — values shown are measured, side
            by side.
          </p>
          <div className="mt-3 border-t border-[var(--line)] pt-2 text-xs text-[var(--ink-2)]">
            {state.data.disclaimers.map((d) => (
              <p key={d}>{d}</p>
            ))}
          </div>
          <button
            type="button"
            className="mt-3 text-sm text-[var(--primary)] underline"
            onClick={() => setState({ kind: "input" })}
          >
            Compare different tickers
          </button>
        </section>
      )}
    </main>
  );
}

function Row({
  label,
  data,
  render,
  diverged = false,
}: {
  label: string;
  data: ComparePayload;
  render: (c: CompareColumn) => React.ReactNode;
  diverged?: boolean;
}) {
  const byTicker = new Map(data.columns.map((c) => [c.ticker, c]));
  return (
    <tr className="border-t border-[var(--line)]">
      <td className="py-2 pr-3 text-[var(--ink-2)]">
        {label} {diverged && <span aria-label="tickers differ on this dimension">◆</span>}
      </td>
      {data.tickers.map((t) => {
        const col = byTicker.get(t);
        if (!col) {
          return (
            <td key={t} className="py-2 pr-3 text-[var(--ink-2)]">
              Couldn&apos;t build this dossier: {data.errors[t] ?? "unavailable"}
            </td>
          );
        }
        return (
          <td key={t} className="py-2 pr-3 text-[var(--ink)]">
            {render(col)}
          </td>
        );
      })}
    </tr>
  );
}
