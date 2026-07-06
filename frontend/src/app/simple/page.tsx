"use client";

import { useState } from "react";
import { DossierView, type Dossier } from "./DossierView";

/**
 * PROGRAM LEAP S5 — The One Screen (Simple Mode vertical slice).
 * Type a ticker, get a 360-degree research dossier. Zero configuration
 * (D32); everything automatic and everything explained (D37); research
 * analysis, not advice (D30).
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

const STAGE_LABELS = [
  "Fetching price history…",
  "Reading recent news and sentiment…",
  "Computing technical vocabulary…",
  "Running the model tournament…",
  "Assembling your dossier…",
];

export default function SimplePage() {
  const [ticker, setTicker] = useState("");
  const [running, setRunning] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    const sym = ticker.toUpperCase().trim();
    if (!sym) {
      setError("Enter a ticker symbol to begin.");
      return;
    }
    setRunning(true);
    setError(null);
    setDossier(null);
    setStageIdx(0);
    const stageTimer = setInterval(
      () => setStageIdx((i) => Math.min(i + 1, STAGE_LABELS.length - 1)),
      2500,
    );
    try {
      const resp = await fetch(
        `${API_BASE}/api/v1/autopilot/dossier?ticker=${encodeURIComponent(sym)}`,
      );
      if (!resp.ok) {
        const body = await resp.json().catch(() => null);
        throw new Error(body?.detail || `Request failed (${resp.status})`);
      }
      const body = await resp.json();
      setDossier(body.data as Dossier);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      clearInterval(stageTimer);
      setRunning(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-2xl font-semibold text-ink">Research any stock</h1>
      <p className="mt-1 text-sm text-ink-2">
        Type a ticker. FINRLX runs the full 360° research pipeline —
        prices, news, technicals, and an automatic model tournament — and
        explains everything it finds. No settings, no setup.
      </p>

      <form onSubmit={run} className="mt-5 flex gap-2">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="e.g. NVDA"
          aria-label="Stock ticker symbol"
          className="w-40 rounded-lg border border-line bg-surface px-3 py-2 text-lg uppercase text-ink outline-none focus:border-accent"
          maxLength={10}
          data-testid="ticker-input"
        />
        <button
          type="submit"
          disabled={running}
          className="rounded-lg bg-primary px-5 py-2 text-lg font-medium text-primary-ink disabled:opacity-50"
          data-testid="run-button"
        >
          {running ? "Researching…" : "Research"}
        </button>
      </form>

      {running && (
        <div className="mt-6 rounded-xl border border-line bg-surface p-4" data-testid="progress" aria-live="polite">
          <p className="text-sm text-ink-2">{STAGE_LABELS[stageIdx]}</p>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded bg-surface-3">
            <div
              className="h-full bg-accent transition-all duration-700"
              style={{ width: `${((stageIdx + 1) / STAGE_LABELS.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {error && (
        <p className="mt-6 rounded-lg bg-breach-soft p-3 text-sm text-breach" data-testid="error">
          {error}
        </p>
      )}

      {dossier && <DossierView dossier={dossier} />}
    </main>
  );
}
