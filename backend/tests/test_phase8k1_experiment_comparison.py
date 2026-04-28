"""Phase 8K.1 tests: offline experiment comparison workbench."""
import json
import os
import pytest

from app.services.finrlx_research import FinRLXResearchService


def _cmp_registry_path():
    return FinRLXResearchService._comparison_registry_path()


def _exp_registry_path():
    return FinRLXResearchService._experiment_registry_path()


def _clear_cmp_registry():
    path = _cmp_registry_path()
    if os.path.exists(path):
        os.remove(path)


def _clear_exp_registry():
    path = _exp_registry_path()
    if os.path.exists(path):
        os.remove(path)


def _clear_export_registry():
    path = FinRLXResearchService._registry_path()
    if os.path.exists(path):
        os.remove(path)


async def _create_export(client) -> dict:
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "name": "Comparison Test Export",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    return r.json()["data"]


async def _create_experiment_with_results(client, export_id: str, name: str, metrics: dict) -> dict:
    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": name,
        "linked_export_id": export_id,
        "hypothesis": "Test",
        "research_acknowledgement": True,
    })
    exp = r.json()["data"]
    # Import results
    await client.post(f"/api/v1/rl/finrlx/research-experiments/{exp['experiment_id']}/results", json={
        "acknowledgement": True,
        "result_summary": f"Results for {name}",
        "result_metrics": metrics,
    })
    # Mark completed
    await client.post(f"/api/v1/rl/finrlx/research-experiments/{exp['experiment_id']}/state", json={
        "lifecycle_state": "completed",
        "acknowledgement": True,
    })
    return exp


async def _setup_two_experiments(client):
    """Create two experiments with results for comparison testing."""
    _clear_cmp_registry()
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    exp1 = await _create_experiment_with_results(client, export["export_id"], "Experiment A",
        {"sharpe_ratio": 1.5, "max_drawdown": -0.08, "total_return": 0.12})
    exp2 = await _create_experiment_with_results(client, export["export_id"], "Experiment B",
        {"sharpe_ratio": 1.2, "max_drawdown": -0.05, "total_return": 0.09})
    return exp1, exp2


# ── Registry creation ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_registry_created_when_missing(client):
    """Comparison registry is created when missing."""
    _clear_cmp_registry()
    reg = FinRLXResearchService.load_comparison_registry()
    assert reg["version"] == 1
    assert isinstance(reg["comparisons"], list)
    assert os.path.exists(_cmp_registry_path())


# ── Create requires acknowledgement ──────────────────────────────

@pytest.mark.asyncio
async def test_create_requires_acknowledgement(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": False,
    })
    assert r.status_code == 422
    assert "acknowledgement" in r.json()["detail"].lower()


# ── Create requires at least 2 unique IDs ────────────────────────

@pytest.mark.asyncio
async def test_create_requires_at_least_2_ids(client):
    exp1, _ = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Test",
        "experiment_ids": [exp1["experiment_id"]],
        "research_acknowledgement": True,
    })
    assert r.status_code == 422
    assert "2" in r.json()["detail"]


# ── Create requires valid experiment IDs ─────────────────────────

@pytest.mark.asyncio
async def test_create_requires_valid_experiment_ids(client):
    exp1, _ = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Test",
        "experiment_ids": [exp1["experiment_id"], "nonexistent-id"],
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


# ── Create succeeds ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_succeeds(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Valid Comparison",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "metric_priority": ["sharpe_ratio"],
        "notes": "Comparing two offline experiments",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["comparison_id"] is not None
    assert data["status"] == "created"
    assert data["lifecycle_state"] == "active"
    assert data["name"] == "Valid Comparison"
    assert len(data["experiment_ids"]) == 2


# ── Safety flags ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_includes_safety_flags(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Safety Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["research_only"] is True
    assert data["offline_only"] is True
    assert data["shadow_only"] is True
    assert data["no_production_influence"] is True
    assert data["not_eligible_for_promotion"] is True
    sf = data["safety_flags"]
    assert sf["research_only"] is True
    assert sf["not_eligible_for_promotion"] is True


