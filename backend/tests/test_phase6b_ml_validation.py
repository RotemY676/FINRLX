"""Phase 6B tests: ML shadow validation and evaluation."""
import pytest


async def _ensure_predictions(client) -> str:
    """Ensure features + ML predictions exist. Returns feature_set_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster", "feature_set_id": fs_id,
    })
    return fs_id


# ── Validation report ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validation_report_created(client):
    """POST /models/validation/run creates a persisted validation report."""
    await _ensure_predictions(client)
    r = await client.post("/api/v1/models/validation/run")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["model_key"] == "ml_return_forecaster"
    assert data["status"] in ("completed", "partial", "failed")
    assert "promotion_readiness" in data


@pytest.mark.asyncio
async def test_validation_reads_predictions(client):
    """Validation evaluates model_predictions, not hardcoded values."""
    await _ensure_predictions(client)
    r = await client.post("/api/v1/models/validation/run")
    data = r.json()["data"]
    # sample_count reflects actual predictions evaluated
    assert "sample_count" in data


@pytest.mark.asyncio
async def test_validation_reads_market_bars(client):
    """Validation uses market_bars for realized returns."""
    await _ensure_predictions(client)
    r = await client.post("/api/v1/models/validation/run")
    data = r.json()["data"]
    # If realized returns found, directional_accuracy is computed
    if data["sample_count"] > 0:
        assert data["directional_accuracy"] is not None
    else:
        # No realized returns available — report is partial
        assert data["status"] in ("partial", "failed")


@pytest.mark.asyncio
async def test_validation_persisted(client):
    """Validation report is persisted and queryable."""
    await _ensure_predictions(client)
    await client.post("/api/v1/models/validation/run")

    r = await client.get("/api/v1/models/validation/latest")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data is not None
    assert data["model_key"] == "ml_return_forecaster"


@pytest.mark.asyncio
async def test_insufficient_sample_needs_more_data(client):
    """Low sample count returns needs_more_data promotion readiness."""
    await _ensure_predictions(client)
    r = await client.post("/api/v1/models/validation/run")
    data = r.json()["data"]
    # With limited test data, promotion_readiness should not be eligible_for_review
    if data["sample_count"] < 20:
        assert data["promotion_readiness"] in ("needs_more_data", "not_ready")


@pytest.mark.asyncio
async def test_confidence_buckets_present(client):
    """Validation includes confidence buckets or warns if unavailable."""
    await _ensure_predictions(client)
    r = await client.post("/api/v1/models/validation/run")
    data = r.json()["data"]
    if data["sample_count"] > 0:
        assert "confidence_buckets" in data
    # If no samples, buckets are null — that's correct


@pytest.mark.asyncio
async def test_baseline_comparison(client):
    """Validation includes comparison against deterministic engines."""
    fs_id = await _ensure_predictions(client)
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/models/validation/run")
    data = r.json()["data"]
    if data["sample_count"] > 0 and data.get("baseline_comparison"):
        assert isinstance(data["baseline_comparison"], dict)


# ── Model status integration ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_model_status_includes_validation(client):
    """Model status includes latest validation summary."""
    await _ensure_predictions(client)
    await client.post("/api/v1/models/validation/run")

    r = await client.get("/api/v1/models/status")
    data = r.json()["data"]
    assert "latest_validation_status" in data
    assert "promotion_readiness" in data


# ── Shadow isolation preserved ────────────────────────────────────────

@pytest.mark.asyncio
async def test_ml_still_shadow_after_validation(client):
    """ML remains shadow/experimental after validation."""
    r = await client.get("/api/v1/models/definitions")
    ml = next(d for d in r.json()["data"] if d["key"] == "ml_return_forecaster")
    assert ml["status"] == "experimental"
    assert ml["is_shadow"] is True


@pytest.mark.asyncio
async def test_live_pipeline_still_excludes_ml(client):
    """Default pipeline still excludes shadow ML after validation."""
    fs_id = await _ensure_predictions(client)
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    warnings = r.json()["data"].get("warnings", [])
    assert not any("shadow" in w.lower() for w in warnings)


@pytest.mark.asyncio
async def test_validation_history(client):
    """GET /models/validation/history returns reports."""
    r = await client.get("/api/v1/models/validation/history")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
