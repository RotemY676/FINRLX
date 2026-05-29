"use client";

import { useState } from "react";

/**
 * Single-ticker deep analysis wizard.
 *
 * Calls GET /api/v1/analysis/single-ticker?ticker=XXX, which returns a
 * self-contained HTML document. The HTML is embedded via `srcDoc` so it
 * isn't subject to the backend's X-Frame-Options:DENY and works
 * cross-origin (Vercel frontend → Railway backend).
 */
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

interface ResultMeta {
  ticker: string;
  durationMs: number;
}

export default function AnalyzePage() {
  const [ticker, setTicker] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [html, setHtml] = useState<string | null>(null);
  const [meta, setMeta] = useState<ResultMeta | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    const sym = ticker.toUpperCase().trim();
    if (!sym) {
      setError("Please enter a ticker symbol.");
      return;
    }
    setRunning(true);
    setError(null);
    setHtml(null);
    setMeta(null);
    try {
      const url = `${API_BASE}/api/v1/analysis/single-ticker?ticker=${encodeURIComponent(sym)}`;
      const resp = await fetch(url);
      const durationMs = parseInt(
        resp.headers.get("x-analysis-duration-ms") || "0",
        10,
      );
      const respTicker = resp.headers.get("x-analysis-ticker") || sym;
      if (!resp.ok) {
        const body = await resp.text();
        let detail = body;
        try {
          const json = JSON.parse(body);
          detail = json.detail || body;
        } catch {
          /* not JSON */
        }
        setError(
          `Analysis failed (HTTP ${resp.status}): ${String(detail).slice(0, 300)}`,
        );
        return;
      }
      const text = await resp.text();
      setHtml(text);
      setMeta({ ticker: respTicker, durationMs });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`Network error: ${msg}`);
    } finally {
      setRunning(false);
    }
  }

  function downloadHtml() {
    if (!html || !meta) return;
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const ts = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 19);
    a.href = url;
    a.download = `finrlx_analysis_${meta.ticker}_${ts}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
      <header className="mb-6">
        <h1 className="text-page-title text-ink">
          Single-ticker deep analysis
        </h1>
        <p className="mt-2 text-body-sm text-ink-3">
          Runs the FINRLX engine ensemble (technical_momentum, risk_quality,
          news_sentiment), a 7-strategy walk-forward backtest, and VADER news
          sentiment for any ticker. The pipeline is the same one used by{" "}
          <code className="rounded bg-surface-3 px-1.5 py-0.5 font-mono text-meta">
            scripts/analyze_ticker.py
          </code>{" "}
          locally. Takes ~5–10 seconds per ticker.
        </p>
      </header>

      <form
        onSubmit={run}
        className="mb-6 flex flex-col gap-3 rounded-lg border border-line bg-surface-2 p-5 sm:flex-row sm:items-center"
      >
        <label
          htmlFor="ticker"
          className="text-body-sm font-medium text-ink-2 sm:w-40 sm:flex-shrink-0"
        >
          Ticker symbol
        </label>
        <input
          id="ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="e.g. UMC, NVDA, AAPL, BRK.B"
          autoComplete="off"
          autoFocus
          maxLength={10}
          disabled={running}
          className="flex-1 rounded-md border border-line bg-surface px-4 py-2 text-body text-ink placeholder:text-ink-4 focus:border-primary focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={running || !ticker.trim()}
          className="rounded-md bg-primary px-6 py-2 text-body font-semibold text-primary-ink hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? "Analyzing…" : "Run analysis"}
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded-md border border-breach bg-breach-soft p-4 text-body-sm text-breach-soft-ink">
          {error}
        </div>
      )}

      {running && !html && (
        <div className="rounded-lg border border-line bg-surface-2 p-12 text-center">
          <div className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <div className="text-body-sm text-ink-3">
            Fetching prices and news · computing features · running 7
            strategies × ~52 weekly rebalances · ~5–10s
          </div>
        </div>
      )}

      {html && meta && (
        <>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-md border border-line bg-surface-2 px-4 py-3 text-body-sm">
            <span className="text-ink-3">
              Report for{" "}
              <strong className="text-ink">{meta.ticker}</strong> generated in{" "}
              {(meta.durationMs / 1000).toFixed(1)}s
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={downloadHtml}
                className="rounded-md border border-line bg-surface px-3 py-1.5 text-meta font-medium text-ink-2 hover:bg-surface-3"
              >
                ↓ Download .html
              </button>
              <span className="text-meta text-ink-4">
                Self-contained · email-safe
              </span>
            </div>
          </div>
          <iframe
            srcDoc={html}
            title={`FINRLX analysis ${meta.ticker}`}
            sandbox="allow-scripts allow-popups"
            className="block w-full rounded-lg border border-line bg-surface"
            style={{ height: "calc(100vh - 320px)", minHeight: 600 }}
          />
        </>
      )}

      {!html && !running && !error && (
        <div className="rounded-lg border border-dashed border-line bg-surface p-12 text-center text-body-sm text-ink-3">
          Enter a ticker and click <strong>Run analysis</strong> to generate
          the report. Each run pulls live yfinance data, so subsequent runs
          for the same ticker pick up new bars and news as they print.
        </div>
      )}
    </div>
  );
}
