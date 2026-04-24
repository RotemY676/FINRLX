"""Phase 4A tests: ingestion layer — market bars, news events, manifests, service, endpoints.

Phase 4A.1 addendum: stable seed, news idempotency, failed status visibility.
"""
import pytest


# ── Model / table availability ────────────────────────────────────────

@pytest.mark.asyncio
async def test_market_bar_table_exists(client):
    """Seed conftest created market_bars rows; verify they are queryable."""
    r = await client.get("/api/v1/ingest/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_bar_count"] >= 3  # at least a few weekday bars from conftest


@pytest.mark.asyncio
async def test_ingestion_manifests_seeded(client):
    """Conftest created at least one manifest."""
    r = await client.get("/api/v1/ingest/manifests")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1
    assert data["items"][0]["kind"] == "bars"
    assert data["items"][0]["status"] == "completed"


# ── GET /ingest/status ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_status_structure(client):
    """GET /ingest/status returns sources list with freshness info."""
    r = await client.get("/api/v1/ingest/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "sources" in data
    assert "total_bar_count" in data
    assert "total_news_count" in data
    assert isinstance(data["sources"], list)


# ── POST /ingest/bars ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_bars_default(client):
    """POST /ingest/bars with default params creates bars and manifest."""
    r = await client.post("/api/v1/ingest/bars", json={"source": "local"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["rows_ingested"] > 0
    assert "manifest_id" in data


@pytest.mark.asyncio
async def test_ingest_bars_specific_ticker(client):
    """POST /ingest/bars for a specific ticker with non-overlapping dates."""
    r = await client.post("/api/v1/ingest/bars", json={
        "source": "local-specific",
        "tickers": ["AAPL"],
        "date_from": "2025-01-06",
        "date_to": "2025-01-17",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["rows_ingested"] > 0


@pytest.mark.asyncio
async def test_ingest_bars_unknown_ticker(client):
    """POST /ingest/bars with unknown ticker returns failed manifest."""
    r = await client.post("/api/v1/ingest/bars", json={
        "source": "local",
        "tickers": ["ZZZZ"],
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "failed"
    assert data["rows_ingested"] == 0


# ── POST /ingest/news ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_news_default(client):
    """POST /ingest/news with default params creates news events and manifest."""
    r = await client.post("/api/v1/ingest/news", json={"source": "local"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["rows_ingested"] > 0


@pytest.mark.asyncio
async def test_ingest_news_date_range(client):
    """POST /ingest/news with specific date range."""
    r = await client.post("/api/v1/ingest/news", json={
        "source": "local",
        "date_from": "2026-04-01",
        "date_to": "2026-04-05",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["rows_ingested"] > 0


# ── Manifest listing ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manifests_list(client):
    """GET /ingest/manifests returns all manifests."""
    r = await client.get("/api/v1/ingest/manifests")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1
    for item in data["items"]:
        assert "source" in item
        assert "kind" in item
        assert "status" in item


@pytest.mark.asyncio
async def test_manifests_filter_by_source(client):
    """GET /ingest/manifests?source=test filters by source."""
    r = await client.get("/api/v1/ingest/manifests?source=test")
    assert r.status_code == 200
    data = r.json()["data"]
    for item in data["items"]:
        assert item["source"] == "test"


# ── Status after ingestion ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_status_after_bar_ingestion(client):
    """After POST /ingest/bars, GET /ingest/status reflects the new data."""
    # Trigger ingestion with unique date range
    await client.post("/api/v1/ingest/bars", json={
        "source": "status-test",
        "tickers": ["MSFT"],
        "date_from": "2025-06-02",
        "date_to": "2025-06-13",
    })

    # Check status
    r = await client.get("/api/v1/ingest/status")
    data = r.json()["data"]
    sources = {(s["source"], s["kind"]): s for s in data["sources"]}
    assert ("status-test", "bars") in sources
    assert sources[("status-test", "bars")]["row_count"] > 0


# ── Idempotency / safe re-ingestion ──────────────────────────────────

@pytest.mark.asyncio
async def test_repeated_bar_ingestion_creates_new_manifest(client):
    """Two ingestion runs each create their own manifest."""
    r1 = await client.post("/api/v1/ingest/bars", json={
        "source": "idempotency-test",
        "tickers": ["MSFT"],
        "date_from": "2026-03-01",
        "date_to": "2026-03-05",
    })
    r2 = await client.post("/api/v1/ingest/bars", json={
        "source": "idempotency-test",
        "tickers": ["MSFT"],
        "date_from": "2026-03-01",
        "date_to": "2026-03-05",
    })
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Each creates its own manifest
    assert r1.json()["data"]["manifest_id"] != r2.json()["data"]["manifest_id"]


# ��─ Phase 4A.1 hardening tests ───────────────────────────────────────

def test_stable_seed_deterministic():
    """_stable_seed returns the same value for the same inputs across calls."""
    from app.services.ingest import _stable_seed
    a = _stable_seed("AAPL", "2026-01-01")
    b = _stable_seed("AAPL", "2026-01-01")
    c = _stable_seed("MSFT", "2026-01-01")
    assert a == b, "Same inputs must produce same seed"
    assert a != c, "Different inputs must produce different seeds"
    assert isinstance(a, int)


@pytest.mark.asyncio
async def test_repeated_news_ingestion_is_idempotent(client):
    """Repeated POST /ingest/news over the same source+date does not duplicate events."""
    payload = {
        "source": "news-idem-test",
        "date_from": "2025-11-03",
        "date_to": "2025-11-07",
    }
    r1 = await client.post("/api/v1/ingest/news", json=payload)
    assert r1.status_code == 200
    first_count = r1.json()["data"]["rows_ingested"]
    assert first_count > 0

    r2 = await client.post("/api/v1/ingest/news", json=payload)
    assert r2.status_code == 200
    second_count = r2.json()["data"]["rows_ingested"]
    assert second_count == 0, "Re-ingestion of same news should insert 0 new rows"


@pytest.mark.asyncio
async def test_failed_ingestion_visible_in_status(client):
    """Failed bar ingestion (unknown ticker) appears in /ingest/status as failed."""
    await client.post("/api/v1/ingest/bars", json={
        "source": "fail-vis-test",
        "tickers": ["NONEXISTENT"],
    })

    r = await client.get("/api/v1/ingest/status")
    data = r.json()["data"]
    sources = {(s["source"], s["kind"]): s for s in data["sources"]}
    assert ("fail-vis-test", "bars") in sources
    assert sources[("fail-vis-test", "bars")]["status"] == "failed"
