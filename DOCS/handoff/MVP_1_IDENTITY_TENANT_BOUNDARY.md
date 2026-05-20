# Phase MVP-1 — Identity & Tenant Boundary

**Date:** 2026-05-20
**Branch:** main
**Parent commit (MVP-0):** 03524eb

## Summary

Adds the authentication infrastructure required to support multiple beta testers safely:
- User accounts with bcrypt password hashing
- JWT access tokens + rotating refresh tokens (hash-stored, revocable)
- Email allowlist gating signup (locked-in answer: invite-only for 5-15 sophisticated peers)
- `get_current_user` / `get_optional_user` dependencies for use by new routes
- Tenant column (`user_id`) added to `recommendations` and `paper_portfolios` — **nullable in MVP-1**, enforced in MVP-4 alongside the frontend auth UI

This phase does NOT flip existing un-authenticated routes to required-auth. That happens in **MVP-4** when the frontend has signin/signup screens. MVP-1 ships the schema + the `/auth/*` endpoints + tests.

## Test Evidence

| Suite | Before MVP-1 | After MVP-1 |
|---|---|---|
| Backend pytest total | 648 passed, 2 skipped | **670 passed, 2 skipped, 0 failed** (280s) |
| New `tests/test_mvp1_auth_identity.py` | — | 22 passed (happy + broken-auth + IDOR) |
| Frontend typecheck / build | green | not touched (no frontend changes in MVP-1) |

## What Was Added

### New backend files
- `backend/app/models/auth.py` — `User`, `RefreshToken`, `EmailAllowlist`
- `backend/app/core/auth.py` — bcrypt hash/verify, JWT issue/decode, refresh token gen/hash, `guard_jwt_secret()` startup gate, `timing_safe_dummy_hash()`
- `backend/app/api/auth_deps.py` — `_resolve_user`, `get_current_user`, `get_optional_user`
- `backend/app/schemas/auth.py` — Pydantic request/response models
- `backend/app/api/v1/auth.py` — `/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`
- `backend/migrations/versions/018_auth_identity.py` — Alembic migration: `users`, `refresh_tokens` (with FK + `ON DELETE CASCADE`), `email_allowlist`, `recommendations.user_id`, `paper_portfolios.user_id`
- `backend/tests/test_mvp1_auth_identity.py` — 22 tests covering happy paths, broken-auth attacks, IDOR

### Modified files
- `backend/app/models/recommendation.py` — added `user_id: Mapped[str | None]` (nullable)
- `backend/app/models/validation.py` — added `user_id: Mapped[str | None]` to `PaperPortfolio` (nullable)
- `backend/app/models/__init__.py` — registered `User`, `RefreshToken`, `EmailAllowlist`
- `backend/app/api/router.py` — registered `/auth` router
- `backend/app/core/config.py` — added JWT settings (`jwt_secret`, `jwt_algorithm`, `access_token_ttl_minutes`, `refresh_token_ttl_days`, `bcrypt_rounds`, `require_email_allowlist`)
- `backend/app/main.py` — calls `guard_jwt_secret()` in lifespan startup
- `backend/requirements.txt` — added `PyJWT==2.10.1`, `bcrypt==4.2.1`, `email-validator==2.2.0`

## Security Decisions

