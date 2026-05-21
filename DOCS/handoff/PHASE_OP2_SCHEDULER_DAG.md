# Phase OP-2 — Daily DAG + JobRun Audit Trail

**Date:** 2026-05-21
**Base commit:** `8689c16` (OP-1 runbook)
**Track:** Phase OP — sub-phase 2 of 5.

## What this sub-phase ships

A persistent record of every scheduled-job execution (`JobRun` table),
a flat daily DAG (currently 2 jobs), a manual-trigger API, and a CLI
the operator schedules via Railway cron. **No new dependencies** —
intentionally chose Railway-cron-orchestrated execution over an
in-process APScheduler to keep the FastAPI process simple.

| Artifact | Path |
|---|---|
| Model | `backend/app/models/jobs.py` |
| Migration `025_job_runs` | `backend/migrations/versions/025_job_runs.py` |
| Persistence service | `backend/app/services/job_runs.py` |
| DAG definition | `backend/app/jobs/daily_dag.py` |
| API | `backend/app/api/v1/ops_jobs.py` |
| CLI | `backend/scripts/run_daily_dag.py` |
| Tests (12) | `backend/tests/test_phase_op2_scheduler.py` |

## DAG entries (current)

| job_key | Description |
|---|---|
| `daily_fx_refresh` | `FxService.refresh_rates_for_today()` — fetches all (base, quote) pairs from Frankfurter |
| `daily_fx_freshness` | `evaluate_freshness + emit_incidents_if_stale` — opens Incidents on stale FX |

Order matters: refresh before freshness so the watchdog never falsely
opens an incident on the same run that would have just filled the gap.

Future entries (planned, not yet wired):
* `daily_ingest_yfinance` — pulls fresh OHLCV via the existing
  yfinance adapter
* `daily_compute_features` — invokes the feature service
* `daily_run_engines` — replaces manual `/api/v1/engines/run`
* `daily_generate_recommendations` — runs the pipeline per active profile

When those are added, append them to `DAILY_DAG` in `daily_dag.py`;
each will get its own `JobRun` row automatically via `record_job`.

## API

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | `/api/v1/ops/jobs` | any auth | returns `{known_jobs, runs[]}` with optional `?job_key=` and `?limit=` |
| POST | `/api/v1/ops/jobs/{job_key}/run` | admin | manually trigger one job; 404 for unknown key, 403 for non-admin |

The GET endpoint is open to any authenticated user so a beta tester
can verify the system ran what was expected.

## `record_job` contract

```python
async with record_job(db, "my_job_key", triggered_by="schedule") as run:
    run.summary = "did 42 things"
```

* Creates a `JobRun` row with `status=open` before yielding.
* On success → `status=completed`, persists `run.summary`, sets
  `finished_at` and `duration_ms`.
* On exception → `status=failed`, persists the traceback into `error`,
  sets `finished_at` and `duration_ms`, **re-raises** so the caller can
  decide what to do.
* `_duration_ms_safe` coerces tz-naive (SQLite) ↔ tz-aware (Postgres)
  datetimes before subtracting, so the same code works in tests and
  in prod.

## CLI

```bash
python -m scripts.run_daily_dag
```

Output:
```
daily_dag: jobs_total=2 completed=2 failed=0
```

Add to Railway cron:
```
0 18 * * *  python -m scripts.run_daily_dag
```

(18:00 UTC = after ECB FX publish window.)

## Invariants tested (12)

1. JobRun writeable; `status` defaults to `"open"`.
2. `mark_completed` sets `summary`, `finished_at`, `duration_ms`.
3. `record_job` success → row ends with `status=completed`.
4. `record_job` failure → row ends with `status=failed`, `error` populated,
   exception re-raised.
5. `DAILY_DAG` contains both FX jobs (contract guard).
6. `run_daily_dag` records one row per job; `completed=[...]`.
7. `run_daily_dag` continues past a failing job (no abort).
8. `run_single_job("unknown")` raises `ValueError`.
9. GET `/ops/jobs` requires auth.
10. GET `/ops/jobs` returns `known_jobs` containing both FX entries.
11. POST `/ops/jobs/.../run` rejected for non-admin (403).
12. POST `/ops/jobs/nope/run` (admin) returns 404.

## Gate results (verified locally, 2026-05-21)

| Gate | Result |
|---|---|
| Backend pytest (OP-2 file) | **12 passed** |
| Backend pytest (full) | running — will report after green |
| Backend ruff | clean |
| Backend mypy | clean on `app/core/` |
| Alembic upgrade head | OK |
| Alembic downgrade `025 → 024` | OK |
| Alembic re-upgrade `024 → 025` | OK |

## Follow-ups

* **OP-3** wires `notifications` so each fresh `Incident` opened by
  `daily_fx_freshness` (or any future job) routes to webhook/email.
* When OP-5 brings in the heavier pipeline jobs (ingest/features/
  signals/recommendations), they slot into `DAILY_DAG` with no API
  change.
* A `/ops/jobs` UI panel can be added later. The data is already
  available via the JSON API for now.

## Why no APScheduler

Adding `apscheduler` would add ~3 transitive deps (`pytz`, `tzlocal`,
`importlib-metadata` if Py < 3.10) for a feature that Railway's cron
gives us for free. The CLI + cron approach keeps:

* the FastAPI process stateless (clean redeploys, no scheduler
  warm-up to worry about);
* every job durable in JobRun even if the cron orchestrator restarts;
* the same DAG runnable manually for debugging.

If we later want sub-daily scheduling (e.g. hourly freshness check),
the simplest add is a separate cron line — no code change.

## Honest limitations

* The CLI exits 0 even when some jobs fail (matches the runbook —
  durable failure is in JobRun, not exit code). Operators who want
  cron-failure on any job failure can pipe through `jq`/`grep` and
  exit-nonzero in their cron wrapper.
* `run_daily_dag` swallows exceptions per-job (by design). If a single
  job's failure should abort the rest, wrap that job in a wrapper that
  re-raises.
* No per-job timeout. If `daily_fx_refresh` hangs because Frankfurter
  is down, we wait on the network adapter's own 10s timeout
  (configured in `frankfurter_provider.py`). For more aggressive
  timeouts, wrap the call in `asyncio.wait_for`.

## Sources

* Railway cron documentation (Railway-native scheduled jobs).
* Existing `DOCS/handoff/ONCALL_RUNBOOK.md` operational patterns.
