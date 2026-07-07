# Council verdicts — Phase A3 (FinRL ensemble legs + selection history)
Date: 2026-07-07 · Gates: backend 1303 passed / 0 failed (+5); runner+exporter
parse-checked; end-to-end RL-win path proven through build_dossier.

## Quant Skeptic — PASS. The two invariants that make artifact-borne RL honest
are both machine-enforced: (1) protocol identity — an artifact whose splits
differ from the service's walk-forward windows is REJECTED
(protocol_mismatch), so no agent is ever scored on friendlier windows; the
exporter script guarantees identity by construction; (2) re-deflation — the
multiple-testing penalty is recomputed over the ENLARGED candidate set for
EVERY row, so adding RL legs raises the bar for all, and the overfit-A2C
fixture (train 2.5 / val 0.3) provably ranks below a modest heuristic.
An honestly-better PPO can win — and the test proves it does.
## Truthfulness Auditor — PASS. queued_for_research_run remains the truthful
E7-absent state naming the recipe and what would appear; rejection notes say
exactly why; selection history + turbulence events surface as data for the
desk, never as narrative.
## UX Critic — PASS. The payload now carries everything §5.4-5.5 needs:
selection-history strip, turbulence events, imported_from_artifact badges.
## Security/Ops — PASS. Loader is read-only with schema-version + malformed-
JSON containment; runner is import-safe without torch and exits with a clear
message on the worker-stack check; no new backend dependencies.
VERDICT: **PASS** — proceed to A4.