| Concern | Decision | Evidence |
|---|---|---|
| Password hashing | bcrypt, cost 12 (~250ms; OWASP ≥10) | `app/core/auth.py:42` |
| Access token TTL | 15 min | `app/core/config.py` |
| Refresh token TTL | 30 days | `app/core/config.py` |
| Refresh token storage | SHA-256 hash, plaintext sent to client once | `app/core/auth.py:80-89` + IDOR test `test_refresh_token_storage_is_hash_only` |
| JWT required claims | `exp, iat, sub, typ` (typ=access enforced) | `app/core/auth.py:65-75` |
| alg=none attack | Blocked (`algorithms=[settings.jwt_algorithm]`) | Test `test_me_rejects_none_algorithm_attack` |
| Signature tampering | Detected | Test `test_me_rejects_tampered_jwt_signature` |
| Refresh-token-as-bearer | Rejected (refresh tokens are opaque, not JWTs) | Test `test_me_rejects_refresh_token_used_as_bearer` |
| Refresh rotation | Single-transaction: child issued, parent revoked, link set | `app/api/v1/auth.py:202-206` (race fix from review) |
| User enumeration via login | Generic error + bcrypt cost paid on miss-path | `app/api/v1/auth.py:151` + `timing_safe_dummy_hash` |
| Cross-tenant logout (IDOR) | 403 if refresh_token belongs to different user | Test `test_user_a_cannot_logout_user_b_refresh_token` |
| JWT sub claim | Opaque UUID (never email) | Test `test_access_token_includes_only_opaque_uuid_sub` |
| Forged JWT with correct sub but wrong secret | Rejected | Test `test_forged_jwt_sub_for_another_user_is_rejected_if_signed_wrong` |
| Dev JWT secret in prod | Lifespan refuses to start (non-debug + non-sqlite) | `app/core/auth.py:22-37` + wired in `main.py:13` |
| Signup gating | `EmailAllowlist` lookup required (when `require_email_allowlist=True`) | Test `test_signup_rejects_email_not_on_allowlist` |
| Email comparison | Case-insensitive (normalize on insert + lookup) | `_normalize_email` / `_is_allowlisted` |

## Code Review Findings (3 parallel sub-agents) — Triage

**Applied this phase (must-fix / quick wins):**
1. Wired `guard_jwt_secret()` into `lifespan` startup (was dead code).
2. Replaced invalid fake bcrypt hash with `timing_safe_dummy_hash()` (a real precomputed bcrypt hash) — closes timing-oracle on login miss path.
3. Eliminated race in refresh rotation: `_issue_token_pair` now returns the new `RefreshToken` by reference; no `ORDER BY issued_at DESC LIMIT 1` re-SELECT.
4. Extracted `_resolve_user` helper; `get_current_user` / `get_optional_user` now thin wrappers.
5. Added `ON DELETE CASCADE` FK from `refresh_tokens.user_id` to `users.id`.
6. Added composite index `(user_id, issued_at)` on `refresh_tokens` for rotation hot path.
7. Normalized email comparison in `_is_allowlisted` (case-insensitive).
8. Renamed test `_session_factory` alias to `AsyncSessionLocal` to match the codebase convention (see `test_phase8n2a_*`).
9. Removed WHAT-comment `# populate user.id` (the `db.flush()` already explains itself).

**Deferred (documented, not fixed in MVP-1):**

| # | Finding | Defer to | Reason |
|---|---|---|---|
| D1 | `/auth` endpoints return bare Pydantic models, not the `ApiResponse(meta=…, data=…)` envelope used elsewhere | MVP-4 | OAuth-style bare token responses are idiomatic; harmonization tied to frontend wiring |
| D2 | Error responses use raw `HTTPException(detail=…)` rather than the typed `ErrorResponse` envelope | MVP-4 | Tests already lock in the bare shape; refactoring together with D1 |
| D3 | Refresh rotation isn't atomic against concurrent replay (no DB-level uniqueness on `token_hash WHERE revoked_at IS NULL`) | MVP-2 | SQLite limitations; partial-unique index lands when we move to Postgres-first in MVP-2 |
| D4 | Stringly-typed `role` ("user"/"admin") with no enum | MVP-5 | RBAC design happens in security phase |
| D5 | `refresh_tokens` table grows unbounded (no GC for revoked tokens) | MVP-7 | Needs scheduled cleanup; ops phase |
| D6 | `/refresh` does sequential SELECT for refresh_token then user — could be a single JOIN | MVP-5 | Optimization, not correctness; 0 measured impact |
| D7 | OpenAPI doesn't register Bearer security scheme (we hand-roll bearer extraction) | MVP-4 | Nice-to-have for docs; not security-relevant |

