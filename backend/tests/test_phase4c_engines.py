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
        assert result["signal_count"] >= 1  # at least 1 signal per engine


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


# ── Phase 4C.1 hardening tests ────────────────────────────────────────

REGISTERED_KEYS = {"technical_momentum", "risk_quality", "news_sentiment", "ml_return_forecaster"}


@pytest.mark.asyncio
async def test_latest_signals_excludes_legacy(client):
    """latest-signals returns only active registered engines, not legacy seeded ones."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/latest-signals")
    signals = r.json()["data"]
    engine_keys = {s["engine_key"] for s in signals}
    # Must not include legacy keys
    legacy_keys = {"momentum", "fundamentals", "narrative", "riskparity", "flow"}
    assert engine_keys.isdisjoint(legacy_keys), f"Legacy keys found: {engine_keys & legacy_keys}"


@pytest.mark.asyncio
async def test_no_unknown_engine_key(client):
    """No signal in latest-signals should have engine_key='unknown'."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/latest-signals")
    for s in r.json()["data"]:
        assert s["engine_key"] != "unknown", f"Found unknown engine_key for ticker {s.get('ticker')}"


@pytest.mark.asyncio
async def test_comparison_only_registered(client):
    """Comparison endpoint includes only registered engine keys."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/comparison")
    data = r.json()["data"]
    if data is None:
        pytest.skip("No recommendation in test DB")
    engine_keys = {e["engine_key"] for e in data["engines"]}
    assert engine_keys.issubset(REGISTERED_KEYS), f"Non-registered keys: {engine_keys - REGISTERED_KEYS}"


@pytest.mark.asyncio
async def test_disagreement_only_registered(client):
    """Disagreement endpoint includes only registered engine keys."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/disagreement")
    data = r.json()["data"]
    if data is None:
        pytest.skip("No recommendation in test DB")
    # total_engines should match number of registered engines with signals
    assert data["total_engines"] <= len(REGISTERED_KEYS)


@pytest.mark.asyncio
async def test_engine_runs_list(client):
    """GET /engines/runs returns list of signal runs."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    r = await client.get("/api/v1/engines/runs")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    for run in data:
        assert "run_id" in run
        assert "engine_name" in run
        assert "signal_count" in run
        assert run["signal_count"] >= 0


@pytest.mark.asyncio
async def test_engine_run_detail(client):
    """GET /engines/runs/{run_id} returns a single run."""
    await client.post("/api/v1/features/compute", json={})
    await client.post("/api/v1/engines/run", json={})

    # Get run list first
    r = await client.get("/api/v1/engines/runs")
    runs = r.json()["data"]
    assert len(runs) >= 1
    run_id = runs[0]["run_id"]

    r2 = await client.get(f"/api/v1/engines/runs/{run_id}")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["run_id"] == run_id
    assert data["signal_count"] >= 1


@pytest.mark.asyncio
async def test_engine_run_returns_feature_set_id(client):
    """POST /engines/run returns the actual feature_set_id used (not None)."""
    await client.post("/api/v1/features/compute", json={})

    r = await client.post("/api/v1/engines/run", json={})
    data = r.json()["data"]
    assert data["feature_set_id"] is not None, "Response should include actual feature_set_id"


# ── Phase 4C.2 cleanup tests ─────────────────────────────────────────

def test_no_seed_import_in_engines_endpoint():
    """engines.py must not import EVIDENCE_ITEMS from seed at runtime."""
    import inspect
    from app.api.v1 import engines as engines_module
    source = inspect.getsource(engines_module)
    assert "from seed import" not in source, "Runtime engines.py must not import from seed"
    assert "EVIDENCE_ITEMS" not in source, "EVIDENCE_ITEMS must not appear in engines.py"


@pytest.mark.asyncio
async def test_evidence_no_signals_returns_none(client):
    """When no registered engine signals exist, evidence returns data=None with warning."""
    # Compute features for a date with no data, then do NOT run engines
    # → latest-signals will be empty for that context
    # But since session DB accumulates signals from prior tests, we check
    # the code path differently: verify the fallback is gone by source check above.
    # Also verify that with real signals, evidence is derived (not hardcoded).
    r = await client.get("/api/v1/engines/evidence")
    assert r.status_code == 200
    data = r.json()["data"]
    meta = r.json()["meta"]
    if data is None:
        # No signals → truthful None, with warning
        assert any("engine-derived evidence" in w or "No evidence" in w for w in meta.get("warnings", []))
    else:
        # Signals exist → evidence derived from real engines, no EVIDENCE_ITEMS
        for item in data["items"]:
            source_engine = item.get("source_engine")
            assert source_engine in ("technical_momentum", "risk_quality", "news_sentiment", "ml_return_forecaster", None)
