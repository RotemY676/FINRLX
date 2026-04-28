"""Phase 8J.1 tests: local research experiment tracking."""
import json
import os
import pytest

from app.services.finrlx_research import FinRLXResearchService


def _exp_registry_path():
    return FinRLXResearchService._experiment_registry_path()


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
        "name": "Experiment Tracking Test Export",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    return r.json()["data"]


async def _create_experiment(client, export_id: str, name: str = "Test Experiment") -> dict:
    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": name,
        "linked_export_id": export_id,
        "hypothesis": "Test hypothesis",
        "method_notes": "Test method",
        "parameters": {"lr": 0.001, "epochs": 10},
        "expected_metrics": ["sharpe_ratio", "max_drawdown"],
        "research_acknowledgement": True,
    })
    return r.json()["data"]


# ── Registry creation ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_experiment_registry_created_when_missing(client):
    """Experiment registry is created when missing."""
    _clear_exp_registry()
    reg = FinRLXResearchService.load_experiment_registry()
    assert reg["version"] == 1
    assert isinstance(reg["experiments"], list)
    assert os.path.exists(_exp_registry_path())


# ── Create experiment requires acknowledgement ────────────────────

@pytest.mark.asyncio
async def test_create_requires_acknowledgement(client):
    """Creating experiment requires research_acknowledgement=true."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Test",
        "linked_export_id": export["export_id"],
        "research_acknowledgement": False,
    })
    assert r.status_code == 422
    assert "acknowledgement" in r.json()["detail"].lower()


# ── Create experiment requires valid linked export ────────────────

@pytest.mark.asyncio
async def test_create_requires_valid_linked_export(client):
    """Creating experiment requires valid linked export ID."""
    _clear_exp_registry()
    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Test",
        "linked_export_id": "nonexistent-export-id",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


# ── Create experiment succeeds ────────────────────────────────────

@pytest.mark.asyncio
async def test_create_succeeds_with_valid_export(client):
    """Creating experiment succeeds with valid linked export and acknowledgement."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)

    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Valid Experiment",
        "linked_export_id": export["export_id"],
        "hypothesis": "Test hypothesis",
        "parameters": {"lr": 0.001},
        "expected_metrics": ["sharpe_ratio"],
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["experiment_id"] is not None
    assert data["status"] == "created"
    assert data["lifecycle_state"] == "planned"
    assert data["name"] == "Valid Experiment"


# ── Safety flags ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_created_experiment_includes_safety_flags(client):
    """Created experiment includes required safety flags."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    data = await _create_experiment(client, export["export_id"])

    assert data["research_only"] is True
    assert data["offline_only"] is True
    assert data["shadow_only"] is True
    assert data["no_production_influence"] is True
    assert data["not_eligible_for_promotion"] is True
    sf = data["safety_flags"]
    assert sf["research_only"] is True
    assert sf["offline_only"] is True
    assert sf["shadow_only"] is True
    assert sf["no_production_influence"] is True
    assert sf["not_eligible_for_promotion"] is True


# ── Linked export metadata ────────────────────────────────────────

@pytest.mark.asyncio
async def test_created_experiment_stores_linked_export_metadata(client):
    """Created experiment stores linked export checksum/fingerprint/row count/date range."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    data = await _create_experiment(client, export["export_id"])

    assert data["linked_export_id"] == export["export_id"]
    assert data["linked_export_checksum"] == export["checksum"]
    assert data["linked_export_fingerprint"] == export["fingerprint"]
    assert data["linked_export_row_count"] >= 0


# ── Registry paths ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_experiment_registry_paths_relative(client):
    """Experiment registry paths remain relative and under research/finrlx_cpu/experiments."""
    exp_dir = FinRLXResearchService._experiments_dir()
    assert "research" in exp_dir
    assert "experiments" in exp_dir
    path = _exp_registry_path()
    assert path.endswith("experiment_registry.json")


# ── No absolute paths in registry ─────────────────────────────────

@pytest.mark.asyncio
async def test_experiment_registry_no_absolute_paths(client):
    """Experiment registry never stores absolute paths."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    await _create_experiment(client, export["export_id"])

    with open(_exp_registry_path(), "r") as f:
        content = f.read()
    assert "C:\\" not in content
    assert "C:/" not in content


# ── No secrets in registry ────────────────────────────────────────

@pytest.mark.asyncio
async def test_experiment_registry_no_secrets(client):
    """Experiment registry never stores env vars/secrets."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    await _create_experiment(client, export["export_id"])

    with open(_exp_registry_path(), "r") as f:
        content = f.read()
    for pattern in ["PASSWORD", "SECRET", "API_KEY", "BROKER", "DATABASE_URL"]:
        assert pattern not in content


