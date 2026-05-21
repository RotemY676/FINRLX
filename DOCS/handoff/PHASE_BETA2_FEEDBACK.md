# Phase BETA-2 — In-App Feedback Form

**Date:** 2026-05-21
**Base commit:** `3828907` (OP-5 / Phase OP close)
**Track:** Phase BETA — sub-phase 2 of 4.

## What this sub-phase ships

A feedback table, three endpoints, and a `/feedback` page where a
beta tester writes notes that land in the DB with their user id +
email + the surface they were on.

| Artifact | Path |
|---|---|
| Model | `backend/app/models/feedback.py` |
| Migration `027_feedback` | `backend/migrations/versions/027_feedback.py` |
| API | `backend/app/api/v1/feedback.py` |
| FE page | `frontend/src/app/feedback/page.tsx` |
| Tests (5) | `backend/tests/test_phase_beta2_feedback.py` |

## API

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/api/v1/feedback` | auth | 201 + row; rejects empty message (422) |
| GET | `/api/v1/feedback/me` | auth | tester's own submissions, newest first |
| GET | `/api/v1/feedback` | admin | all submissions, `?status=open` filter |

## FE page

`/feedback` (3.28 kB) shows a 3-field form (Surface optional, Category
picklist, Message textarea) + a list of the tester's past submissions
with category + status chips. Auth-required; redirects to `/login`
otherwise.

## Tests

1. POST without auth → 401.
2. POST persists with `user_email` from the auth context.
3. GET `/feedback/me` scopes to caller only (tested across two users).
4. GET `/feedback` admin-only (403 for user, 200 for admin).
5. POST with empty message → 422.

## Gate results

| Gate | Result |
|---|---|
| Backend pytest (BETA-2 file) | **5 passed** |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| FE tsc | clean |
| FE next build | `/feedback` 3.28 kB built |
| Alembic upgrade/downgrade/re-upgrade | OK |

## Honest limitations

* No status-update UI yet — admin updates `status` via SQL or future
  PATCH endpoint.
* No file attachments. Plain text only.
* No rate limiting on POST. A misbehaving tester could spam; slowapi
  already gates the parent endpoint via the existing per-IP cap.

## Sources

* (no new external sources)
