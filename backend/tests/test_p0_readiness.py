"""US-P0-08 — unified readiness endpoint (admin-only, fail-closed)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.core.auth import hash_password, issue_access_token
from app.models.auth import User
from app.services.readiness import build_readiness
from tests.conftest import test_session_factory as AsyncSessionLocal

READINESS_PATH = "/api/v1/ops/readiness"


def _uid() -> str:
    return str(uuid.uuid4())


async def _headers(role: str) -> dict[str, str]:
    uid = _uid()
    async with AsyncSessionLocal() as db:
        db.add(User(id=uid, email=f"rdy-{uid[:8]}@example.com",
                    password_hash=hash_password("x"), is_active=True, role=role))
        await db.commit()
    tok, _ = issue_access_token(user_id=uid, role=role)
    return {"Authorization": f"Bearer {tok}"}


@pytest.mark.asyncio
async def test_requires_admin(client):
    assert (await client.get(READINESS_PATH)).status_code == 401
    assert (await client.get(READINESS_PATH, headers=await _headers("user"))).status_code == 403


@pytest.mark.asyncio
async def test_admin_gets_readiness_report(client):
    r = await client.get(READINESS_PATH, headers=await _headers("admin"))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    names = {c["name"] for c in data["components"]}
    assert {"market_data", "fx", "providers", "jobs"} <= names
    assert data["overall"] in {"ready", "degraded", "unavailable"}
    assert isinstance(data["ready"], bool)
    # overall is the worst component; ready iff overall == ready
    assert data["ready"] == (data["overall"] == "ready")


@pytest.mark.asyncio
async def test_seed_market_data_is_ready_but_fx_unavailable():
    """The seeded MarketBars are fresh; no FX rates are seeded → fail closed."""
    async with AsyncSessionLocal() as db:
        report = await build_readiness(db, now=datetime.now(UTC))
    by_name = {c.name: c for c in report.components}
    assert by_name["market_data"].status in {"ready", "degraded"}
    assert by_name["fx"].status == "unavailable"  # no fx seed → not silently ready
    # Overall can never be better than its worst component.
    assert report.overall == "unavailable"
    assert report.ready is False


@pytest.mark.asyncio
async def test_failed_job_run_degrades_jobs_component():
    """A failed job run must surface as a degraded jobs component with scope."""
    from app.models.jobs import JOB_STATUS_FAILED, JobRun

    async with AsyncSessionLocal() as db:
        db.add(JobRun(id=_uid(), job_key="price_refresh", status=JOB_STATUS_FAILED,
                      started_at=datetime.now(UTC), error="boom"))
        await db.commit()
        report = await build_readiness(db, now=datetime.now(UTC))

    jobs = next(c for c in report.components if c.name == "jobs")
    assert jobs.status == "degraded"
    assert "price_refresh" in jobs.affected


@pytest.mark.asyncio
async def test_component_failure_is_fail_closed(monkeypatch):
    """A raising evaluator must degrade to 'unavailable', never crash or pass."""
    async def _boom(*a, **k):
        raise RuntimeError("provider backend down")

    monkeypatch.setattr(
        "app.services.readiness.IntegrationsService.get_provider_readiness", _boom
    )
    async with AsyncSessionLocal() as db:
        report = await build_readiness(db, now=datetime.now(UTC))
    providers = next(c for c in report.components if c.name == "providers")
    assert providers.status == "unavailable"
    assert "evaluation failed" in (providers.detail or "")
