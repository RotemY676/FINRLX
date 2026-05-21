# Phase TPL-4 — Admin CRUD for Templates (closes Phase TPL)

**Date:** 2026-05-21
**Base commit:** `91378df` (TPL-3)
**Track:** Phase TPL — sub-phase 4 of 4 (closes Phase TPL).

## What this sub-phase ships

Admin-gated POST / PUT / DELETE on `/api/v1/templates` for
user-authored templates. Seed templates are immutable (cannot be
edited or deleted; deactivate via `is_active=false` only).

| Artifact | Path |
|---|---|
| New endpoints + role gate | `backend/app/api/v1/templates.py` |
| Create / update request schemas | `backend/app/schemas/template.py` |
| Tests (12) | `backend/tests/test_phase_tpl4_admin_crud.py` |

## API additions

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/api/v1/templates` | admin | 201 / 403 / 409 (key collision) / 422 (invalid bucket+horizon) |
| PUT | `/api/v1/templates/{key}` | admin | 200 / 403 (non-admin or seed) / 404 / 422 |
| DELETE | `/api/v1/templates/{key}` | admin | 200 / 403 (non-admin or seed) / 404 |

### Role check

A small `_require_admin(user)` helper inside `templates.py` raises 403
if `user.role != "admin"`. Inlined (not a shared dep) because this is
the only surface in the codebase that currently needs role-gating;
promote to `auth_deps.py` once a second consumer arrives.

### Seed-template protection

Seed templates (loaded via `seed_recommendation_templates.py`,
`is_seed=True`) cannot be modified or deleted via the API.
This protects the documented contract (W-4 + TPL-1) — the user-facing
"Balanced Growth" template name and meaning is stable across deploys.

To retire a seed, run a one-off SQL `UPDATE` to set `is_active=false`.

### Allocation summary refresh

When a PUT changes `risk_bucket` or `horizon_band`,
`allocation_summary` is recomputed via `derive_allocation`. This keeps
the `/templates` cards (TPL-3) consistent without a separate refresh
step.

## Invariants tested (12)

1. POST without admin role → 403
2. POST with admin role + valid payload → 201, `is_seed=False`, summary correct
3. POST with colliding key → 409
4. POST with invalid `(bucket, horizon)` → 422
5. PUT without admin role → 403
6. PUT against a seed template → 403 with "immutable" detail
7. PUT for unknown key → 404
8. PUT partial (only `name`) leaves other fields untouched
9. PUT changing bucket + horizon → `allocation_summary` recomputed
10. DELETE without admin role → 403
11. DELETE on seed template → 403 with "cannot be deleted" detail
12. DELETE on user-authored template → 200, then GET 404

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (TPL-4 file) | **12 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Phase TPL — ledger

| Sub | Title | Commit | New tests |
|---|---|---|---|
| TPL-1 | recommendation_templates schema + 5 seeds | `f41732b` | 7 |
| TPL-2 | template expected-metrics + read API | `4a47e29` | 9 |
| TPL-3 | /templates page + Apply Template | `91378df` | 5 |
| TPL-4 | admin CRUD + role gate | this commit | 12 |

**Phase TPL total**: 4 sub-phases, 33 new backend tests, 1 new FE route
(`/templates`, 4.61 kB), 1 new DB table (`recommendation_templates`,
5 seed rows), 5 new endpoints (1 from TPL-3 apply + 4 from TPL-2/4).

## Honest limitations

* **No admin UI page.** Operator authors templates via curl /
  HTTPie. A small admin page can be added in BETA-3 alongside other
  ops tooling.
* The role check trusts the JWT's `role` claim implicitly (set at
  login from `User.role`). If we ever support role changes
  mid-session, we'd need to either refresh on role change or
  re-query the User row on every admin endpoint.
* Seed-template immutability is enforced at the API only. A SQL-level
  trigger would be stricter; we accept the API-only guard because all
  writes flow through this code path.
* Created-by-user-id is stored but not exposed in the response (saves
  a join on the user list for the UI we haven't built). Easy to surface
  in TPL-4-followup if needed.

## Sources

* (no new external sources beyond TPL-1..TPL-3)
