# Council verdicts — F1.6 (staleness surfaced on Pro research)
Date: 2026-07-06 · Gates: backend 1282 passed / 0 failed (endpoint contract
test incl. 404 path); frontend tsc+eslint clean, vitest 51, next build green.

## Quant Skeptic — PASS. Tiers come from the D6/F2 watchdog verbatim; the UI
computes nothing.
## UX Critic — PASS. Badge reuses the existing DataFreshnessBadge treatments;
best-effort (absence renders nothing — no invented status); lag explained in
plain language ("N trading day(s) behind the latest session").
## Truthfulness Auditor — PASS. fresh->ok, stale->caution, degraded->warning;
never claims "live"; per-component doc states the best-effort contract.
## Security/Ops — PASS. Ticker encoded; AbortController on unmount; read-only
endpoint; 404 for unknown tickers rather than fabricating rows.
VERDICT: **PASS** — F1 is now CLOSED end-to-end (chain, provenance, quality
flags, watchdog, DAG, flag, API, UI).
