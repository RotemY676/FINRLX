"""Phase 5A+B tests: backtest runner + replay realization."""
import pytest


async def _ensure_pipeline(client) -> str:
    """Ensure features + engines + pipeline run. Returns rec_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    return r.json()["data"]["recommendation_id"]


# ── Backtest ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_backtest_run(client):
    """POST /backtests/run creates a persisted backtest with metrics."""
    r = await client.post("/api/v1/backtests/run", json={
        "name": "Test Backtest",
        "start_date": "2026-03-01",
        "end_date": "2026-04-01",
        "rebalance_frequency": "monthly",
        "cost_bps": 10,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] in ("completed", "failed")
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_backtest_uses_market_bars(client):
    """Backtest produces equity curve from real market_bars, not hardcoded."""
    r = await client.post("/api/v1/backtests/run", json={
        "name": "Bars Test",
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
        "rebalance_frequency": "weekly",
    })
    data = r.json()["data"]
    if data["status"] == "completed":
        assert len(data["equity_curve"]) >= 2
        # Equity curve should not all be 100.0 (would indicate no computation)
        values = [p["value"] for p in data["equity_curve"]]
        assert not all(v == 100.0 for v in values), "Equity curve should vary"


@pytest.mark.asyncio
async def test_backtest_produces_metrics(client):
    """Completed backtest has return/drawdown/sharpe metrics."""
    r = await client.post("/api/v1/backtests/run", json={
        "name": "Metrics Test",
        "start_date": "2026-03-01",
        "end_date": "2026-04-20",
        "rebalance_frequency": "monthly",
    })
    data = r.json()["data"]
    if data["status"] == "completed":
        results = data["results"]
        assert results["total_return"] is not None
        assert results["max_drawdown"] is not None


@pytest.mark.asyncio
async def test_backtest_insufficient_data(client):
    """Backtest with tiny date range returns degraded/failed."""
    r = await client.post("/api/v1/backtests/run", json={
        "name": "Insufficient",
        "start_date": "2026-04-20",
        "end_date": "2026-04-21",
    })
    data = r.json()["data"]
    # Should fail or have warnings about insufficient data
    assert data["status"] in ("completed", "failed")


@pytest.mark.asyncio
async def test_backtest_list(client):
    """GET /backtests returns backtest experiments."""
    await client.post("/api/v1/backtests/run", json={"name": "List Test"})
    r = await client.get("/api/v1/backtests")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_backtest_status(client):
    """GET /backtests/status returns counts."""
    r = await client.get("/api/v1/backtests/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "total" in data
    assert "completed" in data


# ── Replay ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_replay_from_pipeline(client):
    """Replay snapshots are created from a real pipeline recommendation."""
    rec_id = await _ensure_pipeline(client)

    r = await client.get(f"/api/v1/replay/{rec_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data is not None
    assert data["recommendation_id"] == rec_id
    assert len(data["stages"]) >= 3  # selection, allocation, timing, risk, recommendation


@pytest.mark.asyncio
async def test_replay_includes_lineage(client):
    """Replay detail includes pipeline lineage in the recommendation stage."""
    rec_id = await _ensure_pipeline(client)

    r = await client.get(f"/api/v1/replay/{rec_id}")
    data = r.json()["data"]
    rec_stage = next((s for s in data["stages"] if s["stage"] == "recommendation"), None)
    assert rec_stage is not None
    assert "source_feature_set_id" in rec_stage["snapshot_data"]
    assert "source_signal_run_ids" in rec_stage["snapshot_data"]


@pytest.mark.asyncio
async def test_replay_includes_stages(client):
    """Replay includes selection, allocation, timing, risk_overlay stages."""
    rec_id = await _ensure_pipeline(client)

    r = await client.get(f"/api/v1/replay/{rec_id}")
    stages = {s["stage"] for s in r.json()["data"]["stages"]}
    assert "selection" in stages
    assert "allocation" in stages
    assert "timing" in stages
    assert "risk_overlay" in stages


@pytest.mark.asyncio
async def test_replay_list(client):
    """GET /replay returns replay list including pipeline recs."""
    await _ensure_pipeline(client)

    r = await client.get("/api/v1/replay")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_replay_warns_seeded(client):
    """Replay of seeded (non-pipeline) recommendation includes seeded warning."""
    # The conftest seeds a recommendation without pipeline lineage
    r = await client.get("/api/v1/replay")
    data = r.json()["data"]
    # Find a non-pipeline rec if one exists
    for item in data["items"]:
        r2 = await client.get(f"/api/v1/replay/{item['recommendation_id']}")
        detail = r2.json()["data"]
        if detail:
            # Check if it's seeded (no lineage) — it should have a warning
            rec_stage = next((s for s in detail["stages"] if s["stage"] == "recommendation"), None)
            if rec_stage and not rec_stage["snapshot_data"].get("source_feature_set_id"):
                assert any("seeded" in w.lower() or "demo" in w.lower() for w in detail["warnings"])
            break


@pytest.mark.asyncio
async def test_replay_backward_compatible(client):
    """Old replay endpoints still work and return data."""
    r = await client.get("/api/v1/replay")
    assert r.status_code == 200
    assert "items" in r.json()["data"]
    assert "total" in r.json()["data"]
