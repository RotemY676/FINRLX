# FINRLX — Secrets Runbook

Phase MVP-5 deliverable. Operator-facing guide for handling, rotating, and recovering from leaks of every secret FINRLX uses.

Last updated: 2026-05-20.

## 1. Inventory

| Secret                          | Where it lives                                   | Touches             | Rotation cadence            |
|---------------------------------|--------------------------------------------------|---------------------|-----------------------------|
| `JWT_SECRET`                    | Railway env var (backend service)                | All authenticated requests | Every 90 days OR on any leak |
| `DATABASE_URL` (Postgres password component) | Railway env var (backend service)     | All requests        | On personnel change OR on leak |
| `NEXT_PUBLIC_API_URL`           | Railway env var (frontend service)               | Frontend → backend  | Not secret; per-deploy      |
| Beta tester emails (allowlist)  | Postgres `email_allowlist` table                 | Signup gate         | Per onboarding              |
| `yfinance` rate-limit cookies    | Process-only (in memory)                         | yfinance HTTP client | None (not a secret per-se)  |

There is **no** Stripe key, no Alpaca/Polygon key, no Slack webhook, no Sentry DSN in MVP-5. These will appear in Phase MVP-7 and must be added to this table when they do.

## 2. Source-of-truth: Railway environment variables

The canonical secret store for the deployed service is the Railway project. **Never** edit a `.env` file in the repo to change a production value. Railway's dashboard is the authority.

Local-dev workflow:
- `.env` files in `backend/` and `frontend/` are git-ignored and contain ONLY non-secret development defaults.
- `.env.example` files (committed) document the *names* of expected variables.

## 3. Refusal-on-default-secret guard

`backend/app/core/auth.py:guard_jwt_secret()` runs on app startup and **refuses to boot** if `JWT_SECRET` is still the in-source default while running in production-shape conditions (non-debug + non-SQLite). This is enforced unconditionally — it is not a feature flag.

If the app refuses to start in a deployed environment, you almost certainly forgot to set `JWT_SECRET` in Railway.

## 4. Rotation playbooks

### 4a. JWT_SECRET rotation (planned, 90-day cadence)

1. Generate a new secret locally:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. In Railway → backend service → Variables, replace `JWT_SECRET`.
3. Redeploy the backend. The app will boot on the new secret.
4. **All access tokens issued with the old secret will be invalid.** Users get a 401 on their next request; the frontend should treat this as "session expired" and bounce to `/login`. Refresh tokens are stored as `SHA-256(plaintext)` in the DB and are NOT signed with `JWT_SECRET`, so they survive the rotation; the next refresh will issue an access token signed with the new secret.
5. Post in the operator channel: "JWT_SECRET rotated, all sessions terminated".

### 4b. JWT_SECRET emergency rotation (suspected leak)

Same as planned rotation, but additionally:

1. In the DB, mark every active refresh token revoked so leaked refresh tokens can't be used to obtain new access tokens:
   ```sql
   UPDATE refresh_tokens SET revoked_at = NOW() WHERE revoked_at IS NULL;
   ```
2. Force-logout every connected user (the next refresh will fail and bounce them to `/login`).
3. Audit the `audit_events` table for activity in the window the secret was exposed.

### 4c. Database password rotation

1. In Railway → Postgres → Settings, generate a new password.
2. Railway will update `DATABASE_URL` automatically for connected services.
3. Restart the backend service so the new connection string takes effect.
4. Verify `/healthz` reports DB connection OK (Phase MVP-7).

### 4d. Beta tester removal

A beta tester leaves / loses trust:

1. Remove their email from `email_allowlist`:
   ```sql
   DELETE FROM email_allowlist WHERE email = lower('foo@example.com');
   ```
2. Deactivate their existing user record:
   ```sql
   UPDATE users SET is_active = false WHERE email = lower('foo@example.com');
   UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = (SELECT id FROM users WHERE email = lower('foo@example.com'));
   ```
3. They cannot log in or refresh. They cannot re-signup (allowlist + uniqueness on email).

## 5. Leak response (a secret hit a public Git repo, log, or chat)

1. **Immediately** rotate the leaked secret (sections 4a/4c).
2. Search GitHub for the leaked value — if it landed in the public repo, the secret should be considered burnt; Git history retention means rotation is the only mitigation.
3. Audit access logs in the window from "first commit containing the secret" to "rotation complete".
4. Notify affected users if any tester data was potentially accessed.
5. File a postmortem entry in `DOCS/handoff/` titled `INCIDENT_<DATE>_<SHORT_NAME>.md`.

## 6. What NOT to do

- Do not paste secrets into Slack, Linear, or any chat tool. Use Railway's variables panel.
- Do not commit `.env` files. The `.gitignore` covers `.env` but not all variants; if you add `backend/.env.local` or similar, double-check it is ignored before committing.
- Do not log raw `Authorization` headers or refresh tokens. The backend logs the user id and the action, never the credential.
- Do not weaken `guard_jwt_secret()` to "make local Docker work" — fix the env-var instead.

## 7. Verification

To confirm the runbook still matches reality, run on a quiet night:

- `git ls-files | rg '^\.env$|^.*/\.env$'` — must return empty.
- In a deployed environment, attempt to start the backend without `JWT_SECRET` set; the process must refuse to start.
- Open the `/healthz` endpoint (added in MVP-7); it must report DB connectivity without exposing any URL.
