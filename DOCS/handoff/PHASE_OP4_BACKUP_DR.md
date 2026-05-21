# Phase OP-4 — Backup + DR Runbook + JWT Rotation + GDPR Export

**Date:** 2026-05-21
**Base commit:** `7bc9318` (OP-3)
**Track:** Phase OP — sub-phase 4 of 5.

## What this sub-phase ships

A complete DR runbook + two CLI scripts the runbook references.

| Artifact | Path |
|---|---|
| DR runbook | `DOCS/handoff/DR_RUNBOOK.md` |
| JWT rotation script | `backend/scripts/rotate_jwt_secret.py` |
| GDPR per-user export | `backend/scripts/export_user_data.py` |
| Tests | `backend/tests/test_phase_op4_jwt_rotation.py` |

## Runbook scope

* Database loss + restore from off-Railway dump
* Database corruption (bad migration / accidental DROP)
* JWT secret compromise + rotation
* GDPR / right-to-erasure (data export + erase SQL)
* Operational gotchas (test restores on staging, never delete
  audit_events, etc.)

The runbook is the canonical place to start any DR incident. It links
to existing assets (ONCALL_RUNBOOK, deploy_smoke.sh, manage_allowlist)
so no information is duplicated.

## JWT rotation script

`scripts/rotate_jwt_secret.py`:

* `--print-new-secret` → emits a fresh `token_urlsafe(48)` candidate
  (does not modify env; operator pastes it into Railway).
* No flags → dry-run: counts active refresh tokens, prints a hint.
* `--confirm` → revokes every non-revoked `RefreshToken` row, writes
  one `AuditEvent` with `action="rotate_jwt_secret"`, prints the
  number revoked.

Used in two places in the DR runbook:
1. Routine paranoid rotation (quarterly recommended).
2. Suspected leak → out-of-band JWT_SECRET change in Railway, then this
   script to terminate the in-flight sessions.

## GDPR export script

`scripts/export_user_data.py --email <email>` produces a JSON bundle
of:

* the `users` row
* the current `investor_profiles` row
* every `investor_profile_revisions` row
* every `paper_portfolios` row owned by the user
* every `audit_events` row where the user is the actor

Output goes to stdout; the runbook recommends piping to a file +
delivering via a secure channel.

## Erasure (manual, by design)

Erasure is SQL-driven in the runbook, **not** scripted, because:

* Every erasure should be reviewed manually (legal sign-off + ticket
  reference).
* The order matters (foreign-key-ish dependencies, even though we
  don't enforce FKs at the DB layer).
* `audit_events` keeps a hashed record of the erasure itself for the
  accountability requirement of GDPR Article 5.2 — that final step is
  in the SQL block.

## Invariants tested (3)

1. Running `_revoke_all_refresh_tokens` against an in-memory DB with
   one active token revokes that token + writes an `AuditEvent` with
   the supplied `triggered_by`.
2. Running it a second time leaves already-revoked tokens alone
   (revoked_at is preserved, not re-stamped).
3. `_dump_new_secret()` returns a URL-safe alphanumeric string with
   length ≥ 32.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (OP-4 file) | **3 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean across `app/` + `scripts/` |
| Backend mypy | clean on `app/core/` |

## Follow-ups

* **OP-5** ships framework upgrades (FastAPI + Next). After OP-5
  ships, run one full drill: take a dump, restore to staging,
  re-upgrade, smoke. Record in the runbook's drill log table.
* The DR runbook's "Drill log" table has only one row (this commit's
  authoring); after OP-1 lands we should record at least one
  successful round-trip drill.
* GDPR erasure could be wrapped in a `manage_user.py erase --email`
  CLI with the same SQL embedded. We deliberately keep it manual
  for the closed beta.

## Honest limitations

* **No off-Railway backup is actually running yet.** The runbook
  describes how to enable one (cron line provided). OP-1 deploy + an
  operator action are needed to make this real.
* **The drill log is empty.** A documented procedure that's never been
  exercised is just hope.
* The `rotate_jwt_secret` script doesn't itself rotate the env var —
  that's intentional (env writes go through Railway, not Python). The
  script is the safe **after**-rotation cleanup.
* The GDPR export script doesn't include downstream RL/ML/research
  data. Those tables are operator-owned (research mode, hidden from
  beta users) and don't carry user-identifiable data per current code.
  If that ever changes, extend the export accordingly.

## Sources

* GDPR Articles 17 (erasure) and 20 (portability)
* PostgreSQL `pg_dump` / `pg_restore` documentation
* Railway PG backup documentation
* Existing `DOCS/handoff/ONCALL_RUNBOOK.md`
