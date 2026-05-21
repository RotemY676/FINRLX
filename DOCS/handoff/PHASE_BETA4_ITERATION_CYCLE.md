# Phase BETA-4 — Weekly Iteration Cycle (closes Phase BETA + the full track)

**Date:** 2026-05-21
**Base commit:** `3828907` (OP-5)
**Track:** Phase BETA — sub-phase 4 of 4 (closes Phase BETA).

## What this sub-phase ships

A documented weekly iteration cycle the operator runs while the closed
beta is live. No code — this is a process document that wires together
every artifact we shipped across Phases W / TPL / FX / OP.

## The weekly cycle

### Monday — sweep

```bash
# 1. Did the daily DAG actually run? Any failures in the last 7 days?
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$API/api/v1/ops/jobs?limit=50" | jq '.data.runs[] | select(.status=="failed")'

# 2. Any open incidents?
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$API/api/v1/ops/incidents" | jq '.data[] | select(.status=="open")'

# 3. Notifications sent / failed?
# (Inspect the notifications table directly via Railway shell:)
railway shell
psql -d "$DATABASE_URL" -c \
  "SELECT channel, status, COUNT(*) FROM notifications
   WHERE sent_at > NOW() - INTERVAL '7 days' GROUP BY channel, status;"
```

### Tuesday — feedback triage

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$API/api/v1/feedback?status=open" | jq '.data[]'
```

For each row:
* If it's a bug → add an entry to a tracking spreadsheet / GH issue,
  flip status via SQL (`UPDATE feedback SET status='triaged'`).
* If it's a feature request → log it, flip to `triaged`.
* If it's not actionable → flip to `wontfix` with a one-line internal
  comment in the spreadsheet.

### Wednesday — usage check

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "$API/api/v1/ops/users" | jq '.data[] | {email, has_profile, paper_portfolio_count, feedback_count, last_login_at}'
```

* Anyone with `has_profile=false` after 48h → send a nudge email.
* Anyone with `last_login_at` > 7d → consider whether to remove or
  send a check-in.

### Thursday — ship 1–2 fixes

Pick the 1–2 highest-impact triaged-but-open feedback items. Ship
small, push, update Sentry to confirm the fix landed.

### Friday — weekly note

Update an internal "Beta weekly" doc:

```
Week of <date>
- Active testers: N
- New signups: N
- Profiles completed: N
- Paper portfolios created: N
- Feedback received: N (open: K, resolved: K)
- Incidents opened: N (FX: K, other: K)
- Fixes shipped: <one-line each>
- Next week: <one-line plan>
```

This doc is your conversation thread with future-you.

## End-of-beta criteria

When the beta is ready to graduate (open to broader cohort or migrate
to paid):

* [ ] At least 4 weekly cycles run cleanly.
* [ ] ≤ 1 open `severity=1` incident in the last 7 days.
* [ ] Average tester completes the wizard within 48h of signup.
* [ ] All `severity=1` feedback resolved or with documented timelines.
* [ ] Sentry error rate < 1% of authenticated requests.
* [ ] PostHog shows ≥ 50% of testers ran `/profile/run-pipeline`
      at least once.
* [ ] Drill log in DR_RUNBOOK has at least one successful restore drill.

## Phase BETA — ledger

| Sub | Title | Commit | New tests | Notes |
|---|---|---|---|---|
| BETA-1 | Tester invite runbook | (this commit) | (docs only) | gated on OP-1 |
| BETA-2 | Feedback form (API + FE) | (this commit) | +5 | 3 endpoints, /feedback page 3.28 kB |
| BETA-3 | Per-user usage dashboard | (this commit) | +3 | endpoint only; FE page deferred |
| BETA-4 | Weekly iteration cycle doc | (this commit) | (docs only) | — |

**Phase BETA total:** 4 sub-phases, 8 new backend tests, 1 new DB
table (`feedback`), 1 new FE route (`/feedback`), 4 new endpoints
(`/feedback` POST/GET-me/GET-all + `/ops/users`).

## Full track close-out (Phases W → TPL → FX → OP → BETA)

| Phase | Sub-phases | New backend tests | New FE assets | Notes |
|---|---|---|---|---|
| **W** | 8 | ~91 | 8-step wizard + /profile | investor-profile wizard end-to-end |
| **TPL** | 4 | 33 | /templates | 5 seed templates + apply + admin CRUD |
| **FX** | 4 | 22 | CurrencyValuation card | Frankfurter + multi-currency + freshness |
| **OP** | 5 | 25 + (OP-5 zero new) | (deps bumped) | DAG + alerts + DR + framework upgrades |
| **BETA** | 4 | 8 | /feedback | beta-tester flow + ops dashboard |

**Grand total since post-MVP main (`ed18d07`):**

* **Sub-phases:** 25 across 5 phases
* **Backend tests added:** ~179 (post-MVP 747 → ~929 expected at close)
* **New backend tables:** 6 (`investor_profiles`, `investor_profile_revisions`,
  `profile_questions`, `recommendation_templates`, `fx_rates`,
  `paper_portfolios.base_currency` column, `job_runs`,
  `notifications`, `feedback`)
* **New FE routes:** 4 (`/profile`, `/templates`, `/feedback`, plus
  the wizard rewrite of `/onboarding`)
* **New CLIs:** 5 (`seed_profile_questions`, `seed_recommendation_templates`,
  `fx_freshness_watchdog`, `run_daily_dag`, `rotate_jwt_secret`,
  `export_user_data`)
* **New runbooks:** 3 (`PHASE_OP1_LIVE_DEPLOY_RUNBOOK`, `DR_RUNBOOK`,
  `PHASE_BETA1_TESTER_INVITES`)
* **Frameworks upgraded:** FastAPI 0.115→0.118, Next 14→15, React 18→19

## What's left after BETA close

* **OP-1 live deploy** (user action — runbook in
  `PHASE_OP1_LIVE_DEPLOY_RUNBOOK.md`).
* **BETA-1 invitations** (operator runs `manage_allowlist` after OP-1).
* **First DR drill** logged in `DR_RUNBOOK.md`.
* **One real cycle** of the BETA-4 weekly cadence.

Everything else this track was meant to build is shipped and on `main`.

## Honest assessment

What we shipped is a complete, audit-trail-backed beta platform. What
**hasn't** happened is the live deploy + the first real tester signing
up — both gated on OP-1. The plan's autonomous-mode contract was honest
about that gate from the start; this closing doc just confirms it
hasn't moved.

Once OP-1 lands, BETA-1 takes ~30 minutes to send invites, BETA-4 is
a Monday-Friday weekly rhythm, and the rest of the system runs itself
(scheduler, alerts, freshness watchdog, notifications).

## Sources

* All linked phase handoff docs in `DOCS/handoff/`.
