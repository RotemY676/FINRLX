"use client";

/**
 * LEAP S5 — Simple Mode: The One Screen (SIMPLE_MODE_SPEC J0-J5).
 *
 * Ships at /simple first; S7 flips it to `/` when the Pro migration moves
 * today's command-center Home to /pro (sequencing per Decision D26).
 * Replaces the pre-S1 vertical slice, which rendered the payload's raw
 * engine stance vocabulary — the exact violation the S1 council caught;
 * all stance rendering now goes through the lib/simpleStance boundary.
 *
 * Honesty note (spec J1, binding): the dossier endpoint is one blocking GET,
 * so the stage list is *indicative* (client-timed pacing) — it never fakes
 * per-stage completion. Real per-stage progress is DEBT-S5-1.
 */

import { useEffect, useRef, useState } from "react";

import {
  DegradedBanner,
  DisclaimerStrip,
  DossierPriceChart,
  SummaryBar,
  VerdictCards,
  type DossierPayload,
} from "@/components/simple/DossierView";
import { track } from "@/lib/analytics";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

const STAGES = [
  "Fetching price history",
  "Reading recent news",
  "Computing technical signals",
  "Running the model tournament",
  "Assembling your dossier",
] as const;

type ViewState =
  | { kind: "hero" }
  | { kind: "loading"; ticker: string; startedAt: number }
  | { kind: "dossier"; dossier: DossierPayload }
  | { kind: "nodata"; ticker: string }
  | { kind: "error"; ticker: string };

interface AssetSuggestion {
  ticker: string;
  name?: string | null;
}

export default function SimpleModePage() {
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState<AssetSuggestion[]>([]);
  const [state, setState] = useState<ViewState>({ kind: "hero" });
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (state.kind === "loading") {
      timerRef.current = setInterval(
        () => setElapsed((Date.now() - state.startedAt) / 1000),
        250,
      );
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }
    setElapsed(0);
    return undefined;
  }, [state]);

  async function research(rawTicker: string) {
    const ticker = rawTicker.trim().toUpperCase();
    if (!ticker) return;
    const startedAt = Date.now();
    setState({ kind: "loading", ticker, startedAt });
    void track("leap.simple_ticker_submitted");
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/autopilot/dossier?ticker=${encodeURIComponent(ticker)}`,
      );
      if (res.status === 400 || res.status === 502) {
        setState({ kind: "nodata", ticker });
        return;
      }
      if (!res.ok) {
        setState({ kind: "error", ticker });
        return;
      }
      const body = (await res.json()) as { data: DossierPayload };
      setState({ kind: "dossier", dossier: body.data });
      void track("leap.dossier_rendered", {
        ms: Date.now() - startedAt,
        cached: Boolean(body.data.served_from_cache || body.data.served_from_persistence),
      });
    } catch {
      setState({ kind: "error", ticker });
    }
  }

  useEffect(() => {
    // Autocomplete via the Phase 20.3 asset-search endpoint; suggestions are
    // an assist, never a gate — any typed ticker submits.
    const q = input.trim();
    if (state.kind !== "hero" || q.length < 1) {
      setSuggestions([]);
      return;
    }
    const ctl = new AbortController();
    const t = setTimeout(async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/v1/assets?q=${encodeURIComponent(q)}`,
          { signal: ctl.signal },
        );
        if (!res.ok) return;
        const body = (await res.json()) as { data?: AssetSuggestion[] };
        setSuggestions((body.data ?? []).slice(0, 5));
      } catch {
        /* suggestions are best-effort */
      }
    }, 200);
    return () => {
      ctl.abort();
      clearTimeout(t);
    };
  }, [input, state.kind]);

  /* Indicative pacing — explicitly not a claim of backend progress. */
  const indicativeStage = Math.min(Math.floor(elapsed / 1.2), STAGES.length - 1);

  return (
    <div className="mx-auto max-w-5xl space-y-4 px-4 py-8">
      {state.kind === "hero" && (
        <section className="py-16 text-center">
          <h1 className="mb-5 text-2xl font-bold text-ink">Research any stock</h1>
          <form
            className="mx-auto flex max-w-md gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              void research(input);
            }}
          >
            <input
              autoFocus
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Try NVDA"
              aria-label="Stock ticker"
              className="w-full rounded-lg border border-line-strong bg-surface px-4 py-3 text-lg text-ink"
            />
            <button
              type="submit"
              className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-ink"
            >
              Research
            </button>
          </form>
          {suggestions.length > 0 && (
            <ul className="mx-auto mt-2 max-w-md rounded-lg border border-line bg-surface text-left text-sm">
              {suggestions.map((sug) => (
                <li key={sug.ticker}>
                  <button
                    type="button"
                    className="w-full px-3 py-2 text-left hover:bg-surface-2"
                    onClick={() => void research(sug.ticker)}
                  >
                    <span className="font-medium">{sug.ticker}</span>
                    {sug.name ? <span className="text-ink-2"> — {sug.name}</span> : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <p className="mx-auto mt-4 max-w-lg text-sm text-ink-2">
            Automatic 360° research: prices, news, technicals, and a model tournament —
            with the evidence for every conclusion.
          </p>
          <p className="mt-8 text-xs text-ink-4">
            Research analysis, not investment advice.
          </p>
        </section>
      )}

      {state.kind === "loading" && (
        <section aria-live="polite" className="mx-auto max-w-md py-16">
          <p className="mb-3 text-sm text-ink-2">
            <span className="font-semibold text-ink">{state.ticker}</span> —
            researching… {elapsed.toFixed(1)}s
          </p>
          <ol className="space-y-1 text-sm">
            {STAGES.map((stage, i) => (
              <li
                key={stage}
                className={
                  i < indicativeStage
                    ? "text-ink-2"
                    : i === indicativeStage
                      ? "font-medium text-ink"
                      : "text-ink-4"
                }
              >
                {i < indicativeStage ? "✓ " : i === indicativeStage ? "… " : "○ "}
                {stage}
              </li>
            ))}
          </ol>
          {elapsed > 20 && (
            <p className="mt-3 text-xs text-ink-2">
              First-time research for a ticker takes longer; results are cached afterward.
            </p>
          )}
        </section>
      )}

      {state.kind === "dossier" && (
        <>
          <SummaryBar dossier={state.dossier} />
          <DegradedBanner dossier={state.dossier} />
          <VerdictCards dossier={state.dossier} />
          <DossierPriceChart dossier={state.dossier} />
          <DisclaimerStrip disclaimers={state.dossier.disclaimers} />
          <button
            type="button"
            className="text-sm text-primary underline"
            onClick={() => {
              setInput("");
              setState({ kind: "hero" });
            }}
          >
            Research another stock
          </button>
        </>
      )}

      {state.kind === "nodata" && (
        <section className="mx-auto max-w-md py-16 text-center">
          <p className="font-semibold text-ink">
            No price data found for “{state.ticker}”.
          </p>
          <button
            type="button"
            className="mt-4 text-sm text-primary underline"
            onClick={() => setState({ kind: "hero" })}
          >
            Try another ticker
          </button>
        </section>
      )}

      {state.kind === "error" && (
        <section className="mx-auto max-w-md py-16 text-center">
          <p className="font-semibold text-ink">
            Research is temporarily unavailable.
          </p>
          <p className="mt-1 text-sm text-ink-2">
            Your ticker is kept — retry when ready.
          </p>
          <button
            type="button"
            className="mt-4 rounded-lg border border-line-strong px-4 py-2 text-sm"
            onClick={() => void research(state.ticker)}
          >
            Retry {state.ticker}
          </button>
        </section>
      )}
    </div>
  );
}
