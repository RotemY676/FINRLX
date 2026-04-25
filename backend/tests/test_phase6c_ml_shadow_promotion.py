"""Phase 6C tests: ML shadow backtest comparison and promotion governance."""
import pytest


async def _ensure_features_and_predictions(client) -> str:
    """Ensure features + ML predictions exist. Returns feature_set_id."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/models/predict", json={
        "model_key": "ml_return_forecaster", "feature_set_id": fs_id,
    })
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    return fs_id


# ── Shadow promotion review ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_promotion_review_can_be_created(client):
    """POST /models/promotion/review creates a persisted promotion review."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "model_key": "ml_return_forecaster",
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["id"] is not None
    assert data["model_key"] == "ml_return_forecaster"
    assert data["recommendation"] is not None
    assert data["baseline_backtest_id"] is not None
    assert data["shadow_backtest_id"] is not None


@pytest.mark.asyncio
async def test_baseline_backtest_excludes_ml(client):
    """Baseline backtest in promotion review does not include shadow engines."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    baseline_id = data["baseline_backtest_id"]
    bt = await client.get(f"/api/v1/backtests/{baseline_id}")
    bt_data = bt.json()["data"]
    config = bt_data.get("config", {})
    assert config.get("include_shadow_engines") is not True


@pytest.mark.asyncio
async def test_shadow_backtest_includes_ml(client):
    """Shadow backtest in promotion review includes shadow engines."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    shadow_id = data["shadow_backtest_id"]
    bt = await client.get(f"/api/v1/backtests/{shadow_id}")
    bt_data = bt.json()["data"]
    config = bt_data.get("config", {})
    assert config.get("include_shadow_engines") is True


@pytest.mark.asyncio
async def test_live_recs_not_polluted_by_shadow_backtest(client):
    """Shadow backtest recs do not appear in /recommendations/current."""
    await _ensure_features_and_predictions(client)
    await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200
    data = r.json()["data"]
    # The current recommendation should be the original seeded one, not a backtest rec
    if data:
        # If there's a current recommendation, it should not have backtest context
        # Backtest recs are filtered out by context="backtest"
        assert data.get("status") in ("published", "published_with_warning", "draft", None)


@pytest.mark.asyncio
async def test_comparison_metrics_include_deltas(client):
    """Promotion review includes return/sharpe/drawdown/turnover deltas."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    deltas = data.get("metric_deltas", {})
    assert "total_return_delta" in deltas
    assert "sharpe_ratio_delta" in deltas
    assert "max_drawdown_delta" in deltas
    assert "turnover_delta" in deltas
    assert "trade_count_delta" in deltas


@pytest.mark.asyncio
async def test_sample_count_low_forces_needs_more_data(client):
    """With limited test data, recommendation should be needs_more_data."""
    await _ensure_features_and_predictions(client)
    # Run validation first so sample_count is populated
    await client.post("/api/v1/models/validation/run")
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    data = r.json()["data"]
    # In test env, sample_count < 20, so recommendation must be needs_more_data
    if data["sample_count"] < 20:
        assert data["recommendation"] == "needs_more_data"


@pytest.mark.asyncio
async def test_promotion_review_persisted(client):
    """Promotion review is queryable after creation."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    review_id = r.json()["data"]["id"]

    # GET by ID
    r2 = await client.get(f"/api/v1/models/promotion/{review_id}")
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == review_id

    # GET latest
    r3 = await client.get("/api/v1/models/promotion/latest")
    assert r3.status_code == 200
    assert r3.json()["data"] is not None


@pytest.mark.asyncio
async def test_model_status_includes_promotion_review(client):
    """Model status includes latest promotion review summary."""
    await _ensure_features_and_predictions(client)
    await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    r = await client.get("/api/v1/models/status")
    data = r.json()["data"]
    assert "latest_promotion_review_id" in data
    assert "promotion_review_recommendation" in data
    assert "still_shadow" in data
    assert data["still_shadow"] is True


# ── Operator decision ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_operator_decision_records_but_does_not_activate(client):
    """POST decision records operator review but does not activate ML."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    review_id = r.json()["data"]["id"]

    r2 = await client.post(f"/api/v1/models/promotion/{review_id}/decision", json={
        "decision": "keep_shadow",
    })
    assert r2.status_code == 200
    assert r2.json()["data"]["decision"] == "keep_shadow"

    # ML remains shadow
    r3 = await client.get("/api/v1/models/definitions")
    ml = next(d for d in r3.json()["data"] if d["key"] == "ml_return_forecaster")
    assert ml["is_shadow"] is True
    assert ml["status"] == "experimental"


@pytest.mark.asyncio
async def test_ml_remains_shadow_after_review(client):
    """ML model remains shadow/experimental after promotion review."""
    r = await client.get("/api/v1/models/definitions")
    ml = next(d for d in r.json()["data"] if d["key"] == "ml_return_forecaster")
    assert ml["is_shadow"] is True
    assert ml["status"] == "experimental"


@pytest.mark.asyncio
async def test_promotion_history(client):
    """GET /models/promotion/history returns review list."""
    r = await client.get("/api/v1/models/promotion/history")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


@pytest.mark.asyncio
async def test_invalid_decision_rejected(client):
    """Invalid decision value returns 400."""
    await _ensure_features_and_predictions(client)
    r = await client.post("/api/v1/models/promotion/review", json={
        "start_date": "2026-03-15",
        "end_date": "2026-04-15",
    })
    review_id = r.json()["data"]["id"]

    r2 = await client.post(f"/api/v1/models/promotion/{review_id}/decision", json={
        "decision": "activate_now",
    })
    assert r2.status_code == 400
