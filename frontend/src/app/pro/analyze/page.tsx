"use client";

import { useEffect, useRef, useState } from "react";

import { getAccessToken } from "@/services/auth";

/**
 * Single-ticker deep analysis wizard.
 *
 * Calls GET /api/v1/analysis/single-ticker?ticker=XXX, which returns a
 * self-contained HTML document. The HTML is embedded via `srcDoc` so it
 * isn't subject to the backend's X-Frame-Options:DENY and works
 * cross-origin (Vercel frontend → Railway backend).
 *
 * Mobile sizing: AppShell adds ~112px of chrome (AppBar 64 + ContextStrip 48)
 * plus ~40px disclaimer + ~32px page padding ≈ 184px. The iframe uses
 * `100svh - 12rem` (192px) on phone to never overflow and `100dvh` so the
 * height tracks iOS Safari URL-bar collapse/expand.
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
  const resultRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Once the iframe is in the DOM after a successful run, scroll the
    // result block into view so phone users don't have to hunt for it.
    if (html && meta && resultRef.current) {
      requestAnimationFrame(() => {
        resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }, [html, meta]);

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
      // Raw fetch (the response is an HTML document, not the ApiResponse
      // envelope apiFetch expects), so the session bearer is attached by hand.
      // US-P0-03 gates this route: it runs a 7-strategy walk-forward backtest
      // and costs 5-10s of real compute per call.
      const token = getAccessToken();
      const resp = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
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

  function openInNewTab() {
    if (!html) return;
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const blobUrl = URL.createObjectURL(blob);
    window.open(blobUrl, "_blank", "noopener,noreferrer");
    // Defer revoke so the new tab has time to read it.
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-4 md:px-8 md:py-8">
      {/* Header: compact on phone, full on md+ */}
      <header className="mb-4 md:mb-6">
        <h1 className="text-section-title text-ink md:text-page-title">
          Single-ticker deep analysis
        </h1>

        {/* Desktop: full descriptive paragraph */}
        <p className="mt-2 hidden text-body-sm text-ink-3 md:block">
          Runs the FINRLX engine ensemble (technical_momentum, risk_quality,
          news_sentiment), a 7-strategy walk-forward backtest, and VADER news
          sentiment for any ticker. The pipeline is the same one used by{" "}
          <code className="rounded bg-surface-3 px-1.5 py-0.5 font-mono text-meta">
            scripts/analyze_ticker.py
          </code>{" "}
          locally. Takes ~5–10 seconds per ticker.
        </p>

        {/* Mobile: one-liner + collapsible details */}
        <p className="mt-1 text-body-sm text-ink-3 md:hidden">
          Ensemble + 7-strategy backtest. ~5–10s per ticker.
        </p>
        <details className="mt-2 md:hidden">
          <summary className="cursor-pointer text-meta text-ink-3 underline decoration-line">
            More info
          </summary>
          <p className="mt-2 text-body-sm text-ink-3">
            Runs technical_momentum, risk_quality, news_sentiment, a walk-forward
            backtest, and VADER news sentiment. Same pipeline as{" "}
            <code className="rounded bg-surface-3 px-1 py-0.5 font-mono text-meta">
              scripts/analyze_ticker.py
            </code>
            .
          </p>
        </details>
      </header>

      {/* Form: stack on phone, row on md+. 44px+ touch targets. */}
      <form
        onSubmit={run}
        className="mb-4 flex flex-col gap-3 rounded-lg border border-line bg-surface-2 p-4 md:mb-6 md:flex-row md:items-center md:p-5"
      >
        <label
          htmlFor="ticker"
          className="text-body-sm font-medium text-ink-2 md:w-40 md:flex-shrink-0"
        >
          Ticker symbol
        </label>
        <input
          id="ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="e.g. UMC, NVDA, AAPL"
          autoComplete="off"
          autoCapitalize="characters"
          autoFocus
          maxLength={10}
          disabled={running}
          inputMode="text"
          className="min-h-11 w-full flex-1 rounded-md border border-line bg-surface px-4 py-2 text-body text-ink placeholder:text-ink-4 focus:border-primary focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={running || !ticker.trim()}
          className="min-h-11 w-full rounded-md bg-primary px-6 py-2 text-body font-semibold text-primary-ink hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
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
        <div className="rounded-lg border border-line bg-surface-2 p-6 text-center md:p-12">
          <div className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <div className="text-body-sm text-ink-3">
            <span className="md:hidden">Running pipeline · ~5–10s…</span>
            <span className="hidden md:inline">
              Fetching prices and news · computing features · running 7
              strategies × ~52 weekly rebalances · ~5–10s
            </span>
          </div>
        </div>
      )}

      {html && meta && (
        <div ref={resultRef} className="scroll-mt-4">
          {/* Meta bar: stacks on phone, row on md+ */}
          <div className="mb-3 flex flex-col gap-3 rounded-md border border-line bg-surface-2 px-4 py-3 text-body-sm md:flex-row md:flex-wrap md:items-center md:justify-between">
            <span className="text-ink-3">
              Report for <strong className="text-ink">{meta.ticker}</strong>{" "}
              generated in {(meta.durationMs / 1000).toFixed(1)}s
            </span>

            <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
              <div className="flex gap-2">
                <button
                  onClick={downloadHtml}
                  className="min-h-11 flex-1 rounded-md border border-line bg-surface px-3 py-2 text-meta font-medium text-ink-2 hover:bg-surface-3 md:flex-none md:py-1.5"
                >
                  ↓ Download .html
                </button>
                <button
                  onClick={openInNewTab}
                  className="min-h-11 flex-1 rounded-md border border-line bg-surface px-3 py-2 text-meta font-medium text-ink-2 hover:bg-surface-3 md:flex-none md:py-1.5"
                >
                  ↗ Open in new tab
                </button>
              </div>
              <span className="text-meta text-ink-4">
                Self-contained · email-safe
              </span>
            </div>
          </div>

          {/* iframe: dynamic viewport, no fixed minHeight on phone.
              On mobile: 100svh - 12rem covers AppBar(64) + ContextStrip(48)
              + disclaimer(~40) + padding(~32). On desktop: 100dvh - 20rem
              with a 600px floor for a comfortable report view. */}
          <iframe
            srcDoc={html}
            title={`FINRLX analysis ${meta.ticker}`}
            sandbox="allow-scripts allow-popups"
            className="block h-[calc(100svh-12rem)] w-full rounded-lg border border-line bg-surface md:h-[calc(100dvh-20rem)] md:min-h-[600px]"
          />
        </div>
      )}

      {!html && !running && !error && (
        <div className="rounded-lg border border-dashed border-line bg-surface p-6 text-center text-body-sm text-ink-3 md:p-12">
          {/* Desktop copy */}
          <p className="hidden md:block">
            Enter a ticker and click <strong>Run analysis</strong> to generate
            the report. Each run pulls live yfinance data, so subsequent runs
            for the same ticker pick up new bars and news as they print.
          </p>
          {/* Mobile: shorter copy + tap-to-fill chips */}
          <p className="md:hidden">Tap a ticker to start:</p>
          <div className="mt-3 flex flex-wrap justify-center gap-2 md:hidden">
            {["UMC", "NVDA", "AAPL"].map((sym) => (
              <button
                key={sym}
                type="button"
                onClick={() => setTicker(sym)}
                className="min-h-11 rounded-md border border-line bg-surface-2 px-4 py-2 text-body font-semibold text-ink-2 hover:bg-surface-3"
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
