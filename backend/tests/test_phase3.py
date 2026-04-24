"""Phase 3 smoke tests: replay, backtests, paper portfolio endpoints."""
import pytest


@pytest.mark.asyncio
async def test_replay_list(client):
    """GET /api/v1/replay returns list of replays."""
    r = await client.get("/api/v1/replay")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_replay_detail(client):
    """GET /api/v1/replay/{id} returns replay detail when snapshots exist."""
    # Get rec id first
    r = await client.get("/api/v1/recommendations/current")
    rec_id = r.json()["data"]["id"]

    r = await client.get(f"/api/v1/replay/{rec_id}")
    assert r.status_code == 200
    # May be None if no snapshots in test DB — that's OK for the test fixture
    # The endpoint still returns 200 with data=None and a warning


@pytest.mark.asyncio
async def test_backtests_list(client):
    """GET /api/v1/backtests returns list."""
    r = await client.get("/api/v1/backtests")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_backtest_not_found(client):
    """GET /api/v1/backtests/{bad_id} returns 404."""
    r = await client.get("/api/v1/backtests/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_paper_current(client):
    """GET /api/v1/paper/current returns paper portfolio or null."""
    r = await client.get("/api/v1/paper/current")
    assert r.status_code == 200
    # data may be null if no paper portfolio in test DB — endpoint still returns 200