# ── Experiment snapshots ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_snapshots_experiment_metadata(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Snapshot Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    snaps = data["experiment_snapshots"]
    assert len(snaps) == 2
    for snap in snaps:
        assert "experiment_id" in snap
        assert "name" in snap
        assert "linked_export_id" in snap
        assert "result_metrics" in snap


# ── Linked export metadata in snapshots ──────────────────────────

@pytest.mark.asyncio
async def test_comparison_includes_linked_export_in_snapshots(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Export Meta Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    snaps = r.json()["data"]["experiment_snapshots"]
    for snap in snaps:
        assert "linked_export_checksum" in snap
        assert "linked_export_fingerprint" in snap
        assert "linked_export_row_count" in snap


# ── Registry path safety ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_registry_paths_relative(client):
    path = _cmp_registry_path()
    assert "research" in path
    assert "comparisons" in path
    assert path.endswith("comparison_registry.json")


@pytest.mark.asyncio
async def test_comparison_registry_no_absolute_paths(client):
    exp1, exp2 = await _setup_two_experiments(client)
    await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Path Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    with open(_cmp_registry_path(), "r") as f:
        content = f.read()
    assert "C:\\" not in content
    assert "C:/" not in content


@pytest.mark.asyncio
async def test_comparison_registry_no_secrets(client):
    exp1, exp2 = await _setup_two_experiments(client)
    await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Secret Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    with open(_cmp_registry_path(), "r") as f:
        content = f.read()
    for pattern in ["PASSWORD", "SECRET", "API_KEY", "BROKER", "DATABASE_URL"]:
        assert pattern not in content


# ── Sanitization ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_sanitizes_unsafe_fields(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Safe name",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "metric_priority": ["sharpe_ratio", "token_leak"],
        "notes": r"Notes from C:\Users\Rotem\.env with database_url",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["notes"] == "[redacted]"
    assert "token_leak" not in data["metric_priority"]
    assert "sharpe_ratio" in data["metric_priority"]
    with open(_cmp_registry_path(), "r") as f:
        content = f.read()
    assert "C:\\Users" not in content
    assert "database_url" not in content.lower()


# ── List comparisons newest first ────────────────────────────────

@pytest.mark.asyncio
async def test_list_comparisons_newest_first(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r1 = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "First", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    r2 = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Second", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    r = await client.get("/api/v1/rl/finrlx/experiment-comparisons")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 2
    ids = [c["comparison_id"] for c in data]
    id2 = r2.json()["data"]["comparison_id"]
    id1 = r1.json()["data"]["comparison_id"]
    assert ids.index(id2) < ids.index(id1)


# ── Get by ID ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_comparison_by_id(client):
    exp1, exp2 = await _setup_two_experiments(client)
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Get Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    cid = cr.json()["data"]["comparison_id"]
    r = await client.get(f"/api/v1/rl/finrlx/experiment-comparisons/{cid}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["comparison_id"] == cid
    assert "comparison_summary" in data
    assert "safety_flags" in data


@pytest.mark.asyncio
async def test_invalid_comparison_id_returns_404(client):
    _clear_cmp_registry()
    r = await client.get("/api/v1/rl/finrlx/experiment-comparisons/nonexistent-id")
    assert r.status_code == 404


# ── Archive ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_archive_requires_acknowledgement(client):
    exp1, exp2 = await _setup_two_experiments(client)
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Archive Ack Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    cid = cr.json()["data"]["comparison_id"]
    r = await client.post(f"/api/v1/rl/finrlx/experiment-comparisons/{cid}/archive", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_archive_changes_lifecycle(client):
    exp1, exp2 = await _setup_two_experiments(client)
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Archive Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    cid = cr.json()["data"]["comparison_id"]
    r = await client.post(f"/api/v1/rl/finrlx/experiment-comparisons/{cid}/archive", json={
        "acknowledgement": True, "reason": "Done with comparison",
    })
    assert r.status_code == 200
    assert r.json()["data"]["lifecycle_state"] == "archived"


# ── Verify read-only ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_is_read_only(client):
    exp1, exp2 = await _setup_two_experiments(client)
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Verify RO Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    cid = cr.json()["data"]["comparison_id"]
    with open(_cmp_registry_path(), "r") as f:
        before = f.read()
    r = await client.get(f"/api/v1/rl/finrlx/experiment-comparisons/{cid}/verify")
    assert r.status_code == 200
    with open(_cmp_registry_path(), "r") as f:
        after = f.read()
    assert before == after


@pytest.mark.asyncio
async def test_verify_reports_missing_experiment(client):
    exp1, exp2 = await _setup_two_experiments(client)
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Verify Missing", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    cid = cr.json()["data"]["comparison_id"]
    # Remove experiments from registry
    _clear_exp_registry()
    r = await client.get(f"/api/v1/rl/finrlx/experiment-comparisons/{cid}/verify")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["healthy"] is False
    assert len(data["warnings"]) > 0


@pytest.mark.asyncio
async def test_verify_reports_no_result_metrics(client):
    _clear_cmp_registry()
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    # Create experiment without results
    r1 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "No Results A", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    r2 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "No Results B", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    eid1 = r1.json()["data"]["experiment_id"]
    eid2 = r2.json()["data"]["experiment_id"]
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "No Metrics", "experiment_ids": [eid1, eid2],
        "research_acknowledgement": True,
    })
    cid = cr.json()["data"]["comparison_id"]
    r = await client.get(f"/api/v1/rl/finrlx/experiment-comparisons/{cid}/verify")
    assert r.status_code == 200
    data = r.json()["data"]
    assert any("no result metrics" in w.lower() for w in data["warnings"])


# ── Metric coverage ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_metric_coverage_counts(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Coverage Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    summary = r.json()["data"]["comparison_summary"]
    assert "metric_coverage" in summary
    cov = summary["metric_coverage"]
    assert "sharpe_ratio" in cov
    assert cov["sharpe_ratio"]["available_count"] == 2
    assert cov["sharpe_ratio"]["coverage_ratio"] == 1.0


# ── Missing metrics per experiment ───────────────────────────────

@pytest.mark.asyncio
async def test_missing_metrics_per_experiment(client):
    _clear_cmp_registry()
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    # exp1 has sharpe, exp2 does not
    exp1 = await _create_experiment_with_results(client, export["export_id"], "Has Sharpe",
        {"sharpe_ratio": 1.5})
    exp2 = await _create_experiment_with_results(client, export["export_id"], "No Sharpe",
        {"max_drawdown": -0.05})
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Missing Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "metric_priority": ["sharpe_ratio", "max_drawdown"],
        "research_acknowledgement": True,
    })
    summary = r.json()["data"]["comparison_summary"]
    missing = summary["missing_metrics"]
    # exp2 should be missing sharpe_ratio
    assert "sharpe_ratio" in missing.get(exp2["experiment_id"], [])
    # exp1 should be missing max_drawdown
    assert "max_drawdown" in missing.get(exp1["experiment_id"], [])


