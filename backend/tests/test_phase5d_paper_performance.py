"""Phase 5D tests: paper portfolio performance, trades, attribution."""
import pytest


async def _create_test_paper(client) -> str:
    """Create a test paper portfolio from a draft recommendation. Returns portfolio_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    rec_id = r.json()["data"]["recommendation_id"]
    r = await client.post(f"/api/v1/paper/from-recommendation/{rec_id}",
                          json={"allow_unpublished": True})
    return r.json()["data"]["id"]


# ── Trades ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_creation_creates_trades(client):
    """Creating a paper portfolio generates simulated buy trades."""
    pp_id = await _create_test_paper(client)
    r = await client.get(f"/api/v1/paper/{pp_id}/trades")
    assert r.status_code == 200
    trades = r.json()["data"]
    assert len(trades) >= 1
    for t in trades:
        assert t["side"] == "buy"
        assert t["quantity"] > 0
        assert t["price"] > 0


# ── Valuation snapshots ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_valuation_snapshots_generated(client):
    """Recompute generates valuation snapshots from market_bars."""
    pp_id = await _create_test_paper(client)
    r = await client.post(f"/api/v1/paper/{pp_id}/performance/recompute")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "computed"
    assert data["snapshot_count"] >= 1


@pytest.mark.asyncio
async def test_valuations_endpoint(client):
    """GET valuations returns time-series points."""
    pp_id = await _create_test_paper(client)
    await client.post(f"/api/v1/paper/{pp_id}/performance/recompute")
    r = await client.get(f"/api/v1/paper/{pp_id}/valuations")
    assert r.status_code == 200
    points = r.json()["data"]
    assert len(points) >= 1
    for p in points:
        assert "date" in p
        assert "portfolio_value" in p


# ── Performance summary ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_performance_summary(client):
    """Performance summary computes return and drawdown."""
    pp_id = await _create_test_paper(client)
    await client.post(f"/api/v1/paper/{pp_id}/performance/recompute")
    r = await client.get(f"/api/v1/paper/{pp_id}/performance")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "computed"
    assert data["total_return"] is not None
    assert data["max_drawdown"] is not None
    assert data["trade_count"] >= 1


@pytest.mark.asyncio
async def test_performance_no_data(client):
    """Performance without snapshots returns no_data status."""
    pp_id = await _create_test_paper(client)
    r = await client.get(f"/api/v1/paper/{pp_id}/performance")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "no_data"


# ── Attribution ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_asset_attribution(client):
    """Asset attribution returns per-asset contributions."""
    pp_id = await _create_test_paper(client)
    r = await client.get(f"/api/v1/paper/{pp_id}/attribution/assets")
    assert r.status_code == 200
    attrib = r.json()["data"]
    assert len(attrib) >= 1
    for a in attrib:
        assert "ticker" in a
        assert "asset_return" in a
        assert "contribution" in a


@pytest.mark.asyncio
async def test_decision_attribution(client):
    """Decision attribution returns per-event history."""
    pp_id = await _create_test_paper(client)
    r = await client.get(f"/api/v1/paper/{pp_id}/attribution/decisions")
    assert r.status_code == 200
    attrib = r.json()["data"]
    assert len(attrib) >= 1
    assert attrib[0]["event_type"] == "creation"


# ── Provenance ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seed_demo_not_real_performance(client):
    """Seed/demo paper portfolio does not produce recommendation_paper performance."""
    r = await client.get("/api/v1/paper")
    data = r.json()["data"]
    for p in data:
        if p["source_type"] in ("seed_demo", "unknown"):
            assert p["is_demo"] is True
