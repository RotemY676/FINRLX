---
title: Read cross-quarter insights safely
summary: How to interpret the AI-generated SEC trajectory analysis on a ticker page without misreading it as advice.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 50
---

The Insights panel on `/research/[ticker]` synthesizes the last 6 quarterly filings into a structured report. This guide is about reading it well — what to trust, what to verify, what to ignore.

## What you're looking at

The panel auto-fetches the last 6 quarterly filings (10-Q + 10-K) from SEC EDGAR, sends them to an LLM (Gemini 2.5 Flash by default), and asks for four things:

1. **Headline metric trajectory** — 2–4 key metrics tracked across quarters.
2. **Latest-quarter delta** — what changed in the most recent filing vs prior periods.
3. **Risk-factor changes** — new, modified, or removed risks.
4. **What to watch** — one paragraph on the next quarter.

The output is cached for 7 days. Click "Refresh" to regenerate against the latest filings.

## What to trust

- **Direct quotes from the filings.** The system prompt explicitly tells the model to use only the text provided. Quoted numbers like `"Revenue was $35,082M"` should match the source filing.
- **Accession numbers cited inline.** The footer lists every accession analyzed. You can click through to SEC's original document to verify.
- **The provider + model label.** Provenance is displayed in the footer (e.g. "gemini · gemini-2.5-flash · 120,000 in / 800 out tokens"). The same insight produced by different models may read differently.

## What to verify

- **Anything that sounds like a forecast.** Phrases like "should accelerate next quarter" are interpretation, not fact. Cross-check against the filing's own forward-looking statements before relying on them.
- **Computed deltas.** "Revenue grew 50% YoY" — verify the math against the cited figures. LLMs can transpose or misread numbers in long documents.
- **Risk-factor inclusions.** The model may flag a risk as "new" when it was actually present in an earlier filing it didn't see (it only reads what's in the prompt). Read the latest 10-K's Item 1A directly if a risk listing is decision-critical.

## What to ignore

- **"Buy / sell" language.** The system prompt instructs the model to refuse it; if any slips through, treat it as a bug, not a recommendation. Decision support is not investment advice.
- **Confident-sounding macro claims** ("the sector is recovering") — the prompt scopes the model to *this* ticker's filings, so any market-direction prediction is out-of-scope hallucination. Discount it.

## When to refresh

- After a new quarterly filing lands at SEC. The auto-flow only runs on page mount or explicit Refresh; the cached row could be one earnings cycle behind.
- When the "Stale" badge appears (>7 days old).
- When the analysis looks wrong. A re-run sometimes produces a cleaner read on the same data — the underlying model is non-deterministic at the default temperature.

## When the panel can't generate insights

The panel renders honest error states verbatim:

- **"Not in SEC's database"** — the ticker is a non-US listing. SEC EDGAR only covers US-registered issuers. Upload PDFs manually via the Research documents panel below.
- **"SEC unreachable"** — Railway can't reach data.sec.gov. Usually transient; Retry in a minute.
- **"Monthly LLM token budget would be exceeded"** — the operator-set cap on monthly LLM spend has been hit. Either wait for the next month or raise `MAX_MONTHLY_LLM_TOKENS` in the deploy config.
- **"All providers failed"** — the LLM provider chain (typically Gemini → Anthropic) couldn't serve the call. The failure reason for each provider is shown.

## See also

- [Per-ticker research workspace](/help/reference/pages/research-ticker) — the page this panel lives on.
- [Disclaimers](/help/disclaimers) — the platform-wide statement that all FINRLX output is research, not advice.
- [Upload a document](/help/guides/upload-a-document) — manual Q&A on filings you provide.