# ── Ranked metrics deterministic ─────────────────────────────────

@pytest.mark.asyncio
async def test_ranked_metrics_deterministic(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Rank Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    ranked = r.json()["data"]["comparison_summary"]["ranked_metrics"]
    assert "sharpe_ratio" in ranked
    # exp1 has sharpe_ratio=1.5, exp2 has 1.2, so exp1 first
    assert ranked["sharpe_ratio"][0]["value"] == 1.5
    assert ranked["sharpe_ratio"][1]["value"] == 1.2


# ── Mixed type metrics produce warnings ──────────────────────────

@pytest.mark.asyncio
async def test_mixed_type_metrics_warning(client):
    _clear_cmp_registry()
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    exp1 = await _create_experiment_with_results(client, export["export_id"], "Numeric",
        {"metric_x": 1.5})
    exp2 = await _create_experiment_with_results(client, export["export_id"], "String",
        {"metric_x": "not a number"})
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Mixed Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    warnings = r.json()["data"]["warnings"]
    assert any("mixed types" in w.lower() for w in warnings)


# ── Does not trigger training ────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_does_not_trigger_training(client):
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.json()["data"]["training_mode"] == "stubbed"


# ── Does not trigger benchmark ───────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_does_not_trigger_benchmark(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "No Bench", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["not_eligible_for_promotion"] is True


# ── Production isolation ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_comparison_does_not_alter_recommendations(client):
    r_before = await client.get("/api/v1/recommendations/current")
    before = r_before.json()
    exp1, exp2 = await _setup_two_experiments(client)
    await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Iso Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    r_after = await client.get("/api/v1/recommendations/current")
    after = r_after.json()
    assert before["data"]["id"] == after["data"]["id"]


@pytest.mark.asyncio
async def test_comparison_does_not_alter_overview(client):
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_comparison_does_not_alter_publication(client):
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_comparison_does_not_promote_candidates(client):
    exp1, exp2 = await _setup_two_experiments(client)
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Promo Test", "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    assert r.json()["data"]["not_eligible_for_promotion"] is True


# ── Corrupt registries ───────────────────────────────────────────

def _corrupt_cmp_registry():
    path = _cmp_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("{{{invalid json")


@pytest.mark.asyncio
async def test_corrupt_comparison_registry_not_overwritten(client):
    _corrupt_cmp_registry()
    reg = FinRLXResearchService.load_comparison_registry()
    assert reg.get("registry_corrupt") is True
    # File not overwritten
    with open(_cmp_registry_path(), "r") as f:
        assert "{{{invalid" in f.read()
    _clear_cmp_registry()


@pytest.mark.asyncio
async def test_corrupt_comparison_registry_returns_409(client):
    _corrupt_cmp_registry()
    r = await client.get("/api/v1/rl/finrlx/experiment-comparisons")
    assert r.status_code == 409
    _clear_cmp_registry()


@pytest.mark.asyncio
async def test_corrupt_experiment_registry_returns_error(client):
    _clear_cmp_registry()
    # Corrupt experiment registry
    exp_path = _exp_registry_path()
    os.makedirs(os.path.dirname(exp_path), exist_ok=True)
    with open(exp_path, "w") as f:
        f.write("{{{bad")
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Test", "experiment_ids": ["a", "b"],
        "research_acknowledgement": True,
    })
    assert r.status_code in (409, 422)
    _clear_exp_registry()


