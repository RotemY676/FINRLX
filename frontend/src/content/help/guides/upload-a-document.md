---
title: Upload a document for LLM Q&A
summary: How to upload a PDF (10-Q, 10-K, transcript) on a ticker page and ask grounded questions about it.
diataxis: how-to
area: guides
updated: 2026-05-22
order: 51
---

The Research documents panel on `/research/[ticker]` lets you upload PDFs and ask LLM questions grounded in their text. This is the manual path that complements the [auto-fetched SEC insights](/help/guides/read-cross-quarter-insights).

## Why upload manually

- The auto-fetcher only covers **US-registered issuers** (SEC EDGAR). For LSE, TASE, or other foreign listings, you upload PDFs yourself.
- You can analyze **transcripts, presentations, or research notes** — anything in PDF, not just SEC filings.
- You can also upload SEC filings the auto-fetcher missed (older than 6 quarters, or filings in a different form).

## How to upload

1. Navigate to `/research/[ticker]` (e.g. `/research/NVDA`).
2. Scroll to the **Research documents** panel below the auto-generated insights.
3. Click the upload control and select a PDF.
4. The backend extracts text via `pypdf` and persists the document. Typical 10-Q filings extract in well under a second.
5. The new row appears in the document list with a "ready" status. Failures (encrypted PDF, scanned-only, malformed) get committed with an `extraction_status="failed"` and an explicit error message — you can re-upload or fix the source.

Documents are **shared by ticker**. Every signed-in user can see every upload for a given symbol. Only the original uploader (or an admin) can delete a document.

## How to ask a question

1. Select a document from the list.
2. Click one of the suggested prompts ("Summarise this filing in 8 bullet points", "List the top risk factors", etc.) or type your own.
3. The backend sends your prompt + the document's extracted text to the configured LLM (Gemini by default, Anthropic fallback if the provider chain includes it).
4. The answer appears with provenance — provider, model, input/output token counts.
5. Q&A history is shared by document. Anyone analyzing this document later can see what was asked and answered.

## Token budget

Every analysis consumes tokens from the monthly LLM budget. The panel shows current usage; when the cap is reached, new analyses return 503 with a clear "budget exceeded" message rather than silently failing. Operators can raise the cap via `MAX_MONTHLY_LLM_TOKENS` on the backend.

## What the LLM will refuse

The system prompt instructs the model to:

- Refuse trade instructions ("should I buy?", "sell now?").
- Refuse market-direction predictions.
- Only use facts from the document — no general knowledge about the company.
- Cite the section or quoted phrase used.

If you ask a forbidden question, expect a polite refusal. That's the design, not a bug.

## What to verify in any LLM answer

- **Quoted figures** — re-read the source PDF to confirm. LLMs occasionally transpose digits.
- **Section citations** — open the cited page in the PDF and confirm the model read it correctly.
- **Anything that sounds like a forecast or recommendation** — discount it. The model is a reading aid, not an analyst.

## See also

- [Read cross-quarter insights](/help/guides/read-cross-quarter-insights) — the automatic counterpart for US-listed tickers.
- [Per-ticker research workspace](/help/reference/pages/research-ticker) — the page these panels live on.
- [Disclaimers](/help/disclaimers) — platform-wide statement that FINRLX output is research, not advice.
