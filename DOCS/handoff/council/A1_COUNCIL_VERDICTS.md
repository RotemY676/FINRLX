# Council verdicts — Phase A1 (data expansion: XBRL · filings · insider)
Date: 2026-07-07 · Gates: backend 1290 passed / 0 failed (+8); adapters
fixture-tested with zero network in tests; keyless path green.

## Quant Skeptic — PASS. The decisive test is the stance regression: with all
A1 sources present vs all absent, summary.stance and composite_score are
byte-identical — the new data is context, not signal. Restatement handling
(latest-filed 10-K value wins) and 10-Q exclusion are fixture-proven.
## Truthfulness Auditor — PASS. Every absence path returns the named reason
(no_api_key / tier_or_auth / no_sec_cik / sec_unreachable); MSPR carries the
noisiness caveat verbatim; the similarity read states "not a directional
call"; nothing is fabricated when sources are missing.
## UX Critic — PASS. Sections carry per-stage timings for the desk's
progress; degraded states name the missing source, enabling honest UI copy.
## Security/Ops — PASS. SEC UA policy implemented (D51) with contact env +
6h in-process caching; Finnhub tier errors (401/402/403) detected as
tier_or_auth rather than retried; all provider calls timeboxed; total
failure containment per section (a section can never sink a dossier).
VERDICT: **PASS** — proceed to A2.
