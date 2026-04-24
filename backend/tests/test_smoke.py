"""Smoke tests: verify core API endpoints return expected shapes with real data.

These tests use an in-memory SQLite database seeded with test data.
They verify the end-to-end path: HTTP request -> FastAPI -> SQLAlchemy -> response.
"""
import pytest


@pytest.mark.asyncio
async def test_root_health(client):
    """GET /health returns ok status and version."""
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_api_v1_health(client):
    """GET /api/v1/health returns ok with database connected."""
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert "meta" in body
    assert body["meta"]["api_version"] == "v1"
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] == "connected"


@pytest.mark.asyncio
async def test_overview(client):
    """GET /api/v1/overview returns recommendation summary and health."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200
    body = r.json()

    # Envelope structure
    assert "meta" in body
    assert "data" in body

    data = body["data"]
    assert "current_recommendation" in data
    assert "health" in data

    rec = data["current_recommendation"]
    assert rec is not None, "Expected seeded recommendation"
    assert rec["status"] == "published"
    assert rec["total_positions"] == 2
    assert rec["confidence"]["model_confidence"] == 0.85
    assert rec["confidence"]["data_confidence"] == 0.90
    assert rec["confidence"]["operational_confidence"] == 0.95

    health = data["health"]
    assert health["source_freshness_ok"] is True


@pytest.mark.asyncio
async def test_current_recommendation(client):
    """GET /api/v1/recommendations/current returns full recommendation with weights."""
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200
    body = r.json()

    detail = body["data"]
    assert detail is not None, "Expected seeded recommendation"
    assert detail["status"] == "published"
    assert len(detail["weights"]) == 2

    tickers = {w["ticker"] for w in detail["weights"]}
    assert tickers == {"AAPL", "MSFT"}

    aapl = next(w for w in detail["weights"] if w["ticker"] == "AAPL")
    assert aapl["target_weight"] == 0.60
    assert aapl["stance"] == "overweight"

    msft = next(w for w in detail["weights"] if w["ticker"] == "MSFT")
    assert msft["target_weight"] == 0.40
    assert msft["stance"] == "underweight"


@pytest.mark.asyncio
async def test_recommendation_by_id_not_found(client):
    """GET /api/v1/recommendations/{bad_id} returns 404."""
    r = await client.get("/api/v1/recommendations/nonexistent-id")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_overview_envelope_structure(client):
    """Verify the API response envelope matches doc 12 contract."""
    r = await client.get("/api/v1/overview")
    body = r.json()

    meta = body["meta"]
    assert "api_version" in meta
    assert "generated_at" in meta
    assert isinstance(meta["warnings"], list)
