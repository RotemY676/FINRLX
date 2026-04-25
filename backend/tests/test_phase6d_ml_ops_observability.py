"""Phase 6D tests: ML Ops observability and integration."""
import pytest


async def _ensure_predictions_and_validation(client) -> str:
    """Ensure features + ML predictions + validation exist."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster", "feature_set_id": fs_id,
    })
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    await client.post("/api/v1/models/validation/run")
    return fs_id


# ── ML Ops Summary ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ml_ops_summary_works(client):
    """GET /ml-ops/summary returns a valid response."""
    r = await client.get("/api/v1/ml-ops/summary")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["model_key"] == "ml_return_forecaster"
    assert "still_shadow" in data
    assert "live_pipeline_influence" in data
    assert "warnings" in data
    assert "recommended_operator_action" in data


@pytest.mark.asyncio
async def test_summary_includes_latest_model_run(client):
    """Summary includes latest prediction run after predictions are made."""
    await _ensure_predictions_and_validation(client)
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    assert data["latest_prediction_run_id"] is not None
    assert data["latest_prediction_status"] == "completed"
    assert data["prediction_count"] >= 1


@pytest.mark.asyncio
async def test_summary_includes_latest_validation(client):
    """Summary includes latest validation report."""
    await _ensure_predictions_and_validation(client)
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    assert data["latest_validation_report_id"] is not None
    assert data["validation_status"] is not None


@pytest.mark.asyncio
async def test_summary_includes_latest_promotion_review(client):
    """Summary includes latest promotion review if one exists."""
    await _ensure_predictions_and_validation(client)
    # Run a promotion review first
    await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    assert data["latest_promotion_review_id"] is not None
    assert data["promotion_review_recommendation"] is not None


@pytest.mark.asyncio
async def test_summary_still_shadow_true(client):
    """Summary clearly states still_shadow=true."""
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    assert data["still_shadow"] is True


@pytest.mark.asyncio
async def test_summary_live_pipeline_influence_false(client):
    """Summary clearly states live_pipeline_influence=false."""
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    assert data["live_pipeline_influence"] is False


@pytest.mark.asyncio
async def test_warnings_include_sample_count(client):
    """Warnings include sample_count < 20 when applicable."""
    await _ensure_predictions_and_validation(client)
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    messages = [w["message"] for w in data["warnings"]]
    # In test env, sample_count is typically < 20
    val_r = await client.get("/api/v1/models/validation/latest")
    val_data = val_r.json()["data"]
    if val_data and val_data["sample_count"] < 20:
        assert any("sample_count" in m for m in messages)


@pytest.mark.asyncio
async def test_recommended_action_reasonable(client):
    """Recommended action is one of the expected values."""
    await _ensure_predictions_and_validation(client)
    r = await client.get("/api/v1/ml-ops/summary")
    data = r.json()["data"]
    valid_actions = {
        "run_predictions", "run_validation", "run_promotion_review",
        "keep_shadow", "needs_more_data", "eligible_for_manual_review",
        "investigate_model",
    }
    assert data["recommended_operator_action"] in valid_actions


# ── /ops includes ML block ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ops_includes_ml_block(client):
    """GET /ops includes ml_ops block."""
    r = await client.get("/api/v1/ops")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "ml_ops" in data
    ml = data["ml_ops"]
    assert ml is not None
    assert ml["ml_is_shadow_only"] is True
    assert ml["any_model_influences_live_pipeline"] is False
    assert "total_models" in ml
    assert "shadow_models" in ml


# ── Pipeline unchanged ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_unchanged(client):
    """Deterministic pipeline still works without ML."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    data = r.json()["data"]
    assert data["status"] == "completed"
    warnings = data.get("warnings", [])
    assert not any("shadow" in w.lower() for w in warnings)


@pytest.mark.asyncio
async def test_ml_excluded_from_live_pipeline(client):
    """ML remains excluded from live pipeline by default."""
    r = await client.get("/api/v1/models/definitions")
    ml = next(d for d in r.json()["data"] if d["key"] == "ml_return_forecaster")
    assert ml["is_shadow"] is True
    assert ml["status"] == "experimental"


# ── Sub-endpoints ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_model_detail_endpoint(client):
    """GET /ml-ops/models/{model_key} returns combined health/validation/promotion/shadow."""
    r = await client.get("/api/v1/ml-ops/models/ml_return_forecaster")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "health" in data
    assert "validation" in data
    assert "promotion" in data
    assert "shadow" in data
    assert data["shadow"]["still_shadow"] is True


@pytest.mark.asyncio
async def test_warnings_endpoint(client):
    """GET /ml-ops/models/{model_key}/warnings returns warnings list."""
    r = await client.get("/api/v1/ml-ops/models/ml_return_forecaster/warnings")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    # Should always have the shadow info warning
    messages = [w["message"] for w in data]
    assert any("shadow" in m.lower() for m in messages)
