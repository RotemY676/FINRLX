"""Phase 2 smoke tests: decision stages and comparison endpoints."""
import pytest


@pytest.mark.asyncio
async def test_decision_stages(client):
    """GET /api/v1/recommendations/{id}/stages returns pipeline stages."""
    # Get the current recommendation ID first
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200
    rec_id = r.json()["data"]["id"]

    # Fetch stages
    r = await client.get(f"/api/v1/recommendations/{rec_id}/stages")
    assert r.status_code == 200
    data = r.json()["data"]

    assert data["recommendation_id"] == rec_id
    assert data["selection"] is not None
    assert len(data["selection"]["included"]) == 2
    assert data["allocation"] is not None
    assert data["timing"] is not None
    assert data["risk_overlay"] is not None


@pytest.mark.asyncio
async def test_comparison_current(client):
    """GET /api/v1/comparison/current returns comparison data."""
    r = await client.get("/api/v1/comparison/current")
    assert r.status_code == 200
    data = r.json()["data"]

    assert data is not None
    assert data["benchmark_name"] == "Equal Weight"
    assert len(data["weights"]) == 2
    assert data["total_active_weight"] > 0
    assert data["concentration_top3_rec"] > 0

    # Each row has required fields
    row = data["weights"][0]
    assert "ticker" in row
    assert "recommendation_weight" in row
    assert "benchmark_weight" in row
    assert "delta" in row
