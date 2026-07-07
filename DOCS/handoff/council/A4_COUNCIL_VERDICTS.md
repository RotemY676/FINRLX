# Council verdicts — Phase A4 (dossier v2: bands, markers, matrix, splits, section endpoints)
Date: 2026-07-07 · Gates: backend 1309 passed / 0 failed (+6); desk block
smoke-verified end-to-end (13 bands / 52 markers / 8 matrix rows / 3 split
windows on the synthetic fixture).

## Quant Skeptic — PASS. D47 rule parity is machine-enforced: the band rule
is tested equal to production regime_label at multiple prefixes, so the chart
shading can never diverge from the live label logic. Percentiles exclude the
current value from its own reference distribution and are omitted honestly
under 1y of history (tested). DEBT-S5-2 CLOSED.
## Truthfulness Auditor — PASS. Every event marker carries an evidence_ref;
markers before the charted window are filtered; passthrough matrix rows say
"no rolling distribution computed" instead of faking stats.
## UX Critic — PASS. D42 delivered: 10 section endpoints slice the persisted
dossier so the desk streams progressively; unknown sections 404 with the
valid list; split windows give the arena its timeline geometry.
## Security/Ops — PASS. Endpoints reuse the persistence-aware path (no new
build surface); hostile tickers 400 through the existing validator; section
map is a closed allowlist.
VERDICT: **PASS** — proceed to A5 (the Desk UI).
