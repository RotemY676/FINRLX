# PROGRAM LEAP — RESUME marker (§2.2)
BACKEND TRACK COMPLETE: F0, F1, F2-core, S2, S3, S4, S6-backend, S8, S9,
C1-prep (state-drift check in CI gate). Full suite 1281 passed / 0 failed.
Remaining program (frontend + environment-bound), in order — requires
Claude Code with node toolchain and rotated fine-grained token (E1, with
workflow scope so DOCS/ci/leap-ci.yml.pending can be installed):
1. S1 design sprint (spec + wireframes + copy deck, council pre-code review).
2. S5 One Screen (/ ticker-first, dossier UI over GET /autopilot/dossier).
3. S6 compare UI (over GET /autopilot/compare).
4. S7 /pro migration (CSV-driven 308s) + decision workspace rebuild.
5. F1.6 staleness badges; F3 sweeps (logged-out re-verify + first authenticated).
6. F2 leftover: session-filtered ingest ranges. 7. C1 close + tag leap-v1.
