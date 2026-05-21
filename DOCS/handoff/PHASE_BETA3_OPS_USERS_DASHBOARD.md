# Phase BETA-3 — Per-User Usage Dashboard (admin)

**Date:** 2026-05-21
**Base commit:** `3828907` (OP-5)
**Track:** Phase BETA — sub-phase 3 of 4.

## What this sub-phase ships

`GET /api/v1/ops/users` (admin-only) returns one row per user with
the aggregated stats the operator needs during the closed beta:

* `id`, `email`, `role`, `is_active`
* `created_at`, `last_login_at`
* `has_profile` + `profile_version`
* `paper_portfolio_count`
* `feedback_count`

| Artifact | Path |
|---|---|
| Endpoint | `backend/app/api/v1/ops_users.py` |
| Tests (3) | `backend/tests/test_phase_beta3_ops_users.py` |

## Query strategy

Four cheap queries (no JOINs):
1. Up to `limit` users ordered by `created_at` desc.
2. `InvestorProfile.user_id, version` for those user ids.
3. `PaperPortfolio` count per user.
4. `Feedback` count per user.

Aggregations merged in Python — the user list is small (≤ 5–20 for the
closed beta), so we don't need DB-side aggregation pyrotechnics.

## Why no FE page in this sub-phase

The data is available via the JSON API. A small `/ops/users` page can
be added in a follow-up commit; for the closed beta, the operator can
query the endpoint via `curl` or via the existing admin tools.

## Tests

1. Non-admin → 403.
2. Admin sees every signed-up user including the one we just created.
3. A user who's completed the wizard shows `has_profile=true` +
   `profile_version=1`.

## Gate results

| Gate | Result |
|---|---|
| Backend pytest (BETA-3 file) | **3 passed** |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |

## Honest limitations

* `last_login_at` is only populated by the existing `/auth/login`
  flow. Refresh-only sessions don't update it. Acceptable for the
  closed beta; future enhancement would also touch refresh.
* No pagination on the endpoint beyond `limit`. Fine for ≤ 20 users.
* "Recent activity" is implicit (via `last_login_at`). A more
  granular "last action" would need event tracking we don't have
  outside of analytics events that may not be persisted to the DB.

## Sources

* (no new external sources)
