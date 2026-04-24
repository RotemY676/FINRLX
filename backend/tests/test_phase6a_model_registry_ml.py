"""Phase 6A tests: ML model registry + baseline model."""
import pytest


async def _ensure_features(client) -> str:
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    return r.json()["data"]["feature_set_id"]


# ── Model definitions ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_model_definitions_exist(client):
    """GET /models/definitions returns ml_return_forecaster."""
    r = await client.get("/api/v1/models/definitions")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    keys = {d["key"] for d in data}
    assert "ml_return_forecaster" in keys
    ml = next(d for d in data if d["key"] == "ml_return_forecaster")
    assert ml["status"] == "experimental"
    assert ml["is_shadow"] is True
    assert ml["model_type"] == "baseline_linear"


# ── Train ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_train_baseline(client):
    """POST /models/train creates a model run."""
    await _ensure_features(client)
    r = await client.post("/api/v1/models/train", json={"model_key": "ml_return_forecaster"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["run_type"] == "train"
    assert data["metrics"] is not None


# ── Predict ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_predict_creates_predictions(client):
    """POST /models/predict creates model predictions from feature_values."""
    fs_id = await _ensure_features(client)
    r = await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster",
        "feature_set_id": fs_id,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["metrics"]["prediction_count"] >= 1


@pytest.mark.asyncio
async def test_predictions_have_lineage(client):
    """Model predictions include feature set lineage."""
    fs_id = await _ensure_features(client)
    await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster",
        "feature_set_id": fs_id,
    })
    r = await client.get("/api/v1/models/predictions")
    assert r.status_code == 200
    preds = r.json()["data"]
    assert len(preds) >= 1
    for p in preds:
        assert "ticker" in p
        assert "prediction_score" in p
        assert "confidence" in p
        assert "quality" in p


@pytest.mark.asyncio
async def test_insufficient_data_partial(client):
    """Prediction with no feature set returns failed."""
    r = await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster",
        "feature_set_id": "nonexistent",
    })
    data = r.json()["data"]
    assert data["status"] == "failed"


# ── ML engine integration ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ml_engine_definition_exists(client):
    """Engine definitions include ml_return_forecaster."""
    r = await client.get("/api/v1/engines/definitions")
    data = r.json()["data"]
    keys = {d["key"] for d in data}
    assert "ml_return_forecaster" in keys
    ml = next(d for d in data if d["key"] == "ml_return_forecaster")
    assert ml["category"] == "ml"


@pytest.mark.asyncio
async def test_ml_engine_runs_with_predictions(client):
    """ML engine generates signal outputs from model_predictions."""
    fs_id = await _ensure_features(client)
    await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster",
        "feature_set_id": fs_id,
    })
    r = await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    data = r.json()["data"]
    # Should include ml_return_forecaster among completed engines
    ml_results = [res for res in data["results"] if res["engine_key"] == "ml_return_forecaster"]
    assert len(ml_results) == 1
    assert ml_results[0]["status"] == "completed"
    assert ml_results[0]["signal_count"] >= 1


# ── Existing engines still work ───────────────────────────────────────

@pytest.mark.asyncio
async def test_deterministic_engines_still_work(client):
    """Technical momentum, risk_quality, news_sentiment still produce signals."""
    fs_id = await _ensure_features(client)
    r = await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    data = r.json()["data"]
    det_engines = {res["engine_key"] for res in data["results"]
                   if res["status"] == "completed" and res["engine_key"] != "ml_return_forecaster"}
    assert "technical_momentum" in det_engines
    assert "risk_quality" in det_engines
    assert "news_sentiment" in det_engines


# ── Pipeline works without ML ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_works(client):
    """Pipeline still creates recommendations."""
    fs_id = await _ensure_features(client)
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    data = r.json()["data"]
    assert data["status"] == "completed"


# ── Status ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_model_status(client):
    """GET /models/status returns counts."""
    r = await client.get("/api/v1/models/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_definitions"] >= 1
    assert data["active_definitions"] >= 1


# ── Phase 6A.1 shadow isolation tests ─────────────────────────────────

@pytest.mark.asyncio
async def test_default_pipeline_excludes_ml(client):
    """Default pipeline run excludes shadow ML signals from scoring."""
    fs_id = await _ensure_features(client)
    await client.post("/api/v1/models/predict", json={"model_key": "ml_return_forecaster", "feature_set_id": fs_id})
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})

    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    data = r.json()["data"]
    assert data["status"] == "completed"
    # Signal run IDs should NOT include ml_return_forecaster runs
    # (we can't easily check engine_name from run_ids, but check warnings)
    warnings = data.get("warnings", [])
    assert not any("shadow" in w.lower() for w in warnings), "Default pipeline should not mention shadow engines"


@pytest.mark.asyncio
async def test_pipeline_with_shadow_includes_ml(client):
    """Pipeline with include_shadow_engines=true includes ML signals and warns."""
    fs_id = await _ensure_features(client)
    await client.post("/api/v1/models/predict", json={"model_key": "ml_return_forecaster", "feature_set_id": fs_id})
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})

    r = await client.post("/api/v1/pipeline/run", json={
        "feature_set_id": fs_id,
        "include_shadow_engines": True,
    })
    data = r.json()["data"]
    assert data["status"] == "completed"
    warnings = data.get("warnings", [])
    assert any("shadow" in w.lower() or "experimental" in w.lower() for w in warnings), \
        "Pipeline with shadow engines should include shadow warning"


@pytest.mark.asyncio
async def test_ml_signals_still_generated(client):
    """ML engine still generates signal_outputs even when excluded from pipeline."""
    fs_id = await _ensure_features(client)
    await client.post("/api/v1/models/predict", json={"model_key": "ml_return_forecaster", "feature_set_id": fs_id})
    r = await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    data = r.json()["data"]
    ml = [res for res in data["results"] if res["engine_key"] == "ml_return_forecaster"]
    assert len(ml) == 1
    assert ml[0]["status"] == "completed"
    assert ml[0]["signal_count"] >= 1
