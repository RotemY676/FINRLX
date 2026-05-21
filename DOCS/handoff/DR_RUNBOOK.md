# Disaster-Recovery Runbook

**Date:** 2026-05-21
**Owner:** Operator
**Sources:** Phase OP-4 (this), Phase MVP-7 ONCALL_RUNBOOK, Railway docs.

## Scope

This runbook covers the four DR scenarios the closed beta needs to
survive:

1. **Database loss** (Railway PG instance vanishes).
2. **Database corruption** (bad migration, accidental DROP).
3. **JWT secret compromise** (suspected leak).
4. **GDPR / right-to-erasure request** from a beta tester.

It does **not** cover region-level Railway outages (we're on a single
region) or compromised admin accounts (the closed-beta threat model
assumes the operator is trusted).

## 1 — Backups: enable + verify

### Railway Postgres point-in-time backups

* Railway free-tier Postgres includes daily snapshots; Pro tier adds
  point-in-time restore (PITR).
* **Enable PITR** in the Railway dashboard for the FINRLX project.
* **Snapshot retention** is 7 days on free, 30 days on Pro.

### Off-Railway nightly dump (recommended)

Add a Railway cron line:

```
0 3 * * *  pg_dump --no-owner --no-acl --clean --if-exists -Fc \
            "$DATABASE_URL" \
            -f /tmp/finrlx-$(date +\%F).dump && \
            curl -fsSL -X PUT \
              --data-binary @/tmp/finrlx-$(date +\%F).dump \
              "$BACKUP_UPLOAD_URL/$(date +\%F).dump"
```

`BACKUP_UPLOAD_URL` is a presigned URL or a service like Bunny.net
storage / Backblaze B2 / S3. Retain at least 30 days off-Railway.

### Verify backup restore (monthly drill)

Once a month, restore the latest dump to a staging DB and run the
gate suite:

```bash
# 1. Provision a fresh PG instance (e.g. local docker).
docker run --rm -d --name finrlx-staging -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:16

# 2. Restore.
pg_restore -d "postgresql://postgres:test@localhost:5433/postgres" /tmp/latest.dump

# 3. Migrate (idempotent).
DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5433/postgres \
  alembic upgrade head

# 4. Smoke.
DATABASE_URL=... python -m pytest tests/test_smoke.py -x -q
```

A passing smoke means the backup is restorable. Record the result in
this file's drill log below.

### Drill log

| Date | Backup taken | Restore tested | Verifier | Notes |
|---|---|---|---|---|
| 2026-05-21 | (none — pre-OP-1) | — | — | OP-4 runbook authored; first drill blocked on OP-1 live deploy |

## 2 — Restore from backup

### Scenario A: Railway PG vanished

1. In Railway, re-add a Postgres plugin to the project.
2. Note the new `DATABASE_URL`.
3. From your latest off-Railway dump:
   ```
   pg_restore -d "$DATABASE_URL" /path/to/latest.dump
   ```
4. Set the new `DATABASE_URL` in the backend service's env vars.
5. Redeploy the backend.
6. Run `scripts/deploy_smoke.sh` against the new URL.

### Scenario B: Last migration broke the schema

1. Identify the bad migration revision (alembic prints it in logs).
2. Downgrade locally + on prod:
   ```
   alembic downgrade <previous_revision_id>
   ```
3. Patch the migration in a follow-up commit.
4. `alembic upgrade head` again.

If the downgrade itself fails, restore from the previous night's dump
(scenario A).

## 3 — JWT secret rotation

When you suspect `JWT_SECRET` has leaked:

```bash
# 1. Generate a fresh secret + see how many active sessions you have.
python -m scripts.rotate_jwt_secret --print-new-secret

# (Copy the printed secret.)

# 2. Set the new JWT_SECRET in Railway env vars + redeploy.

# 3. Once the new build is healthy, revoke all existing refresh tokens
#    so the leaked-secret holders can't mint fresh access tokens via
#    the refresh path:
python -m scripts.rotate_jwt_secret --confirm --triggered-by "security-incident-2026-XX"
```

After step 3, every user must re-login. The script also writes an
`audit_events` row tagged `action=rotate_jwt_secret`.

## 4 — GDPR / right-to-erasure

### Export (Right to data portability)

```bash
python -m scripts.export_user_data --email tester@example.com > /tmp/tester.json
```

The JSON contains: user row, current investor profile, every profile
revision, every paper portfolio they own, every audit event where
they were the actor.

Deliver `/tmp/tester.json` via secure channel.

### Erasure

```sql
-- Manual, because this requires inspection + sign-off.
-- 1. Identify the user.
SELECT id, email, created_at FROM users WHERE email = 'tester@example.com';

-- 2. Inspect related rows.
SELECT COUNT(*) FROM investor_profiles WHERE user_id = '<user-id>';
SELECT COUNT(*) FROM investor_profile_revisions WHERE user_id = '<user-id>';
SELECT COUNT(*) FROM refresh_tokens WHERE user_id = '<user-id>';
SELECT COUNT(*) FROM paper_portfolios WHERE user_id = '<user-id>';

-- 3. Delete in dependency order.
DELETE FROM investor_profile_revisions WHERE user_id = '<user-id>';
DELETE FROM investor_profiles WHERE user_id = '<user-id>';
DELETE FROM refresh_tokens WHERE user_id = '<user-id>';
DELETE FROM paper_portfolios WHERE user_id = '<user-id>';
DELETE FROM email_allowlist WHERE email = 'tester@example.com';
DELETE FROM users WHERE id = '<user-id>';

-- 4. Log the deletion. audit_events keep a record for GDPR's own
--    accountability requirement — we keep this entry even after the
--    user row is gone.
INSERT INTO audit_events (id, actor, action, object_type, occurred_at, details)
VALUES (
  gen_random_uuid(),
  'operator',
  'gdpr_erasure',
  'user',
  NOW(),
  '{"email_hash": "<sha256 of email>", "ticket": "<your-ticket-ref>"}'::jsonb
);
```

Always run in a transaction; commit only after the count assertions look right.

## 5 — Operational gotchas

* **Always test restores on a staging instance first.** A restore that
  succeeds locally but kills prod because of schema drift is the
  classic mistake.
* **Never delete `audit_events` rows.** They survive user deletions and
  underpin the legal record.
* **The `JWT_SECRET` rotation script is idempotent.** Re-running it
  after all tokens are revoked simply revokes zero rows and writes a
  fresh audit entry — safe.
* **Backup destinations should be off-Railway.** A Railway-wide issue
  that wipes your project also wipes its backups. The off-Railway
  dump is your real safety net.

## 6 — Where the code lives

| Concern | File |
|---|---|
| Rotate JWT secret | `backend/scripts/rotate_jwt_secret.py` |
| GDPR export | `backend/scripts/export_user_data.py` |
| Smoke test | `backend/scripts/deploy_smoke.sh` |
| Allowlist management | `backend/scripts/manage_allowlist.py` |
| Migrations | `backend/migrations/versions/` |

## 7 — Sources

* Railway documentation on PG backups & PITR
* PostgreSQL docs on `pg_dump` / `pg_restore`
* GDPR Article 17 (right to erasure) — informs the SQL flow above
* Existing `DOCS/handoff/ONCALL_RUNBOOK.md` operational baseline
