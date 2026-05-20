# FINRLX — On-Call Runbook

Phase MVP-7 deliverable. Operator-facing reference for keeping the live service answerable, deploying changes, and responding when something breaks.

Last updated: 2026-05-20.

## 0. Quickest sanity check

```
curl -s https://<backend-url>/healthz | jq
```

If you see `"status": "ok"` you're done. If you see `"status": "unhealthy"` or no response, jump to §4.

## 1. Architecture summary

- **Frontend**: Next.js 14 App Router on Railway. Static + SSR.
- **Backend**: FastAPI + SQLAlchemy 2 (async) on Railway. PostgreSQL on Railway.
- **Auth**: JWT access + refresh (rotation, SHA-256 hashed in DB).
- **Observability**: Sentry (errors) + PostHog (5 product events). Both no-op when env DSN/key is unset.
- **CI**: GitHub Actions (ruff, mypy, pytest, vitest, next build, Playwright + axe).
- **No live broker**, **no real money**, paper trading only.

## 2. Environment variables (production)

Set in Railway → backend service → Variables:

| Variable | Required | Purpose |
|---|---|---|
| `JWT_SECRET` | **YES** | 48-char random string. App refuses to boot without it. |
| `DATABASE_URL` | **YES** | Set automatically by Railway when Postgres is attached. |
| `CORS_ORIGINS` | YES | JSON array of allowed frontend origins. |
| `REQUIRE_EMAIL_ALLOWLIST` | recommended | `true` in prod so signup is invite-only. |
| `SENTRY_DSN` | optional | Backend Sentry project DSN. No-op if missing. |
| `SENTRY_ENVIRONMENT` | optional | e.g. `production` / `preview`. |
| `RATE_LIMIT_ENABLED` | optional | `true` (default). Disable only for load tests. |

Frontend service → Variables:

| Variable | Required | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | YES | Public URL of the backend service. |
| `NEXT_PUBLIC_SENTRY_DSN` | optional | Browser-side Sentry. No-op if missing. |
| `NEXT_PUBLIC_POSTHOG_KEY` | optional | PostHog write key. No-op if missing. |
| `NEXT_PUBLIC_POSTHOG_HOST` | optional | Defaults to `https://us.i.posthog.com`. |
| `SENTRY_DSN` | optional | Server-side rendering errors. |

See `DOCS/handoff/SECRETS_RUNBOOK.md` for rotation cadence.

## 3. Deploying a change

1. **Land on `main`** through a PR. CI must be green (`gh pr checks <PR#>` from the repo).
2. **Railway auto-deploys `main`** for both services. Watch the deploy log for `Sentry initialized for environment=...` (if SENTRY_DSN is set) and the uvicorn startup line.
3. **Smoke the deploy**:
   ```bash
   FINRLX_BACKEND_URL=https://<backend>.up.railway.app \
   FINRLX_FRONTEND_URL=https://<frontend>.up.railway.app \
   bash scripts/deploy_smoke.sh
   ```
   Every line should say `OK`. The script returns a non-zero exit code if any check fails.

## 4. `/healthz` interpretation

The probe returns three checks plus an overall status:

```json
{
  "status": "ok" | "degraded" | "unhealthy",
  "version": "0.1.0",
  "checks": [
    { "name": "database", "ok": true,  "severity": "hard", "detail": "connected" },
    { "name": "market_data_freshness", "ok": true, "severity": "soft", "detail": "newest_bar_2026-05-17" },
    { "name": "recent_recommendation", "ok": true, "severity": "info", "detail": "latest_2026-05-19T08:00:00+00:00" }
  ]
}
```

- **`status: "ok"`** — everything green. HTTP 200.
- **`status: "degraded"`** — soft check failing (typically stale market data). HTTP 200, Railway keeps routing traffic. Action: run the ingest job. See §5.
- **`status: "unhealthy"`** — hard check (DB) failing. HTTP 503, Railway will pull the service from the load balancer.

## 5. Common incidents

### 5a. /healthz returns 503 → database unreachable

1. Check Railway → Postgres → Status. If down, no action — Railway will restore.
2. If Postgres is up: `DATABASE_URL` may be stale or rotated without redeploy. Restart the backend service.
3. If the issue persists, file an incident in `DOCS/handoff/INCIDENT_YYYY-MM-DD_<short>.md` and post to the operator channel.

### 5b. Market data stale (`degraded`)

```bash
# Trigger an ingest run.
curl -X POST "$FINRLX_BACKEND_URL/api/v1/ingest/bars" \
  -H "Content-Type: application/json" \
  -d '{"source": "yfinance", "tickers": ["AAPL", "MSFT", "GOOGL"], "date_from": "2026-01-01", "date_to": "2026-05-20"}'
```

`/healthz` should return `"status": "ok"` within 30s of the ingest finishing.

### 5c. A tester reports "I see 429 too often"

Rate limits are per-IP. If they are behind a shared NAT (corporate office), the cap may bite. Defaults: auth=10/min, ingest=20/min, recommendation-write=30/min, global=120/min. Tune in Railway env via `RATE_LIMIT_*` settings.

### 5d. Sentry sees a spike of identical errors

1. Look at the first occurrence in Sentry — what release/commit?
2. If the regression landed in the latest deploy, **roll back** by re-deploying the previous commit from Railway's "Deployments" tab.
3. File the cause + the fix into a `DOCS/handoff/INCIDENT_*.md` postmortem.

### 5e. Refresh tokens rejected en masse

Likely `JWT_SECRET` was rotated. See `DOCS/handoff/SECRETS_RUNBOOK.md` §4a. Users will be re-logged-in once they refresh.

## 6. Roll-back

Railway dashboard → service → Deployments → click the previous green commit → "Redeploy". Takes ~3 minutes. The DB schema may be ahead of the rolled-back code — only roll back if the migration is forward-compatible.

If the schema is incompatible: also `alembic downgrade -1` *manually* (do NOT add it to the startCommand; that's a one-way street).

## 7. Logs

- Railway → service → "View logs" — stdout + stderr.
- Sentry — captured exceptions with stack traces (only if `SENTRY_DSN` is set).
- PostHog — per-user product events (only if `NEXT_PUBLIC_POSTHOG_KEY` is set).

## 8. Out of scope

- **Real broker execution** — explicitly NOT in MVP. Paper portfolio only.
- **Real-time market data** — daily bars only.
- **Stripe / billing** — beta is free.
- **Multi-region** — single Railway region.

## 9. Contacts

This is a single-operator system today. If you (Rotem) cannot respond, the service runs read-only behind invite-only signup — nothing breaks irreversibly during downtime. Document any maintenance window in the operator channel before disabling the backend.
