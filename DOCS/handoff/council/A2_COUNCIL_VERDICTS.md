# Council verdicts — Phase A2 (sentiment duality: social lane + FinGPT A/B)
Date: 2026-07-07 · Gates: backend 1298 passed / 0 failed (+8).

## Quant Skeptic — PASS. Divergence is sign-based with a ±0.05 dead zone
(unit-tested matrix incl. both not_applicable paths); FinGPT scores attach to
items but the stance pipeline reads only the lexicon compound — the D44
"never influences stances" note ships in the payload and the composite path
is untouched (A1 regression still covers it).
## Truthfulness Auditor — PASS. The scored social lane activates only behind
FINNHUB_PREMIUM (E8 unverified tier — the exact caveat from the research
report); the keyless fallback is labeled "mentions only, unscored" verbatim;
not-trending is an honest state, not an error; artifact absence reports
research_worker_unavailable with what would appear.
## UX Critic — PASS. The payload gives the desk everything §5.6 needs: dual
per-item scores, agreement flags + rate, lane statuses, divergence read.
## Security/Ops — PASS. Premium flag default off; tier/auth codes detected;
keyless fallback has no secrets; artifact loader is read-only with malformed-
JSON containment.
VERDICT: **PASS** — proceed to A3.