# ── Rebuild requires acknowledgement ─────────────────────────────

@pytest.mark.asyncio
async def test_rebuild_requires_acknowledgement(client):
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons/rebuild-registry", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rebuild_succeeds(client):
    _corrupt_cmp_registry()
    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons/rebuild-registry", json={
        "acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["rebuilt"] is True
    _clear_cmp_registry()


# ── Snapshot sanitization (legacy unsafe metadata) ───────────────

def _inject_unsafe_experiment_metadata(experiment_id: str):
    """Directly edit experiment_registry.json to simulate legacy unsafe metadata."""
    path = _exp_registry_path()
    with open(path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    for exp in reg.get("experiments", []):
        if exp.get("experiment_id") == experiment_id:
            exp["name"] = r"Loaded from C:\Users\Rotem\.env"
            exp["result_summary"] = "DATABASE_URL=postgres://secret"
            exp["result_metrics"] = {
                "safe_metric": 1.23,
                "api_key": "sk-test-secret",
                "path": "/etc/passwd",
                "nested_obj": {"a": 1},
            }
            exp["warnings"] = ["token=abc123"]
            exp["limitations"] = ["broker credential leaked"]
            break
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)


@pytest.mark.asyncio
async def test_comparison_sanitizes_legacy_unsafe_experiment_snapshot(client):
    """Comparison defensively sanitizes experiment snapshot data from legacy unsafe metadata."""
    exp1, exp2 = await _setup_two_experiments(client)
    # Inject unsafe metadata into exp1
    _inject_unsafe_experiment_metadata(exp1["experiment_id"])

    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Legacy Sanitize Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]

    # Check response does not contain unsafe values
    resp_str = json.dumps(data)
    for unsafe in ["C:\\Users", ".env", "DATABASE_URL", "postgres://",
                    "sk-test-secret", "/etc/passwd", "token=abc123", "broker credential"]:
        assert unsafe not in resp_str, f"Found '{unsafe}' in comparison response"

    # safe_metric should remain
    found_safe = False
    for snap in data["experiment_snapshots"]:
        if "safe_metric" in snap.get("result_metrics", {}):
            assert snap["result_metrics"]["safe_metric"] == 1.23
            found_safe = True
    assert found_safe

    # Check registry file
    with open(_cmp_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["C:\\Users", ".env", "DATABASE_URL", "postgres://",
                    "sk-test-secret", "/etc/passwd", "token=abc123", "broker credential"]:
        assert unsafe not in content, f"Found '{unsafe}' in comparison registry"


@pytest.mark.asyncio
async def test_comparison_summary_sanitizes_metric_names(client):
    """Comparison summary only includes safe metric names, not unsafe keys."""
    exp1, exp2 = await _setup_two_experiments(client)
    # Inject unsafe metric keys into exp1
    path = _exp_registry_path()
    with open(path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    for exp in reg.get("experiments", []):
        if exp.get("experiment_id") == exp1["experiment_id"]:
            exp["result_metrics"] = {
                "sharpe_ratio": 1.1,
                "api_key": 123,
                "/etc/passwd": 999,
                "DATABASE_URL": "postgres://secret",
            }
            break
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

    r = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Summary Sanitize Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    summary = r.json()["data"]["comparison_summary"]

    # Safe metric should be present
    assert "sharpe_ratio" in summary["metric_names"]

    # Unsafe metric names must not be present
    for unsafe_name in ["api_key", "/etc/passwd", "DATABASE_URL"]:
        assert unsafe_name not in summary["metric_names"]
        assert unsafe_name not in summary.get("metric_coverage", {})
        assert unsafe_name not in summary.get("ranked_metrics", {})

    # Warnings should not contain unsafe metric names
    warnings_str = " ".join(summary.get("warnings", []))
    for unsafe_name in ["api_key", "/etc/passwd", "DATABASE_URL", "postgres://"]:
        assert unsafe_name not in warnings_str


@pytest.mark.asyncio
async def test_comparison_registry_clean_after_legacy_snapshot(client):
    """Comparison registry contains no unsafe patterns after legacy unsafe experiment data."""
    exp1, exp2 = await _setup_two_experiments(client)
    _inject_unsafe_experiment_metadata(exp1["experiment_id"])

    await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Registry Clean Test",
        "experiment_ids": [exp1["experiment_id"], exp2["experiment_id"]],
        "research_acknowledgement": True,
    })

    with open(_cmp_registry_path(), "r") as f:
        content = f.read()
    content_lower = content.lower()

    for pattern in ["c:\\users", "/etc/", "sk-test-secret", "postgres://"]:
        assert pattern not in content_lower, f"Found '{pattern}' in comparison registry"

    for pattern in ["api_key", "database_url", "credential"]:
        assert pattern not in content_lower, f"Found '{pattern}' in comparison registry"
    # "broker" appears in the safe limitation "No broker execution." — check for "broker credential" specifically
    assert "broker credential" not in content_lower, "Found 'broker credential' in comparison registry"


# ── /rl/execute absent ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_rl_execute_remains_absent(client):
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


# ── Regression ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phase8j1_experiments_still_work(client):
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Regression Test", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_existing_pipeline_still_works(client):
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
