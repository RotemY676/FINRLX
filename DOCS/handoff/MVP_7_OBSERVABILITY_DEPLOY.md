# Phase MVP-7 — Observability + Deploy Green

**Date:** 2026-05-20
**Branch:** main
**Parent commit (MVP-6):** 398f0cc
**Phase commits:** 9d83991 (7a) → 2195a6b (7b) → f27b1a2 (7c) → [this commit] (7d/7e)

## Summary

Production deploy can now be observed and probed:

- **`/healthz`** deep probe (DB + market-data freshness + recommendation recency). Used as Railway's healthcheck path.
- **Sentry SDK** scaffolded on both services. Activates only when `SENTRY_DSN` (backend) / `NEXT_PUBLIC_SENTRY_DSN` (frontend) is set. No-op default.
- **PostHog** wrapper for the 5 MVP product events. Activates only when `NEXT_PUBLIC_POSTHOG_KEY` is set. No-op default.
- **`scripts/deploy_smoke.sh`** — operator-runnable post-deploy verification (8 HTTP checks + 4 security-header checks).
- **`DOCS/handoff/ONCALL_RUNBOOK.md`** — playbook for `/healthz` interpretation, common incidents, rollback, and env-var inventory.

## What about the "Railway deploy failed" carry-over from MVP-5?

Read the original artifact, not just the summary. The 2026-04-24 log shows the failure was the local `railway-oneclick.ps1` helper script not finding the `railway` CLI or `npm` in the Windows PATH — **not a Railway-side deploy failure.** The current `backend/Dockerfile`, `frontend/Dockerfile`, and `railway.toml` files ARE the deterministic versions the helper script tried to produce, and they have been stable in `main` for ~26 days.

Honest position for this phase: I cannot trigger an actual Railway deploy from this environment (no Railway CLI, no Docker daemon to validate the image locally). What I can verify:

- Dockerfiles are syntactically correct.
- railway.toml uses the new `/healthz` deep probe (was `/api/health`, a shallow check).
- The seed script is idempotent (checks asset count, skips if non-zero) — safe to re-run on every restart.
- A post-deploy smoke is now scriptable in one command.

What the operator still needs to do, with zero ambiguity:

1. Open Railway, redeploy main on both services.
2. Set `SENTRY_DSN` + `NEXT_PUBLIC_SENTRY_DSN` if observability desired.
3. Set `NEXT_PUBLIC_POSTHOG_KEY` if product analytics desired.
4. Run `scripts/deploy_smoke.sh` — every line must say `OK`.

That sequence is documented in `ONCALL_RUNBOOK.md` §3.

## What landed (commit-by-commit)

| Commit | Phase | What |
|---|---|---|
| 9d83991 | MVP-7a | `app/core/healthz.py` + `/healthz` route + 5 tests. DB SELECT-1 (hard), market-data freshness ≤ 7d (soft), recent rec ≤ 30d (info). 503 only on hard fail; 200 with `status="degraded"` on soft. |
| 2195a6b | MVP-7b | Sentry scaffolding: `app/core/observability.py` (`init_sentry()` returns False when DSN empty, otherwise calls `sentry_sdk.init` with FastAPI+Starlette integrations) + 2 tests via monkeypatch (no network). Frontend: `src/instrumentation.ts` (server) + `src/app/sentry-init.tsx` (client) — both dynamic import gated on env. |
| f27b1a2 | MVP-7c | `src/lib/analytics.ts` typed-union wrapper for 5 events: `signup`, `first_rec_view`, `paper_trade`, `replay_open`, `disclaimer_accept`. Dynamic posthog-js import. Call sites added to signup, decision, paper, replay, and disclaimer modal. 2 Vitest tests proving no-op default. |
| (this) | MVP-7d / 7e | `backend/railway.toml`: healthcheckPath `/api/health` → `/healthz`. `scripts/deploy_smoke.sh`: 12-check smoke (8 HTTP + 4 security headers) the operator runs after each deploy. `DOCS/handoff/ONCALL_RUNBOOK.md`: full operator playbook. |

## Test evidence

| Suite | Before MVP-7 | After MVP-7 |
|---|---|---|
| Backend pytest | 735 passed | **742 passed** (5 healthz + 2 observability) |
| `ruff check app/` | clean | **clean** |
| `mypy` on `app/core/` | 6 files clean | **7 files clean** (adds healthz, observability) |
| Vitest | 11 passed | **13 passed** (+ 2 analytics no-op) |
| `next build` | 17 routes | **17 routes** |
| Playwright | 9 passed | **9 passed** |
| GitHub Actions CI | green | **green** (latest run on commit f27b1a2) |

## Operator action required to fully activate observability

This is the only manual sequence:

1. **Sentry** — create a project, copy DSN to Railway. Two services means two projects (backend, frontend), or one project + two environment names.
2. **PostHog** — create a project, copy the write key to Railway frontend service as `NEXT_PUBLIC_POSTHOG_KEY`. Optionally pin the host (`NEXT_PUBLIC_POSTHOG_HOST`).
3. **Trigger an error to validate Sentry** — `curl https://<backend>/api/v1/auth/login -X POST -d 'garbage'` should fire a 422 into Sentry once the DSN is set.
4. **Click around the frontend to validate PostHog** — visit `/decision`, accept the disclaimer, visit `/paper` and `/replay`. Five events should land in PostHog within a minute.

Until those env vars are set, the code paths are no-ops — Sentry never receives a request, PostHog is never imported. This is by design: nobody pays the bundle/cold-start cost when observability is off.

## Known follow-ups

- **Live deploy validation** — needs the operator to actually push a deploy. The smoke script is ready; the env vars need setting. Tracked in this doc but not in a separate ticket.
- **Sentry source-maps + release tagging** — would require `SENTRY_AUTH_TOKEN` in CI and `withSentryConfig` wrapping `next.config.js`. Out of scope for MVP. The current setup captures errors with line numbers from the minified bundle, which is enough for triage.
- **Rate-limit storage** — slowapi's default in-memory storage is fine for single-instance Railway but won't survive horizontal scaling. When Railway adds a second instance, switch to Redis.
- **Carried over from earlier phases**: FastAPI/starlette major upgrade (CVEs from MVP-5), Next.js 14 → 16 (CVEs from MVP-5), the latent F821 bug in `app/services/engines.py`, the a11y baseline (color-contrast + scrollable-region-focusable from MVP-6e).

## What's next — Phase MVP-8 (Beta Polish & Launch Pack)

Goal: hand to first tester. Copy pass across the 6 surfaces, empty/loading/error states, `BETA_TESTER_GUIDE.md`, internal invite mechanism. Will also assume the operator has by then set the observability env vars and run a real deploy.
