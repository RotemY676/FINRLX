# PROGRAM LEAP — RESUME marker (§2.2)
DONE: F0, F1 (CLOSED end-to-end incl. F1.6 UI), F2(core), S1, S2, S3, S4,
S5 (+polish), S6 (backend+UI), S7a, S8, S9, C1-prep. All in-env gates green:
backend 1282/0, frontend tsc+eslint+vitest 51+build.
Remaining program — ONLY these:
1. S7b: full D33 migration of remaining manual surfaces under /pro/* with the
   redirects CSV + e2e spec (large; buildable here, e2e run env-blocked).
2. F2 leftover: session-filtered ingest ranges (low priority).
3. F3 sweeps (logged-out re-verify + first authenticated) — env-blocked
   (Playwright browser download domain + production network).
4. C1 close report + tag leap-v1 — after F3.
5. E1 operator item: rotate exposed token (fine-grained, workflow scope) and
   install DOCS/ci/leap-ci.yml.pending.
