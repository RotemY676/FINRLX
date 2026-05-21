# Phase BETA-1 — Beta-Tester Invite Runbook (BLOCKED ON OP-1)

**Date:** 2026-05-21
**Base commit:** `3828907` (OP-5 / Phase OP close)
**Track:** Phase BETA — sub-phase 1 of 4.
**Status:** Documentation only — the actual invites require the live
Railway deployment from OP-1 to be reachable.

## What this sub-phase ships

The runbook that turns a deployed FINRLX into 3–5 working beta-tester
sessions. No new code — every tool the runbook references already exists
from earlier phases.

## Pre-conditions

- [ ] OP-1 deploy is live + `scripts/deploy_smoke.sh` is fully green.
- [ ] `scripts/seed_profile_questions` + `scripts/seed_recommendation_templates`
      have been run against the prod DB.
- [ ] You can reach the backend Railway shell via `railway shell`.
- [ ] You have 3–5 email addresses ready (sophisticated peers).

## Step 1 — Add testers to the allowlist

```bash
# Inside the backend Railway shell:
python -m scripts.manage_allowlist add tester1@example.com --note "Cohort A: PM background"
python -m scripts.manage_allowlist add tester2@example.com --note "Cohort A: quant"
python -m scripts.manage_allowlist add tester3@example.com --note "Cohort A: hobbyist"
# ... etc.

# Verify:
python -m scripts.manage_allowlist list
```

Each `add` writes one `EmailAllowlist` row. Without this, the tester's
`/auth/signup` returns 403.

## Step 2 — Send each tester the welcome email

Template (paste-ready):

```
Subject: FINRLX closed beta — your access is live

Hi <name>,

You're invited to the FINRLX closed beta. Quick context:

* What it is: a decision-intelligence tool for medium-term equity
  investing. Generates a recommendation (portfolio of weights, with
  confidence breakdown), paper-trades it locally, and lets you replay
  every decision deterministically.
* What it isn't: investment advice. Educational research only. We
  spell this out in a disclaimer modal on first launch.

To get started:

1. Sign up: <FRONTEND_URL>/signup
   Use this exact email: <tester_email>
   Password: 12+ chars, your choice.

2. The signup auto-routes you into an 8-step investor-profile wizard.
   It takes ~3 minutes and uses standard suitability questions (no
   "what's your salary" — just bands).

3. Then you land on /decision. The first recommendation auto-runs
   against the universe + your saved profile. Paper-trade it, replay
   it, edit your profile at /profile, or apply a pre-made template
   at /templates.

If anything looks broken or confusing, please use the in-app
feedback button (bottom right) — that's how we'll prioritize fixes.

Quick guide: <link to DOCS/handoff/BETA_TESTER_GUIDE.md or hosted copy>
```

## Step 3 — Watch for activity

```bash
# Inside Railway shell, hourly for the first 24 hours:
python -m scripts.manage_allowlist list
```

The list shows when each tester first signed up. If a tester's email
shows allowlisted but never used after 48 hours, send a follow-up.

## Step 4 — Check operational state

After the first wave of activity:

* `/api/v1/ops/incidents` — any new FX-stale or pipeline incidents?
* `/api/v1/ops/jobs` — the OP-2 daily DAG ran on schedule?
* `/api/v1/ops/users` *(added in BETA-3)* — who completed the wizard?
  Who has a paper portfolio?
* Sentry — any errors tagged with a tester's user_id?

## Step 5 — Revoke / extend access

To deactivate a tester (they leave the beta, or you want to gate):

```bash
python -m scripts.manage_allowlist deactivate tester@example.com
```

This sets `users.is_active = false`, revokes their refresh tokens, and
keeps them out of the allowlist. They can't log in, refresh, or
re-sign-up.

## Reference links

* Allowlist tool: `backend/scripts/manage_allowlist.py`
* Tester-facing guide: `DOCS/handoff/BETA_TESTER_GUIDE.md`
* DR (if a tester reports data loss): `DOCS/handoff/DR_RUNBOOK.md`
* Operational runbook (oncall, scheduler, alerts):
  `DOCS/handoff/ONCALL_RUNBOOK.md`
* Tester feedback storage (BETA-2): `feedback` table
* Per-user dashboard (BETA-3): `/api/v1/ops/users`

## Honest limitations

* **This sub-phase is gated on OP-1.** Until the deploy is live, the
  signup URL doesn't resolve.
* The allowlist is operator-managed only. There's no "request invite"
  flow yet — intentional for the closed beta.
* `BETA_TESTER_GUIDE.md` exists in repo from Phase MVP-8 but may need
  refreshing for Phase W (wizard) + Phase TPL (templates) + Phase FX
  (currency selector). A small follow-up commit can append the new
  sections.

## Sources

* `DOCS/handoff/MVP_LAUNCH_HANDOFF.md` (original invite contract, MVP-8)
* `DOCS/handoff/MVP_8_OBSERVABILITY_DEPLOY.md` (allowlist gating)
* `backend/scripts/manage_allowlist.py` (the actual tool)
