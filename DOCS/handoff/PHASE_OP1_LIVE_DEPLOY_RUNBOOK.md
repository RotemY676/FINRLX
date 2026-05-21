# Phase OP-1 — Live Railway Deploy Runbook (USER-GATED)

**Date:** 2026-05-21
**Base commit:** `fc47497` (FX-4 / Phase FX close)
**Track:** Phase OP — sub-phase 1 of 5.
**Status:** **BLOCKED on user action** — this sub-phase ships
documentation; the actual deploy must be performed by the operator
because it requires Railway tokens, DSN values, and observation of the
running deployment.

## What this runbook is for

This is the precise step-by-step the operator runs to bring the post-
Phase-FX codebase live on Railway, set the third-party DSNs, and
smoke-test the deployment. Once it's green, OP-2..OP-5 (autonomously
shipped) become meaningful — the scheduler runs against the live DB,
the FX watchdog fills with real ECB rates, etc.

## Pre-flight checklist

Before pressing any buttons:

- [ ] You are signed into Railway and have access to the FINRLX project.
- [ ] You have Sentry DSNs ready for both backend and frontend
      services (sign up at sentry.io if needed; free tier is fine).
- [ ] You have a PostHog project key + host (free tier is fine).
- [ ] The current `main` is at commit `fc47497` or later (post-FX).
- [ ] Local `python -m pytest -q` passes (899/2 expected).

## Step 1 — Push to Railway

The repo already includes `railway.toml` for both backend
(`backend/railway.toml`) and frontend (`frontend/railway.toml`). The
deploy is triggered by pushing to `main`, which has already happened
(see `git log`). If Railway auto-deploy is enabled, the deployment is
in progress; otherwise:

```bash
# From the Railway dashboard, trigger a manual deploy of the backend
# service. The frontend deploys separately. Both should pick up the
# latest commit.
```

Watch the build logs. The backend build runs `Dockerfile`, which:
1. installs `requirements.txt`
2. copies `app/`
3. starts via `startCommand`:
   `alembic upgrade head && python -m seed && uvicorn app.main:app …`

The `alembic upgrade head` step is the critical one — it applies
migrations 021..024 (investor_profiles, rec_templates, fx_rates,
paper_base_currency).

## Step 2 — Set environment variables in Railway

In the backend service's "Variables" tab, set:

| Variable | Source | Notes |
|---|---|---|
| `SENTRY_DSN` | Sentry project → settings → Client Keys (DSN) | enables backend error tracking |
| `ALLOWED_HOSTS` | comma-list incl. frontend's railway URL | already set per Phase MVP-5 |
| `JWT_SECRET` | 32+ random bytes, generate fresh for prod | **required** |
| `FEATURE_RESEARCH_LANE` | `false` | hides research lane from beta UI |
| any existing prod DB vars | — | leave intact |

In the frontend service's "Variables" tab:

| Variable | Source |
|---|---|
| `NEXT_PUBLIC_SENTRY_DSN` | same Sentry project → client DSN |
| `NEXT_PUBLIC_POSTHOG_KEY` | PostHog project key |
| `NEXT_PUBLIC_POSTHOG_HOST` | typically `https://eu.posthog.com` or `https://us.posthog.com` |
| `NEXT_PUBLIC_API_BASE_URL` | the backend's public Railway URL |

After saving each set, **redeploy** the affected service.

## Step 3 — Seed the post-Phase-W / post-Phase-TPL catalogs

These two seeds power the investor-profile wizard and the templates page.
They are idempotent — safe to run twice.

```bash
# Open a Railway shell for the backend service and run:
python -m scripts.seed_profile_questions
python -m scripts.seed_recommendation_templates
```

Expected output:
* `profile_questions: inserted=26 skipped=0 total_now=26`
* `recommendation_templates: inserted=5 skipped=0 total_now=5`

If you see `inserted=0 skipped=26` on a re-run, that's normal
(idempotent).

## Step 4 — Add yourself to the allowlist

```bash
python -m scripts.manage_allowlist add your-email@example.com --note "OP-1 deploy verifier"
```

## Step 5 — Smoke test

```bash
# From your local shell:
bash backend/scripts/deploy_smoke.sh https://<backend-url>.up.railway.app
```

Every line must print `OK`. Errors here are blocking — do not proceed
to step 6 until they're resolved.

## Step 6 — Walk all 14 surfaces in the browser

Sign up with your allowlisted email, then visit:

1. `/onboarding` — finish the 8-step wizard
2. `/decision` — auto-routed after wizard submit
3. `/profile` — your profile is shown; click "Run a profile-aware recommendation"
4. `/templates` — 5 seed cards render; click Apply on one
5. `/paper` — currency selector defaults to your profile.base_currency
6. `/overview` — main dashboard
7. `/comparison`
8. `/replay`
9. `/backtests`
10. `/universe`
11. `/policies`
12. `/integrations`
13. `/risk`
14. `/news`

Screenshot anything broken.

## Step 7 — Open OP-1 done

* Sentry shows zero new errors after the walk.
* PostHog shows your session events (`paper_trade`, etc.).
* `/ops/incidents` shows no `FX stale: …` incidents (OP-2 schedule
  picks this up; the watchdog is run manually for now via
  `python -m scripts.fx_freshness_watchdog`).

When all of the above is green, **OP-1 is closed.** OP-2 can then take
over the daily ingestion + FX refresh.

## What can fail and how to fix it

| Symptom | Likely cause | Fix |
|---|---|---|
| `alembic upgrade head` fails | DB schema drift from earlier prod | Run `alembic stamp` after manual diff inspection |
| `/healthz` returns 503 | DB unreachable | check Railway PG service status |
| Frontend 401 on every request | `NEXT_PUBLIC_API_BASE_URL` typo | re-set it; redeploy |
| Wizard "Could not load questions" | seed step 3 never ran | re-run `python -m scripts.seed_profile_questions` |
| `/templates` shows 0 cards | TPL seed never ran | re-run TPL seed |
| Sentry not reporting | `SENTRY_DSN` typo | the `app/core/observability.py` initialiser silently no-ops on bad DSN; verify in the service logs |

## Why this sub-phase ships only docs

The actual deploy needs:
* Railway tokens I cannot see.
* DSN values from accounts I cannot access.
* A human pressing "redeploy" and watching the build logs.

Per the locked autonomous-mode contract in
`project_phase_w_tpl_fx_op_decisions.md`: pause for paid external API
keys, deploys, DSNs. The runbook above is everything the user needs
to do the step without me re-explaining.

## After OP-1: OP-2..OP-5

OP-2..OP-5 are shipped autonomously and run against the local DB until
OP-1 lands. After OP-1 they automatically pick up production state:

* **OP-2** scheduler runs daily ingestion + FX refresh.
* **OP-3** alerts route freshness incidents to webhook/email.
* **OP-4** DR runbook + JWT rotation script.
* **OP-5** FastAPI 0.115→0.118+ and Next 14→15.

## Sources

* Existing `DOCS/handoff/MVP_LAUNCH_HANDOFF.md` (the original MVP deploy
  guide; OP-1 supersedes the "what to do tomorrow" section).
* Existing `DOCS/handoff/ONCALL_RUNBOOK.md` for general operational
  procedures.
* Existing `backend/scripts/deploy_smoke.sh` for the smoke test
  invocation.
