"""Phase 8I.2 tests: dataset export governance, persistence & operator controls."""
import json
import os
import pytest

from app.services.finrlx_research import FinRLXResearchService


def _registry_path():
    return FinRLXResearchService._registry_path()


def _clear_registry():
    path = _registry_path()
    if os.path.exists(path):
        os.remove(path)


async def _create_export(client) -> dict:
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "name": "Governance Test Export",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    return r.json()["data"]


# ── Registry creation ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_registry_created_when_missing(client):
    """Registry file is created when it doesn't exist."""
    _clear_registry()
    reg = FinRLXResearchService.load_dataset_export_registry()
    assert reg["version"] == 1
    assert isinstance(reg["exports"], list)
    assert os.path.exists(_registry_path())


@pytest.mark.asyncio
async def test_export_registers_in_registry(client):
    """Creating an export registers it in export_registry.json."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    reg = FinRLXResearchService.load_dataset_export_registry()
    ids = [e["export_id"] for e in reg["exports"]]
    assert export_id in ids


# ── List exports ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_uses_registry_newest_first(client):
    """GET /dataset-exports uses registry and returns newest first."""
    _clear_registry()
    d1 = await _create_export(client)
    d2 = await _create_export(client)

    r = await client.get("/api/v1/rl/finrlx/dataset-exports")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 2
    # d2 was created after d1 so should be first
    ids = [e["export_id"] for e in data]
    assert ids.index(d2["export_id"]) < ids.index(d1["export_id"])


# ── Get by ID — full schema ────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_export_returns_full_schema_from_registry(client):
    """GET /dataset-exports/{id} returns full Phase 8I.1 schema from registry."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    r = await client.get(f"/api/v1/rl/finrlx/dataset-exports/{export_id}")
    assert r.status_code == 200
    d = r.json()["data"]

    assert d["export_id"] == export_id
    assert d["status"] == "completed"
    assert d["lifecycle_state"] == "active"
    assert d["research_only"] is True
    assert d["offline_only"] is True
    assert d["shadow_only"] is True
    assert d["no_production_influence"] is True
    assert d["not_eligible_for_promotion"] is True
    assert isinstance(d["assets"], list)
    assert isinstance(d["feature_schema"], list)
    assert isinstance(d["target_schema"], list)
    assert isinstance(d["warning_schema"], list)
    assert isinstance(d["limitations"], list)
    assert isinstance(d["warnings"], list)
    assert d["export_path"].startswith("research/finrlx_cpu/exports/")
    assert d["checksum"] is not None
    assert d["fingerprint"] is not None
    assert "artifact_exists" in d
    assert "metadata_exists" in d
    assert "data_exists" in d


# ── Path safety ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_registry_paths_are_relative(client):
    """Registry paths are relative and stay under research/finrlx_cpu/exports."""
    _clear_registry()
    await _create_export(client)

    reg = FinRLXResearchService.load_dataset_export_registry()
    for entry in reg["exports"]:
        assert not entry.get("export_path", "").startswith("/")
        assert not entry.get("export_path", "").startswith("C:")
        assert entry["export_path"].startswith("research/finrlx_cpu/exports/")
        assert not entry.get("metadata_path", "").startswith("/")
        assert not entry.get("data_path", "").startswith("/")


@pytest.mark.asyncio
async def test_registry_never_stores_absolute_paths(client):
    """Registry JSON does not contain absolute paths."""
    _clear_registry()
    await _create_export(client)

    with open(_registry_path(), "r") as f:
        content = f.read()
    assert "C:\\" not in content
    assert "C:/" not in content


@pytest.mark.asyncio
async def test_registry_never_stores_secrets(client):
    """Registry JSON does not contain env vars or secrets."""
    _clear_registry()
    await _create_export(client)

    with open(_registry_path(), "r") as f:
        content = f.read()
    for pattern in ["PASSWORD", "SECRET", "API_KEY", "BROKER", "DATABASE_URL"]:
        assert pattern not in content


