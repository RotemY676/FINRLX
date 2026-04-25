"""Phase 6F tests: policy rules, integrations, universe management."""
import pytest


# ── Policy Rules ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_default_policy_rules_exist(client):
    """GET /policies/rules returns default policy rules."""
    r = await client.get("/api/v1/policies/rules")
    assert r.status_code == 200
    rules = r.json()["data"]
    assert len(rules) >= 8
    keys = {rule["key"] for rule in rules}
    assert "position_cap_max" in keys
    assert "cash_floor" in keys
    assert "confidence_model_min" in keys
    assert "ml_shadow_only" in keys


@pytest.mark.asyncio
async def test_policy_rule_detail(client):
    """GET /policies/rules/{key} returns single rule."""
    r = await client.get("/api/v1/policies/rules/position_cap_max")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["key"] == "position_cap_max"
    assert data["threshold_value"] == 0.15
    assert data["category"] == "position_cap"


@pytest.mark.asyncio
async def test_policy_rule_update_records_history(client):
    """PATCH /policies/rules/{key} updates and records history."""
    r = await client.patch("/api/v1/policies/rules/position_cap_max", json={
        "threshold_value": 0.20,
        "actor": "test_operator",
        "reason": "Increased cap for testing",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["threshold_value"] == 0.20
    assert data["version"] >= 2

    # Check history
    r2 = await client.get("/api/v1/policies/rules/position_cap_max/history")
    assert r2.status_code == 200
    history = r2.json()["data"]
    assert len(history) >= 1
    assert history[0]["previous_value"] == 0.15
    assert history[0]["new_value"] == 0.20
    assert history[0]["actor"] == "test_operator"

    # Restore original value
    await client.patch("/api/v1/policies/rules/position_cap_max", json={
        "threshold_value": 0.15,
        "actor": "test_operator",
        "reason": "Restored original value",
    })


@pytest.mark.asyncio
async def test_policy_breaches_endpoint(client):
    """GET /policies/breaches returns active breaches."""
    r = await client.get("/api/v1/policies/breaches")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


@pytest.mark.asyncio
async def test_policy_evaluate_endpoint(client):
    """POST /policies/evaluate returns rule evaluations."""
    r = await client.post("/api/v1/policies/evaluate")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    for item in data:
        assert "key" in item
        assert "is_enforced" in item


# ── Integrations ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_integrations_endpoint(client):
    """GET /integrations returns integration list."""
    r = await client.get("/api/v1/integrations")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    # Should have at least local adapter entries
    for item in data:
        assert "source_key" in item
        assert "is_real_provider" in item
        assert "is_placeholder" in item


@pytest.mark.asyncio
async def test_integrations_labels_placeholder_truthfully(client):
    """Placeholder/demo feeds are not marked as real providers."""
    r = await client.get("/api/v1/integrations")
    data = r.json()["data"]
    for item in data:
        if item.get("is_placeholder"):
            assert item["is_real_provider"] is False
            assert "placeholder" in item.get("status", "") or len(item.get("warnings", [])) > 0


@pytest.mark.asyncio
async def test_integration_health(client):
    """GET /integrations/health returns health summary."""
    r = await client.get("/api/v1/integrations/health")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "total_integrations" in data
    assert "placeholder" in data
    assert "real_providers" in data


@pytest.mark.asyncio
async def test_integration_readiness(client):
    """GET /integrations/readiness returns readiness."""
    r = await client.get("/api/v1/integrations/readiness")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "ready_for_pipeline" in data


# ── Universe ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_universes_returns_default(client):
    """GET /universes returns at least one universe."""
    r = await client.get("/api/v1/universes")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    assert "asset_count" in data[0]


@pytest.mark.asyncio
async def test_default_universe(client):
    """GET /universes/default returns the default universe with assets."""
    r = await client.get("/api/v1/universes/default")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data is not None
    assert data["asset_count"] >= 2
    assert len(data["tickers"]) >= 2


@pytest.mark.asyncio
async def test_universe_coverage(client):
    """GET /universes/{id}/coverage returns coverage by data domain."""
    # First get default universe ID
    r = await client.get("/api/v1/universes/default")
    uid = r.json()["data"]["universe_id"]

    r2 = await client.get(f"/api/v1/universes/{uid}/coverage")
    assert r2.status_code == 200
    cov = r2.json()["data"]["coverage"]
    assert "market_bars" in cov
    assert "features" in cov
    assert "signals" in cov
    assert "model_predictions" in cov
    # Market bars should have coverage from seeded data
    assert cov["market_bars"]["covered"] >= 1


@pytest.mark.asyncio
async def test_universe_readiness(client):
    """GET /universes/{id}/readiness returns readiness status."""
    r = await client.get("/api/v1/universes/default")
    uid = r.json()["data"]["universe_id"]

    r2 = await client.get(f"/api/v1/universes/{uid}/readiness")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert "readiness_status" in data
    assert data["readiness_status"] in ("ready", "incomplete")


# ── Ops integration ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ops_includes_policy_block(client):
    """GET /ops includes policy summary."""
    r = await client.get("/api/v1/ops")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "policy" in data
    pol = data["policy"]
    assert pol["total_rules"] >= 8
    assert pol["active_rules"] >= 1


@pytest.mark.asyncio
async def test_ops_includes_integrations_block(client):
    """GET /ops includes integrations summary."""
    r = await client.get("/api/v1/ops")
    data = r.json()["data"]
    assert "integrations_summary" in data
    integ = data["integrations_summary"]
    assert "total_integrations" in integ
    assert "placeholder" in integ


@pytest.mark.asyncio
async def test_ops_includes_universe_block(client):
    """GET /ops includes universe summary."""
    r = await client.get("/api/v1/ops")
    data = r.json()["data"]
    assert "universe" in data
    uni = data["universe"]
    assert uni["total_assets"] >= 2
    assert uni["total_universes"] >= 1


@pytest.mark.asyncio
async def test_ml_ops_still_shadow(client):
    """ML ops remains shadow-only."""
    r = await client.get("/api/v1/ops")
    data = r.json()["data"]
    assert data["ml_ops"]["ml_is_shadow_only"] is True


@pytest.mark.asyncio
async def test_existing_pipeline_unchanged(client):
    """Pipeline still works after policy/integration/universe additions."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
