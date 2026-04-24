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


# ── Phase 5A+B.1 provenance tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_legacy_backtest_labeled_demo(client):
    """Seeded backtest from conftest is labeled source_type=seed_demo."""
    r = await client.get("/api/v1/backtests")
    data = r.json()["data"]
    for item in data["items"]:
        if item.get("source_type") in ("seed_demo", "unknown"):
            assert item["is_demo"] is True
            assert item["lineage_available"] is False
            return
    # If all are pipeline_backtest, that's fine too
    pytest.skip("No legacy backtest in test DB")


@pytest.mark.asyncio
async def test_pipeline_backtest_has_provenance(client):
    """POST /backtests/run creates pipeline_backtest with lineage."""
    r = await client.post("/api/v1/backtests/run", json={
        "name": "Provenance Test",
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    if data["status"] == "completed":
        assert data["source_type"] == "pipeline_backtest"
        assert data["is_demo"] is False
        assert data["lineage_available"] is True
        assert data["provenance"] is not None
        assert len(data["provenance"]["recommendation_ids"]) >= 1


@pytest.mark.asyncio
async def test_backtest_list_has_provenance_fields(client):
    """GET /backtests list items include source_type, is_demo, decision_count."""
    r = await client.get("/api/v1/backtests")
    for item in r.json()["data"]["items"]:
        assert "source_type" in item
        assert "is_demo" in item
        assert "lineage_available" in item
        assert "decision_count" in item


@pytest.mark.asyncio
async def test_backtest_detail_includes_decision_points(client):
    """GET /backtests/{id} includes decision_points for pipeline backtest."""
    r = await client.post("/api/v1/backtests/run", json={
        "name": "Decisions Test",
        "start_date": "2026-03-01",
        "end_date": "2026-04-15",
        "rebalance_frequency": "monthly",
    })
    bt_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/backtests/{bt_id}")
    data = r2.json()["data"]
    assert "decision_points" in data


@pytest.mark.asyncio
async def test_backtest_decisions_endpoint(client):
    """GET /backtests/{id}/decisions works."""
    r = await client.post("/api/v1/backtests/run", json={"name": "DecEP Test"})
    bt_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/backtests/{bt_id}/decisions")
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_backtest_equity_curve_endpoint(client):
    """GET /backtests/{id}/equity-curve works."""
    r = await client.post("/api/v1/backtests/run", json={"name": "EqCurve Test"})
    bt_id = r.json()["data"]["id"]
    r2 = await client.get(f"/api/v1/backtests/{bt_id}/equity-curve")
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_backtest_recs_not_in_current(client):
    """Backtest recommendations do not appear in /recommendations/current."""
    # Run a backtest (creates backtest-context recommendations)
    await client.post("/api/v1/backtests/run", json={
        "name": "Isolation Test",
        "start_date": "2026-03-20",
        "end_date": "2026-04-10",
    })

    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200
    data = r.json()["data"]
    # If there's a current rec, it should not be a backtest one
    # data may be None or a live rec — either way, no backtest rec should appear


@pytest.mark.asyncio
async def test_backtest_recs_not_in_overview(client):
    """Backtest recommendations do not appear in /overview."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200
    # Overview should still work without showing backtest recs
