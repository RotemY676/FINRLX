"""Phase OP-2 — JobRun lifecycle, DAG, and /ops/jobs endpoint contract.

Coverage:
* JobRun model writeable; status defaults to "open".
* JobRunService.create_open + mark_completed + mark_failed set fields.
* record_job context manager: success path records completed.
* record_job context manager: exception path records failed + re-raises.
* run_daily_dag executes every DAG entry; failures stay in JobRun.
* run_single_job(unknown_key) raises ValueError.
* GET /ops/jobs requires auth; lists known_jobs + recent runs.
* POST /ops/jobs/{key}/run rejected for non-admin (403).
* POST /ops/jobs/{key}/run 404 on unknown key.
"""
from __future__ import annotations

import secrets

import pytest
from sqlalchemy import select

from app.jobs.daily_dag import DAILY_DAG, run_daily_dag, run_single_job
from app.models.auth import EmailAllowlist
from app.models.jobs import JOB_STATUS_FAILED, JobRun
from app.services.job_runs import JobRunService, record_job


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client, *, role: str = "user") -> tuple[str, str]:
    from sqlalchemy import select as _select

    from app.models.auth import User
    from tests.conftest import test_session_factory

    email = f"op2-{role}-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    user_id = body["user"]["id"]
    access = body["tokens"]["access_token"]
    if role != "user":
        async with test_session_factory() as db:
            u = (
                await db.execute(_select(User).where(User.id == user_id))
            ).scalar_one()
            u.role = role
            await db.commit()
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "a-strong-password-12345"},
        )
        access = r.json()["tokens"]["access_token"]
    return user_id, access


# ── JobRunService + record_job ───────────────────────────────────────


@pytest.mark.asyncio
async def test_job_run_writeable_defaults_open():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        svc = JobRunService(db)
        run = await svc.create_open("test_job_writeable")
    assert run.status == "open"
    assert run.started_at is not None
    assert run.finished_at is None


@pytest.mark.asyncio
async def test_mark_completed_sets_duration():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        svc = JobRunService(db)
        run = await svc.create_open("test_job_completed")
        await svc.mark_completed(run, summary="hello")
    assert run.status == "completed"
    assert run.summary == "hello"
    assert run.finished_at is not None
    assert run.duration_ms is not None
    assert run.duration_ms >= 0


@pytest.mark.asyncio
async def test_record_job_success_marks_completed():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        async with record_job(db, "test_ctx_success") as run:
            run.summary = "done"

        row = (
            await db.execute(
                select(JobRun).where(JobRun.job_key == "test_ctx_success")
            )
        ).scalar_one()
    assert row.status == "completed"
    assert row.summary == "done"


@pytest.mark.asyncio
async def test_record_job_failure_marks_failed_and_reraises():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        with pytest.raises(RuntimeError, match="boom"):
            async with record_job(db, "test_ctx_failure"):
                raise RuntimeError("boom")

        row = (
            await db.execute(
                select(JobRun).where(JobRun.job_key == "test_ctx_failure")
            )
        ).scalar_one()
    assert row.status == JOB_STATUS_FAILED
    assert row.error is not None
    assert "boom" in row.error


# ── DAG ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dag_known_jobs_match_module_export():
    keys = [k for k, _ in DAILY_DAG]
    # The DAG must always include FX refresh + freshness watchdog —
    # the OP-2 contract.
    assert "daily_fx_refresh" in keys
    assert "daily_fx_freshness" in keys


@pytest.mark.asyncio
async def test_run_daily_dag_records_one_row_per_job(monkeypatch):
    """Every job in DAILY_DAG produces a JobRun row."""
    from app.jobs import daily_dag as dag_mod
    from tests.conftest import test_session_factory

    # Replace the actual job funcs with deterministic stubs so we don't
    # depend on the live Frankfurter API in CI.
    async def ok(_db):
        return "ok"

    monkeypatch.setattr(
        dag_mod, "DAILY_DAG",
        [("noop_a", ok), ("noop_b", ok)],
    )

    async with test_session_factory() as db:
        result = await run_daily_dag(db, triggered_by="test")
        assert result["completed"] == ["noop_a", "noop_b"]
        assert result["failed"] == []

        rows = (
            await db.execute(
                select(JobRun).where(JobRun.job_key.in_(("noop_a", "noop_b")))
            )
        ).scalars().all()
        # at least 2; tests are session-scoped so we don't assert exact equality
        assert {r.job_key for r in rows} >= {"noop_a", "noop_b"}
        for r in rows:
            assert r.status == "completed"


@pytest.mark.asyncio
async def test_run_daily_dag_continues_past_failure(monkeypatch):
    from app.jobs import daily_dag as dag_mod
    from tests.conftest import test_session_factory

    async def ok(_db):
        return "fine"

    async def bang(_db):
        raise RuntimeError("intentional failure")

    monkeypatch.setattr(
        dag_mod, "DAILY_DAG",
        [("fail_first", bang), ("ok_after", ok)],
    )

    async with test_session_factory() as db:
        result = await run_daily_dag(db, triggered_by="test")
    assert "ok_after" in result["completed"]
    assert any(s.startswith("fail_first") for s in result["failed"])


@pytest.mark.asyncio
async def test_run_single_job_unknown_key_raises():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        with pytest.raises(ValueError):
            await run_single_job(db, "nonexistent_job")


# ── API ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ops_jobs_list_requires_auth(client):
    r = await client.get("/api/v1/ops/jobs")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_ops_jobs_list_returns_known_jobs(client):
    _, token = await _signup(client)
    r = await client.get("/api/v1/ops/jobs", headers=_bearer(token))
    assert r.status_code == 200, r.text
    body = r.json()["data"]
    assert "daily_fx_refresh" in body["known_jobs"]
    assert "daily_fx_freshness" in body["known_jobs"]
    assert isinstance(body["runs"], list)


@pytest.mark.asyncio
async def test_ops_jobs_run_rejected_for_non_admin(client):
    _, user_token = await _signup(client)
    r = await client.post(
        "/api/v1/ops/jobs/daily_fx_refresh/run", headers=_bearer(user_token)
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_ops_jobs_run_404_for_unknown(client):
    _, admin_token = await _signup(client, role="admin")
    r = await client.post(
        "/api/v1/ops/jobs/nope/run", headers=_bearer(admin_token)
    )
    assert r.status_code == 404
