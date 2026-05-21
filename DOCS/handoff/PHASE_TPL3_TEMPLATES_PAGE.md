# Phase TPL-3 — Templates Page + Apply-Template Flow

**Date:** 2026-05-21
**Base commit:** `4a47e29` (TPL-2)
**Track:** Phase TPL — sub-phase 3 of 4.

## What this sub-phase ships

A new `/templates` page that lists pre-made recommendation templates
with their expected metrics and a one-click "Apply to my profile"
action. Plus the backend endpoint that performs the apply.

| Artifact | Path |
|---|---|
| Apply endpoint | `backend/app/api/v1/profile.py` (`POST /profile/apply-template/{key}`) |
| Service method | `backend/app/services/profile.py` (`ProfileService.apply_template`) |
| /templates page | `frontend/src/app/templates/page.tsx` |
| FE helpers + types | `frontend/src/features/wizard/api.ts` |
| Tests (5) | `backend/tests/test_phase_tpl3_apply_template.py` |

## Behavior contract

### Apply semantics (honesty-first)

`POST /api/v1/profile/apply-template/{key}` overrides only **non-personal**
fields:

* Template-applied: `risk_bucket`, `horizon_band`, `primary_goal`,
  `max_drawdown_pct`, `sector_whitelist`, `sector_blacklist`,
  `exclude_leverage`, `base_currency`, `trading_frequency`,
  `region_preference`.
* **Preserved**: `risk_score`, `knowledge_level`, `years_investing`,
  `instruments_traded`, `investable_amount_band`, `income_band`,
  `liquid_net_worth_band`.

This is the right design: a template can't know your risk tolerance or
financial situation. Applying one tells the recommendation engine "use
this universe / cadence / DD cap" but keeps the truth about *you* intact.

A new revision row is appended with
`change_summary="applied template:<key>"` so the audit trail records
exactly which template was applied at version N.

### Edge cases

* `404` if `{key}` is unknown or `is_active=False`.
* `400 no_profile` if the user hasn't completed the wizard yet —
  the FE catches this and routes the user to `/onboarding`.

### Frontend page

* Lists all active templates, seeds first.
* Each card shows: name + description, badge, allocation summary,
  expected return, max DD cap, Sharpe estimate, horizon tag, cadence
  tag, currency tag, sector whitelist/blacklist tags, **confidence label
  + methodology note** (carried verbatim from TPL-2), and the Apply button.
* Apply success: shows the new version in a status banner, then routes
  to `/profile` after 1.2s.
* Apply failure with `no_profile`: prompts the user to finish the
  wizard, then routes to `/onboarding` after 1.5s.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (TPL-3 file) | **5 passed** |
| Backend pytest (full) | running — will report after green |
| Frontend tsc | clean |
| Frontend vitest | 27 (unchanged) |
| Frontend next build | 23 routes; `/templates` 4.61 kB |
| Playwright chromium | 30 passed + 1 pre-existing flake on admin-mobile |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Follow-ups

* **TPL-4** adds an admin CRUD page (small) for authoring new
  templates (`is_seed=False`). The model + endpoints exist already;
  TPL-4 just adds the page + role-gated POST/PUT/DELETE handlers.
* If we add a "Compare templates" view (multi-select to see metrics
  side-by-side), it consumes the same `GET /api/v1/templates` payload.
* A future small commit can add a sidebar link to `/templates`. Out
  of scope here to keep the diff small.

## Honest limitations

* The Apply endpoint always succeeds atomically (single transaction;
  flush before revision row, then commit). No partial state.
* If a future schema change deprecates a `risk_bucket` value, an old
  template carrying that bucket would persist into a user's profile
  on apply, and a subsequent recommendation run would degrade
  gracefully via `load_overrides_for_user` returning `None` (W-5
  contract). The fix is a one-time migration that retags affected
  templates — we don't add a runtime guard because schema changes
  should be loud, not silent.
* The page doesn't yet show a confirm dialog before overwriting the
  user's existing universe/cadence/currency. For a closed beta this is
  acceptable; if we open to a wider audience a confirm dialog is a
  trivial follow-up.

## Sources

* (no new external sources beyond W-1..W-5 + TPL-1/TPL-2)
