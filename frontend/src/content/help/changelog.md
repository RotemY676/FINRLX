---
title: Changelog
summary: What changed and when, newest first.
diataxis: reference
area: changelog
updated: 2026-05-22
---

What changed and when, newest first. Entries follow the [Keep a Changelog](https://keepachangelog.com/) convention with the tags **Added**, **Changed**, **Fixed**, **Deprecated**, and **Removed**.

## 2026.05 — Phase 18: SEC EDGAR auto-ingest + cross-quarter insights

**Added**

- A new **Insights panel** on every `/research/[ticker]` page that automatically fetches the last 6 quarterly filings (10-Q + 10-K) from SEC EDGAR and synthesizes a four-section analysis (headline-metric trajectory, latest-quarter delta, risk-factor changes, what-to-watch). Insights cache for 7 days and can be regenerated on demand. See [Read cross-quarter insights](/help/guides/read-cross-quarter-insights) and the [per-ticker workspace reference](/help/reference/pages/research-ticker).
- Backend endpoints under `/api/v1/research/{ticker}/`:
  - `POST /auto-ingest` — fetch + persist 6 quarterly filings from SEC.
  - `POST /insights` — generate fresh insights from current sec_auto documents.
  - `GET /insights` — most recent cached insights (or null).
  - `GET /edgar/probe?ticker=` — diagnostic endpoint to verify SEC connectivity.
- New `ticker_insights` table (Alembic migration 032) for cross-document analysis history.
- Decision-support disclaimer footer on every AI-generated insight card per the fintech-disclaimer-and-marketing-guard requirement.
- `SEC_USER_AGENT` env var required for any EDGAR call (SEC's fair-access policy).

**Changed**

- `research_documents` table extended (migration 031) with `source`, `sec_accession_no`, `sec_form`, `sec_period_of_report`, `external_url` columns. `storage_path` is now nullable so SEC-auto rows can persist without a local file. Composite unique index on `(ticker, sec_accession_no)` makes re-ingest idempotent.
- LLM provider chain now supports `LLM_PROVIDER_CHAIN=gemini,anthropic` for free-first cascading fallback (Phase 17.4). Gemini 2.5 Flash is the default free-tier provider; Anthropic fires only when Gemini fails or is over quota.

## 2026.05 — Phase 17: Research documents + LLM Q&A

**Added**

- A **Research documents panel** on `/research/[ticker]` where authenticated users can upload PDFs (10-Q, 10-K, transcripts) and ask LLM questions grounded in the document text. See [Upload a document for LLM Q&A](/help/guides/upload-a-document).
- Backend endpoints: `POST/GET/DELETE /api/v1/research/documents`, `POST /api/v1/research/documents/{id}/analyze`, `GET /api/v1/research/documents/_usage` (monthly token-budget status).
- PDF text extraction via `pypdf` (Phase 17.0), real Anthropic provider integration (Phase 17.2), shared-by-ticker document sharing model with per-uploader delete permission.
- Monthly LLM token budget tracker (`MAX_MONTHLY_LLM_TOKENS` env var) that 503s the analyze endpoint before exceeding the cap.

## 2026.05 — Phase 16: Per-ticker research workspace

**Added**

- The [Research hub](/help/reference/pages/research) at `/research` and the [per-ticker workspace](/help/reference/pages/research-ticker) at `/research/[ticker]`.
- Per-ticker panels: real price chart, news mentions filtered to the symbol, fundamentals snapshot (Finnhub-backed), sector peer comparison. Each panel honors feature flags and renders an honest "configure provider" empty state when its upstream isn't wired.

## 2026.05 — Help center launch

**Added**

- A complete in-app Help center at [`/help`](/help). Authored in MDX, served by Next.js, ~50 pages across Getting started, Concepts, Guides, Reference, Glossary, FAQ, Troubleshooting, Changelog, and Disclaimers.
- The global Help (`?`) button in the top bar of every page links to the Help center.
- Contextual `?` glyphs deep-link from in-app screens — Policies, Decision, Home, Universe, Backtests, Risk, Replay, Comparison — into the matching help page.
- Numbered-callout screenshots on six high-traffic reference pages (Home, Decision, Policies, Universe, Backtests, Replay), captured against the live deploy with a 25-second post-networkidle wait so charts and animations are fully settled.
- A search bar on the Help landing page covering every help page's title, summary, and body text.
- A Playwright-based screenshot pipeline (`npm run help:shots`) that re-captures the screenshot set against the live deploy, for ongoing maintenance.

## 2026.05 — Onboarding wizard (WIZ-1/2/3)

**Added**

- An eight-step welcome wizard at `/onboarding` that collects knowledge, financial, risk, objectives, universe, and operational preferences. Defaults flow from the wizard into the workspace.
- A "Re-run the wizard" button on the [Profile page](/help/reference/pages/profile) so you can update your defaults at any time. See [Re-run the welcome wizard](/help/guides/re-run-the-wizard).
- WIZ-2: Users without a complete profile are routed to `/onboarding` after sign-in.
- WIZ-1: The profile questions catalog seeds automatically on first server boot.

## 2026.05 — Home command center (HOME-1)

**Changed**

- The home page is now the **Decision Command Center**, replacing the previous greeting + next-actions overview. The new screen answers "what changed, what needs review, what evidence supports it, what is stale, shadow-only, or blocked" at a glance. See [Reading the dashboard](/help/getting-started/reading-the-dashboard).

## See also

- [Help center landing](/help) — start here if you are new.
- [FAQ](/help/faq) — common questions answered.
