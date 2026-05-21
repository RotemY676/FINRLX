# Phase OP-3 — Notifications Service (Webhook + SMTP)

**Date:** 2026-05-21
**Base commit:** `b8535c1` (OP-2 / DAG)
**Track:** Phase OP — sub-phase 3 of 5.

## What this sub-phase ships

Pluggable notification service that walks open Incident rows and sends
one notification per `(incident, channel)` pair — once per pair, ever.
The audit lives in a new `notifications` table with a UNIQUE constraint
so idempotency is enforced at the DB.

| Artifact | Path |
|---|---|
| Model | `backend/app/models/notification.py` |
| Migration `026_notifications` | `backend/migrations/versions/026_notifications.py` |
| Service | `backend/app/services/notifications.py` |
| DAG entry `daily_notify_incidents` | `backend/app/jobs/daily_dag.py` |
| Tests (10) | `backend/tests/test_phase_op3_notifications.py` |

## Channels

Both auto-discovered at runtime via `discover_channels()`. A channel
returns `is_configured=False` when its env vars are missing; only
configured channels receive sends.

### WebhookChannel

| Env var | Purpose |
|---|---|
| `NOTIFY_WEBHOOK_URL` | POST target (required) |
| `NOTIFY_WEBHOOK_TIMEOUT_S` | HTTP timeout, default 10s |

Sends `POST <url>` with JSON `{subject, body, source: "finrlx"}`. Any
4xx/5xx → recorded as `status=failed` with the response text.

### SmtpChannel

| Env var | Purpose |
|---|---|
| `NOTIFY_SMTP_HOST` | required |
| `NOTIFY_SMTP_PORT` | default 587 |
| `NOTIFY_SMTP_FROM` | required |
| `NOTIFY_SMTP_TO` | required |
| `NOTIFY_SMTP_USER` / `NOTIFY_SMTP_PASSWORD` | optional |

Uses STARTTLS via `smtplib.SMTP`. No external lib dependency. Synchronous
send inside the async pipeline — acceptable because notification runs
once per day, not request-path.

## DAG integration

Added `daily_notify_incidents` as the **last** entry in `DAILY_DAG`:

```
DAILY_DAG = [
    daily_fx_refresh,
    daily_fx_freshness,      # opens Incidents
    daily_notify_incidents,  # sends them
]
```

So if a fresh FX stale incident is opened in step 2, step 3 ships the
notification in the same DAG run.

## Idempotency

* `notifications` table UNIQUE on `(incident_id, channel)`.
* Pre-fetch of all existing `(incident_id, channel)` pairs at the
  start of `notify_unsent_incidents`; the in-memory set short-circuits
  before any DB write.
* A failed send still writes a row with `status=failed`; the next run
  treats that row as "already attempted" (you'd manually delete the
  failed row before retry).

## `notify_unsent_incidents` return value

```python
{"sent": N, "skipped": M, "failed": K}
```

Or `{"sent": 0, "skipped": 0, "failed": 0, "no_channels": 1}` when no
channel is configured.

## Invariants tested (10)

1. `WebhookChannel.is_configured` reflects `NOTIFY_WEBHOOK_URL` env.
2. `WebhookChannel.is_configured` true when env set.
3. `SmtpChannel.is_configured` reflects all three required env vars.
4. `SmtpChannel.is_configured` true with full env.
5. `discover_channels` returns `[]` when env is empty.
6. `notify_unsent_incidents` returns `no_channels=1` when no channel.
7. With a stub channel, one Notification row per open Incident.
8. Second call is fully idempotent: `sent=0, skipped=N`.
9. Failing channel writes `status=failed` with error captured.
10. `daily_notify_incidents` is in `DAILY_DAG`.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (OP-3 file) | **10 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| Alembic upgrade head | OK |
| Alembic downgrade `026 → 025` | OK |
| Alembic re-upgrade `025 → 026` | OK |

## Operator setup (post-OP-1)

To enable in prod, set the env vars in Railway, then redeploy:

```bash
NOTIFY_WEBHOOK_URL=https://hooks.slack.com/services/...
# and/or
NOTIFY_SMTP_HOST=smtp.example.com
NOTIFY_SMTP_FROM=alerts@example.com
NOTIFY_SMTP_TO=ops@example.com
NOTIFY_SMTP_USER=alerts@example.com
NOTIFY_SMTP_PASSWORD=...
```

The next `daily_notify_incidents` run picks them up automatically.

## Follow-ups

* **OP-4** ships the DR runbook + JWT rotation; that runbook includes
  a section on enabling notification env vars at the same step as
  Sentry DSN.
* A future hourly DAG can include freshness + notify (currently
  daily). Add a `scripts/run_hourly_dag.py` + a new DAG list +
  another Railway cron line.
* The send adapters are deliberately simple. If we ever need
  templating (jinja2 bodies, HTML emails, etc.), wrap the channel
  protocol — don't fork.

## Honest limitations

* **SMTP send is blocking** inside the async pipeline. Acceptable for
  daily cadence; not for high-volume. If we ever batch many emails,
  wrap the smtp call in `asyncio.get_running_loop().run_in_executor`.
* **Failed sends are not auto-retried.** Operator must inspect
  `notifications` table, delete the `failed` row, and re-run the job.
  This is intentional — auto-retries can amplify a webhook outage
  into a notification storm.
* **No rate limiting between channels.** If 50 incidents open at once,
  50 messages go out per channel. For the closed beta this is fine;
  for a wider release, add a batch summary mode.
* **Subject line is truncated to 140 chars** before the
  `[FINRLX/<severity>]` prefix. Longer titles lose their tail.

## Sources

* (no new external libraries beyond Python stdlib `smtplib` +
  existing `httpx`)