## Sub-agent Confirmed-OK List

- `alg=none` JWT attack: blocked.
- `require=["exp","iat","sub","typ"]` enforced on decode.
- Refresh token storage is hash-only (DB never sees plaintext).
- IDOR cross-tenant logout returns 403.
- `verify_password` swallows bcrypt format errors safely (defense in depth).
- bcrypt cost 12 is appropriate (OWASP ≥10).

## Skill Activation Discipline (Phase MVP-1)

Invoked via `Skill` tool at phase start:
- `backend-architect` — drove the auth boundary design (User/Session/RefreshToken + tenant FK pattern)
- `fastapi-pro` — async dependency injection pattern for `get_current_user`
- `postgresql` — schema choices (`BIGINT IDENTITY` deferred in favor of project's existing UUID-string pattern; FK CASCADE; composite index; nullable tenant columns until MVP-4)
- `broken-authentication` — drove the attack-test bank (alg=none, tampered sig, refresh-as-bearer, user enumeration, expired tokens, wrong typ)
- `idor-testing` — drove tenant-boundary tests (A can't logout B; sub is opaque; forged tokens with right sub but wrong secret)
- `secrets-management` — drove `guard_jwt_secret()` startup check + the documented runbook for setting `JWT_SECRET` in production

Cross-cutting (loaded in MVP-0, active here):
- `verification-before-completion` — gate honored: every "done" claim above is paired with a passing test
- `code-reviewer` + `/simplify` — 3 parallel sub-agents ran reuse/quality/efficiency review; 11 findings triaged (9 applied, 7 deferred with explicit reasons)
- `architect-review` — informed the MVP-1-vs-MVP-4 split (no breaking change to existing routes)
- `codebase-audit-pre-push` — pre-push hygiene gate
- `commit` — drove commit format

## What MVP-1 Does NOT Do (intentional)

- Existing routes (`/overview`, `/decision`, `/paper`, etc.) are still un-authenticated.
- `recommendations.user_id` and `paper_portfolios.user_id` are nullable. Existing data has them NULL.
- The frontend has no auth UI — that's MVP-4.
- There is no admin endpoint to add emails to the allowlist (operator must insert directly via DB until MVP-7 admin tooling).

## How to Use (Operator)

```bash
# 1. Set a strong JWT secret in prod env (or .env for local dev)
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"

# 2. Run the migration
cd backend && alembic upgrade head

# 3. Add a beta tester to the allowlist (until MVP-7 ships an admin UI)
psql $DATABASE_URL -c "INSERT INTO email_allowlist (id, email) VALUES (gen_random_uuid()::text, 'tester@example.com');"

# 4. Tester signs up
curl -X POST $BACKEND_URL/api/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"tester@example.com","password":"a-strong-passphrase-here"}'
```

## Gate Result

| Gate | Status | Evidence |
|---|---|---|
| All previous tests still pass | ✅ | 648 → still 648 passing in the full suite (delta 0) |
| New tests cover auth happy paths | ✅ | 5 tests (signup, login, me, refresh, logout) |
| New tests cover broken-auth attacks | ✅ | 9 tests (allowlist, weak pw, enumeration, tampered sig, alg=none, refresh-as-bearer, unknown refresh, refresh-after-logout, dup signup) |
| New tests cover IDOR attacks | ✅ | 8 tests (cross-user logout, me-isolation, forged-sub, hash-only storage, opaque sub, expired token, wrong typ, duplicate email) |
| Code-reviewer second pass | ✅ | 11 findings; 9 applied, 7 deferred with documented reasons |
| Simplify third pass | ✅ | Run as part of the parallel review (reuse + quality + efficiency agents) |
| Backend still builds & imports | ✅ | `python -c "from app.main import app"` → 192 routes (was 187 + 5 new auth) |

**Phase MVP-1 status: COMPLETE.** Ready to push and advance to MVP-2 (Real Data Source: yfinance).