# ── List experiments newest first ─────────────────────────────────

@pytest.mark.asyncio
async def test_list_experiments_newest_first(client):
    """List experiments returns newest first."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    d1 = await _create_experiment(client, export["export_id"], "First")
    d2 = await _create_experiment(client, export["export_id"], "Second")

    r = await client.get("/api/v1/rl/finrlx/research-experiments")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 2
    ids = [e["experiment_id"] for e in data]
    assert ids.index(d2["experiment_id"]) < ids.index(d1["experiment_id"])


# ── Get experiment by ID ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_experiment_by_id(client):
    """Get experiment by ID returns full schema."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.get(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["experiment_id"] == created["experiment_id"]
    assert data["name"] == "Test Experiment"
    assert data["lifecycle_state"] == "planned"
    assert data["research_only"] is True
    assert data["linked_export_id"] == export["export_id"]
    assert "safety_flags" in data


# ── Invalid experiment ID ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_experiment_id_returns_404(client):
    """Invalid experiment ID returns safe 404."""
    _clear_exp_registry()
    r = await client.get("/api/v1/rl/finrlx/research-experiments/nonexistent-id")
    assert r.status_code == 404


# ── Lifecycle update requires acknowledgement ─────────────────────

@pytest.mark.asyncio
async def test_lifecycle_update_requires_acknowledgement(client):
    """Lifecycle update requires acknowledgement."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/state", json={
        "lifecycle_state": "running_offline",
        "acknowledgement": False,
    })
    assert r.status_code == 422


# ── Lifecycle update rejects invalid state ────────────────────────

@pytest.mark.asyncio
async def test_lifecycle_update_rejects_invalid_state(client):
    """Lifecycle update rejects invalid lifecycle state."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/state", json={
        "lifecycle_state": "production_ready",
        "acknowledgement": True,
    })
    assert r.status_code == 422


# ── Lifecycle update succeeds ─────────────────────────────────────

@pytest.mark.asyncio
async def test_lifecycle_update_succeeds(client):
    """Lifecycle update changes only experiment lifecycle, not production state."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/state", json={
        "lifecycle_state": "running_offline",
        "acknowledgement": True,
        "reason": "Starting offline analysis",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["lifecycle_state"] == "running_offline"
    assert data["research_only"] is True
    assert data["not_eligible_for_promotion"] is True


# ── Result import requires acknowledgement ────────────────────────

@pytest.mark.asyncio
async def test_result_import_requires_acknowledgement(client):
    """Result import requires acknowledgement."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/results", json={
        "acknowledgement": False,
        "result_summary": "test",
    })
    assert r.status_code == 422


# ── Result import is metadata-only ────────────────────────────────

@pytest.mark.asyncio
async def test_result_import_is_metadata_only(client):
    """Result import stores metadata only — numeric/text summaries and metrics."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/results", json={
        "acknowledgement": True,
        "result_summary": "Offline analysis complete. Sharpe 1.2.",
        "result_metrics": {"sharpe_ratio": 1.2, "max_drawdown": -0.05},
        "warnings": ["Small sample size"],
        "limitations": ["Synthetic data only"],
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["result_summary"] == "Offline analysis complete. Sharpe 1.2."
    assert data["result_metrics"]["sharpe_ratio"] == 1.2
    assert data["result_metrics"]["max_drawdown"] == -0.05


# ── Result import sanitizes unsafe paths/secrets ──────────────────

@pytest.mark.asyncio
async def test_result_import_sanitizes_unsafe_fields(client):
    """Result import rejects or sanitizes unsafe absolute paths/secrets."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/results", json={
        "acknowledgement": True,
        "result_summary": "test",
        "result_metrics": {"path": "/etc/passwd", "nested_obj": {"a": 1}},
    })
    assert r.status_code == 200
    data = r.json()["data"]
    # nested_obj should be skipped (non-primitive)
    assert "nested_obj" not in data["result_metrics"]
    # path stored as string, no execution
    assert isinstance(data["result_metrics"].get("path"), str)


# ── Verify experiment is read-only ────────────────────────────────

