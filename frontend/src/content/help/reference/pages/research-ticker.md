---
title: Research workspace (per ticker)
summary: The per-name research page combining price, news, fundamentals, peers, uploaded documents, and AI-generated quarterly insights.
diataxis: reference
area: reference
updated: 2026-05-22
order: 114
---

When you click a ticker on the [Research hub](/help/reference/pages/research), you land on its dedicated workspace at `/research/[ticker]` (e.g. `/research/NVDA`). This is the single screen that combines everything FINRLX knows about a name.

## Panels on this page

The panels render top-down, each appearing as its data backend responds. Slow panels don't block fast ones — the page is usable while later sections are still loading.

### 1. Price chart

Real OHLC bars from the backend's `/api/v1/pricechart` endpoint. Handles empty-coverage tickers gracefully (the card shows an empty-state note when the backend has no data for the symbol).

### 2. News mentions

A filtered slice of the global news feed — entries whose title or summary mentions the ticker (word-boundary match). Sentiment chip on each row. Sourced from the same RSS aggregator that powers the [News page](/help/reference/pages/news); no ticker-specific feed.

### 3. Fundamentals + peers (feature-flagged)

Two side-by-side panels for valuation snapshot + sector peer comparison. Both honor their feature flags — when the flag is off OR the upstream provider (Finnhub) is unconfigured, each panel renders an honest "configure provider" empty state rather than fake data.

### 4. SEC quarterly insights (auto-generated)

On mount, the panel runs an automatic flow for US-listed tickers:

1. **Fetches the last 6 quarterly filings** (10-Q + 10-K) from SEC EDGAR via the backend's `/api/v1/research/{ticker}/auto-ingest` endpoint. Sequential downloads honor SEC's fair-access policy (≤10 req/sec, real User-Agent).
2. **Synthesizes a cross-quarter analysis** by calling `/api/v1/research/{ticker}/insights`. The LLM (Gemini 2.5 Flash by default, with Anthropic fallback if configured) produces four sections:
   - **Headline metric trajectory** — 2–4 key metrics across quarters.
   - **Latest-quarter delta** — what changed in the most recent filing.
   - **Risk-factor changes** — new, modified, or removed risks vs the prior period.
   - **What to watch** — one paragraph on the next quarter.
3. **Renders the result** with a provenance footer (provider, model, token counts, list of accession numbers analyzed) and a decision-support disclaimer.

Insights are cached for 7 days. When older than that, the panel shows a "Stale" badge and a Refresh button.

For **non-US tickers** (LSE, TASE, foreign exchanges), the panel renders a clear "not in SEC's database" note rather than fake data — SEC coverage is the underlying limit, not a bug.

For ingestion failures (SEC unreachable, LLM provider chain exhausted, monthly budget exceeded), the panel surfaces the actual backend error verbatim with a Retry button. No silent failures.

### 5. Research documents (manual upload + Q&A)

Below the auto-generated insights, the [DocumentsPanel](/help/guides/upload-a-document) lets you upload your own filings (PDFs, transcripts) for ad-hoc LLM analysis. Uploaded documents and auto-fetched SEC filings share the same list; auto-fetched rows are tagged so you can tell them apart.

## What this page is not

- A trading or order screen. There is no buy/sell button here. The disclaimer on every insight card says it explicitly: decision support, not investment advice.
- A real-time feed. The price chart updates on backend refresh cadence; news refreshes on the aggregator's schedule; insights are explicitly time-shifted (auto-fetched filings can be days behind SEC's publishing time).

## Honest empty / unavailable states

- **Fundamentals/peers — "Configure provider"**: a Finnhub API key isn't set, or the upstream returned no coverage. Not a bug.
- **Price chart — "No data"**: the backend doesn't have bars for this symbol. Often means a low-coverage exchange.
- **Insights — "Not in SEC's database"**: the ticker isn't US-registered. Upload PDFs manually to still get LLM analysis.
- **Insights — "Could not generate insights"**: either SEC was unreachable, the LLM chain failed, or the monthly token budget was exceeded. The exact reason is shown.

## See also

- [Universe](/help/reference/pages/universe) — controls which tickers appear in the [Research hub](/help/reference/pages/research).
- [News](/help/reference/pages/news) — the unfiltered news feed.
- [Read cross-quarter insights](/help/guides/read-cross-quarter-insights) — interpreting the AI-generated output safely.
