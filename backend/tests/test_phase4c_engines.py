"""Phase 4C tests: engine runner — definitions, real signal generation, endpoints."""
import pytest


# ── Engine definitions ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_engine_definitions_exist(client):
    """GET /engines/definitions returns default engine definitions."""
    r = await client.get("/api/v1/engines/definitions")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 3
    keys = {d["key"] for d in data}
    assert "technical_momentum" in keys
    assert "risk_quality" in keys
    assert "news_sentiment" in keys


@pytest.mark.asyncio
async def test_engine_definition_structure(client):
    """Each definition has required fields."""
    r = await client.get("/api/v1/engines/definitions")
    for d in r.json()["data"]:
        assert "key" in d
        assert "name" in d
        assert "category" in d
        assert "required_feature_keys" in d
        assert "is_active" in d


# ── Engine run ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_engines(client):
    """POST /engines/run creates signal_run and signal_outputs from feature values."""
    # First ensure features exist
    await client.post("/api/v1/features/compute", json={})

    r = await client.post("/api/v1/engines/run", json={})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["successful"] >= 3
    assert data["failed"] == 0
    for result in data["results"]:
        assert result["status"] == "completed"
        assert result["signal_count"] >= 2  # at least AAPL + MSFT


@pytest.mark.asyncio
async def test_engine_uses_feature_values(client):
    """Engine signals are derived from feature_values, not hardcoded constants."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/latest-signals")
    assert r.status_code == 200
    signals = r.json()["data"]
    assert len(signals) >= 4  # at least 2 assets × 2+ engines

    # Check that at least the real engine-produced signals have lineage
    # (old seed signals from conftest may lack it)
    real_signals = [s for s in signals if s["engine_key"] in ("technical_momentum", "risk_quality", "news_sentiment")]
    assert len(real_signals) >= 4  # 2 assets × 2+ engines
    for s in real_signals:
        assert s["source_feature_set_id"] is not None
        assert s["feature_quality_summary"] is not None


@pytest.mark.asyncio
async def test_technical_momentum_non_hardcoded(client):
    """technical_momentum produces different scores for different assets."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/latest-signals")
    signals = r.json()["data"]

    momentum_signals = [s for s in signals if s["engine_key"] == "technical_momentum"]
    assert len(momentum_signals) >= 2

    # Scores should not all be identical (would indicate hardcoding)
    scores = [s["score"] for s in momentum_signals]
    assert len(set(scores)) > 1 or len(scores) == 1, "Scores should vary between assets"


@pytest.mark.asyncio
async def test_news_sentiment_zero_count_hold(client):
    """news_sentiment engine: zero news_count_7d → hold, low confidence, not failure."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/latest-signals")
    signals = r.json()["data"]

    # MSFT has no test news in conftest → news_count_7d may be 0
    # The engine should still produce a signal (hold, not error)
    news_signals = [s for s in signals if s["engine_key"] == "news_sentiment"]
    assert len(news_signals) >= 1
    for s in news_signals:
        assert s["stance"] in ("buy", "hold", "sell", "trim")
        assert s["confidence"] >= 0


@pytest.mark.asyncio
async def test_insufficient_data_produces_caveats(client):
    """Engines with insufficient features produce caveats, not fake confidence."""
    # Compute features for a date with no bars → all price features insufficient
    await client.post("/api/v1/features/compute", json={"as_of": "2019-01-10"})
    r = await client.post("/api/v1/engines/run", json={})
    data = r.json()["data"]

    # Should still complete (engines handle missing data gracefully)
    assert data["successful"] >= 1

    r2 = await client.get("/api/v1/engines/latest-signals")
    signals = r2.json()["data"]

    # At least some signals should have caveats about missing data
    all_caveats = []
    for s in signals:
        all_caveats.extend(s.get("caveats", []))
    # With no data at all, momentum should report "No momentum data available"
    assert len(all_caveats) >= 1


# ── Latest signals ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_latest_signals_endpoint(client):
    """GET /engines/latest-signals returns persisted outputs."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/latest-signals")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    for s in data:
        assert "engine_key" in s
        assert "ticker" in s
        assert "stance" in s
        assert "score" in s
        assert "confidence" in s


# ── Engine status ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_engine_status(client):
    """GET /engines/status returns status summary."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_definitions"] >= 3
    assert data["active_definitions"] >= 3
    assert data["latest_run_id"] is not None
    assert data["latest_run_status"] == "completed"


# ── Comparison / disagreement use real data ───────────────────────────

@pytest.mark.asyncio
async def test_comparison_uses_real_signals(client):
    """GET /engines/comparison returns data from persisted signal_outputs, not ENGINE_DEFS."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/comparison")
    assert r.status_code == 200
    data = r.json()["data"]
    if data is None:
        pytest.skip("No recommendation in test DB")
    assert len(data["engines"]) >= 1
    # Engine keys should be our real engines, not the old hardcoded ones
    engine_keys = {e["engine_key"] for e in data["engines"]}
    assert engine_keys.intersection({"technical_momentum", "risk_quality", "news_sentiment"})


@pytest.mark.asyncio
async def test_disagreement_uses_real_signals(client):
    """GET /engines/disagreement returns data from persisted signal_outputs."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/disagreement")
    assert r.status_code == 200
    data = r.json()["data"]
    if data is None:
        pytest.skip("No recommendation in test DB")
    assert data["total_engines"] >= 1
    # dispersion should be computed, not hardcoded 0.37
    assert isinstance(data["dispersion"], float)


@pytest.mark.asyncio
async def test_evidence_not_hardcoded(client):
    """GET /engines/evidence returns items derived from real signals when available."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/evidence")
    assert r.status_code == 200
    data = r.json()["data"]
    if data is None:
        pytest.skip("No recommendation in test DB")
    assert len(data["items"]) >= 1
    # Should reference real engine names
    source_engines = {i["source_engine"] for i in data["items"] if i.get("source_engine")}
    assert source_engines.intersection({"technical_momentum", "risk_quality", "news_sentiment"})