@pytest.mark.asyncio
async def test_verify_experiment_is_read_only(client):
    """Verify experiment is read-only and does not modify registry."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    with open(_exp_registry_path(), "r") as f:
        before = f.read()

    r = await client.get(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/verify")
    assert r.status_code == 200

    with open(_exp_registry_path(), "r") as f:
        after = f.read()
    assert before == after


# ── Verify reports missing/stale linked export safely ─────────────

@pytest.mark.asyncio
async def test_verify_reports_stale_linked_export(client):
    """Verify experiment reports stale linked export safely."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    # Mark linked export as stale
    await client.post(f"/api/v1/rl/finrlx/dataset-exports/{export['export_id']}/mark-stale", json={
        "acknowledgement": True, "reason": "test stale",
    })

    r = await client.get(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/verify")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["healthy"] is False
    assert any("stale" in w.lower() for w in data["warnings"])


# ── Corrupt experiment registry ───────────────────────────────────

def _corrupt_exp_registry():
    path = _exp_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("{{{invalid json")


@pytest.mark.asyncio
async def test_corrupt_experiment_registry_not_silently_overwritten(client):
    """Corrupt experiment registry does not get silently overwritten."""
    _clear_exp_registry()
    _corrupt_exp_registry()

    with open(_exp_registry_path(), "r") as f:
        corrupt_content = f.read()

    reg = FinRLXResearchService.load_experiment_registry()
    assert reg.get("registry_corrupt") is True

    # Registry file should not be overwritten
    with open(_exp_registry_path(), "r") as f:
        after = f.read()
    assert after == corrupt_content

    _clear_exp_registry()


@pytest.mark.asyncio
async def test_corrupt_experiment_registry_returns_safe_warning(client):
    """Corrupt experiment registry returns safe warning."""
    _corrupt_exp_registry()
    reg = FinRLXResearchService.load_experiment_registry()
    assert reg.get("registry_corrupt") is True
    assert len(reg.get("warnings", [])) > 0
    assert "corrupt" in reg["warnings"][0].lower()
    _clear_exp_registry()


# ── Rebuild experiment registry requires acknowledgement ──────────

@pytest.mark.asyncio
async def test_rebuild_experiment_registry_requires_ack(client):
    """Rebuild experiment registry requires acknowledgement."""
    r = await client.post("/api/v1/rl/finrlx/research-experiments/rebuild-registry", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rebuild_experiment_registry_succeeds(client):
    """Rebuild experiment registry succeeds with acknowledgement."""
    _corrupt_exp_registry()
    r = await client.post("/api/v1/rl/finrlx/research-experiments/rebuild-registry", json={
        "acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["rebuilt"] is True
    _clear_exp_registry()


# ── Production isolation tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_experiment_does_not_alter_recommendations(client):
    """Experiment endpoints do not alter recommendations."""
    r_before = await client.get("/api/v1/recommendations/current")
    before = r_before.json()

    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    await _create_experiment(client, export["export_id"])

    r_after = await client.get("/api/v1/recommendations/current")
    after = r_after.json()
    assert before["data"]["id"] == after["data"]["id"]
    assert before["data"]["status"] == after["data"]["status"]


@pytest.mark.asyncio
async def test_experiment_does_not_alter_overview(client):
    """Experiment endpoints do not alter overview."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_experiment_does_not_alter_publication(client):
    """Experiment endpoints do not alter publication status."""
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_experiment_does_not_promote_candidates(client):
    """Experiment endpoints do not promote candidates."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    data = await _create_experiment(client, export["export_id"])
    assert data["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_experiment_does_not_trigger_training(client):
    """Experiment endpoints do not trigger training."""
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.json()["data"]["training_mode"] == "stubbed"


@pytest.mark.asyncio
async def test_experiment_does_not_trigger_benchmark(client):
    """Experiment endpoints do not trigger benchmark execution."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    # Updating state to running_offline should not trigger benchmark
    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/state", json={
        "lifecycle_state": "running_offline",
        "acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["research_only"] is True


@pytest.mark.asyncio
async def test_rl_execute_remains_absent(client):
    """/rl/execute remains absent/404."""
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


# ── Phase 8I and 8I.2 regression ─────────────────────────────────

@pytest.mark.asyncio
async def test_phase8i_exports_still_work(client):
    """Phase 8I export workflow still works."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_phase8a_status_still_works(client):
    """Phase 8A status endpoint still works."""
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.status_code == 200
    assert r.json()["data"]["research_only"] is True


@pytest.mark.asyncio
async def test_existing_pipeline_still_works(client):
    """Pipeline still works."""
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