# ── Mark stale ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mark_stale_requires_acknowledgement(client):
    """Mark stale requires acknowledgement=true."""
    data = await _create_export(client)
    r = await client.post(f"/api/v1/rl/finrlx/dataset-exports/{data['export_id']}/mark-stale", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_mark_stale_changes_lifecycle(client):
    """Mark stale changes lifecycle_state to stale and preserves files."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    r = await client.post(f"/api/v1/rl/finrlx/dataset-exports/{export_id}/mark-stale", json={
        "acknowledgement": True, "reason": "Test stale marking",
    })
    assert r.status_code == 200
    result = r.json()["data"]
    assert result["lifecycle_state"] == "stale"

    # Verify in registry
    reg = FinRLXResearchService.load_dataset_export_registry()
    entry = next(e for e in reg["exports"] if e["export_id"] == export_id)
    assert entry["lifecycle_state"] == "stale"


@pytest.mark.asyncio
async def test_mark_stale_invalid_id_returns_404(client):
    r = await client.post("/api/v1/rl/finrlx/dataset-exports/nonexistent/mark-stale", json={
        "acknowledgement": True,
    })
    assert r.status_code == 404


# ── Verify artifact ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_reports_existing_files(client):
    """Verify reports existing metadata/data files."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    r = await client.get(f"/api/v1/rl/finrlx/dataset-exports/{export_id}/verify")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["artifact_exists"] is True
    assert d["metadata_exists"] is True
    assert d["data_exists"] is True
    assert d["export_id"] == export_id


@pytest.mark.asyncio
async def test_verify_reports_missing_files_safely(client):
    """Verify reports missing files without crash."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    # Delete the data files
    export_dir = FinRLXResearchService._exports_dir()
    for ext in [".jsonl", ".meta.json", ".json"]:
        p = os.path.join(export_dir, f"{export_id}{ext}")
        if os.path.exists(p):
            os.remove(p)

    r = await client.get(f"/api/v1/rl/finrlx/dataset-exports/{export_id}/verify")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["artifact_exists"] is False
    assert len(d["warnings"]) > 0


@pytest.mark.asyncio
async def test_verify_invalid_id_returns_404(client):
    r = await client.get("/api/v1/rl/finrlx/dataset-exports/nonexistent/verify")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_verify_does_not_modify_registry_for_existing_files(client):
    """Verify is read-only: registry file unchanged when artifacts exist."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    with open(_registry_path(), "r") as f:
        before = f.read()

    r = await client.get(f"/api/v1/rl/finrlx/dataset-exports/{export_id}/verify")
    assert r.status_code == 200
    assert r.json()["data"]["artifact_exists"] is True

    with open(_registry_path(), "r") as f:
        after = f.read()

    assert before == after


@pytest.mark.asyncio
async def test_verify_does_not_modify_registry_for_missing_files(client):
    """Verify is read-only: registry file unchanged even when artifacts are missing."""
    _clear_registry()
    data = await _create_export(client)
    export_id = data["export_id"]

    # Delete artifact files
    export_dir = FinRLXResearchService._exports_dir()
    for ext in [".jsonl", ".meta.json", ".json"]:
        p = os.path.join(export_dir, f"{export_id}{ext}")
        if os.path.exists(p):
            os.remove(p)

    with open(_registry_path(), "r") as f:
        before = f.read()

    r = await client.get(f"/api/v1/rl/finrlx/dataset-exports/{export_id}/verify")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["artifact_exists"] is False
    assert len(d["warnings"]) > 0

    with open(_registry_path(), "r") as f:
        after = f.read()

    assert before == after


# ── Rebuild registry ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rebuild_requires_acknowledgement(client):
    r = await client.post("/api/v1/rl/finrlx/dataset-exports/rebuild-registry", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rebuild_scans_exports_directory(client):
    """Rebuild scans only exports directory."""
    # Create an export to have files on disk
    _clear_registry()
    await _create_export(client)

    # Clear registry and rebuild
    _clear_registry()

    r = await client.post("/api/v1/rl/finrlx/dataset-exports/rebuild-registry", json={
        "acknowledgement": True,
    })
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["rebuilt"] is True
    assert d["export_count"] >= 1


# ── Corrupt registry ───────────────────────────────────────────────

def _corrupt_registry():
    path = _registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("{{{invalid json")


@pytest.mark.asyncio
async def test_corrupt_registry_returns_safe_warning(client):
    """Corrupt registry load returns safe warning with corrupt marker."""
    _corrupt_registry()
    reg = FinRLXResearchService.load_dataset_export_registry()
    assert isinstance(reg["exports"], list)
    assert reg.get("registry_corrupt") is True
    assert len(reg.get("warnings", [])) > 0
    assert "corrupt" in reg["warnings"][0].lower()
    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_registry_not_overwritten_by_export(client):
    """Creating an export does not overwrite a corrupt registry."""
    _clear_registry()
    _corrupt_registry()

    # Read the corrupt content
    with open(_registry_path(), "r") as f:
        corrupt_content = f.read()

    # Create export — should succeed but skip registry
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    # Export response should include a warning about skipped registry
    assert any("registry" in w.lower() and "corrupt" in w.lower() for w in data.get("warnings", []))

    # Registry file should NOT have been overwritten
    with open(_registry_path(), "r") as f:
        after_content = f.read()
    assert after_content == corrupt_content

    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_registry_requires_rebuild(client):
    """Corrupt registry requires explicit rebuild before registry writes resume."""
    _clear_registry()
    _corrupt_registry()

    # Rebuild with acknowledgement
    r = await client.post("/api/v1/rl/finrlx/dataset-exports/rebuild-registry", json={
        "acknowledgement": True,
    })
    assert r.status_code == 200

    # Now creating an export should register normally
    r2 = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    assert r2.status_code == 200
    export_id = r2.json()["data"]["export_id"]

    reg = FinRLXResearchService.load_dataset_export_registry()
    assert reg.get("registry_corrupt") is not True
    ids = [e["export_id"] for e in reg["exports"]]
    assert export_id in ids

    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_list_returns_409(client):
    """List endpoint returns 409 when registry is corrupt."""
    _corrupt_registry()
    r = await client.get("/api/v1/rl/finrlx/dataset-exports")
    assert r.status_code == 409
    assert "corrupt" in r.json()["detail"].lower()
    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_get_returns_409(client):
    """Get endpoint returns 409 when registry is corrupt."""
    _corrupt_registry()
    r = await client.get("/api/v1/rl/finrlx/dataset-exports/any-id")
    assert r.status_code == 409
    assert "corrupt" in r.json()["detail"].lower()
    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_verify_returns_409(client):
    """Verify endpoint returns 409 when registry is corrupt."""
    _corrupt_registry()
    r = await client.get("/api/v1/rl/finrlx/dataset-exports/any-id/verify")
    assert r.status_code == 409
    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_mark_stale_returns_409(client):
    """Mark-stale endpoint returns 409 when registry is corrupt."""
    _corrupt_registry()
    r = await client.post("/api/v1/rl/finrlx/dataset-exports/any-id/mark-stale", json={
        "acknowledgement": True,
    })
    assert r.status_code == 409
    _clear_registry()


@pytest.mark.asyncio
async def test_corrupt_errors_contain_no_secrets(client):
    """Corrupt registry errors do not leak secrets or absolute paths."""
    _corrupt_registry()
    r = await client.get("/api/v1/rl/finrlx/dataset-exports")
    body = r.text
    assert "C:\\" not in body
    assert "C:/" not in body
    for pattern in ["PASSWORD", "SECRET", "API_KEY", "BROKER", "DATABASE_URL"]:
        assert pattern not in body
    _clear_registry()


# ── Safety regressions ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_governance_does_not_alter_recommendations(client):
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_governance_does_not_alter_overview(client):
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_governance_does_not_alter_publication(client):
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_governance_does_not_promote_candidate(client):
    _clear_registry()
    data = await _create_export(client)
    assert data["not_eligible_for_promotion"] is True

    reg = FinRLXResearchService.load_dataset_export_registry()
    for entry in reg["exports"]:
        assert entry["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_governance_does_not_trigger_training(client):
    """Governance endpoints do not trigger training."""
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.json()["data"]["training_mode"] == "stubbed"


@pytest.mark.asyncio
async def test_governance_does_not_trigger_benchmark(client):
    """Existing benchmark still works independently."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    assert r.json()["data"]["status"] in ("completed", "partial")


@pytest.mark.asyncio
async def test_rl_execute_remains_absent(client):
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


@pytest.mark.asyncio
async def test_phase8i1_exports_still_work(client):
    """Phase 8I.1 export workflow still works."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "completed"
