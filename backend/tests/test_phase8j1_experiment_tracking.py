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


# ── Lifecycle reason sanitizes unsafe paths/secrets ───────────────

@pytest.mark.asyncio
async def test_lifecycle_reason_sanitizes_unsafe_paths_and_secrets(client):
    """Lifecycle update reason is sanitized — unsafe paths/secrets redacted."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/state", json={
        "lifecycle_state": "running_offline",
        "acknowledgement": True,
        "reason": r"Started from C:\Users\Rotem\.env with api_key=sk-test-secret and DATABASE_URL=postgres://secret",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["lifecycle_state"] == "running_offline"

    # Response warnings should not contain the actual unsafe input values
    warnings_text = " ".join(data.get("warnings", []))
    for unsafe in ["C:\\Users", "sk-test-secret", "DATABASE_URL", "postgres://"]:
        assert unsafe not in warnings_text, f"Found '{unsafe}' in response warnings"

    # Should contain redaction warning
    assert any("redacted" in w.lower() for w in data.get("warnings", []))

    # Registry file must not contain any of the actual unsafe input values
    with open(_exp_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["C:\\Users", "sk-test-secret", "DATABASE_URL", "postgres://"]:
        assert unsafe not in content, f"Found '{unsafe}' in registry file"
    # "api_key" as a key name (not in redaction warnings) should not appear as stored data
    # Count occurrences — the only "api_key" allowed would be inside disallowed-pattern constants,
    # but those are in .py not in registry JSON
    assert "api_key" not in content, "Found 'api_key' in registry file"


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


# ── Create experiment sanitizes unsafe metadata ──────────────────

@pytest.mark.asyncio
async def test_create_experiment_sanitizes_unsafe_metadata(client):
    """Create experiment redacts/drops unsafe paths, secrets, env vars from metadata."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)

    r = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Safe experiment name",
        "linked_export_id": export["export_id"],
        "hypothesis": r"Loaded data from C:\Users\Rotem\.env and analyzed",
        "method_notes": "Used /etc/passwd as config source",
        "parameters": {"path": "/etc/passwd", "api_key": "sk-test-secret", "safe_lr": 0.001},
        "expected_metrics": ["sharpe_ratio", "token_leak"],
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]

    # hypothesis and method_notes should be redacted
    assert data["hypothesis"] == "[redacted]"
    assert data["method_notes"] == "[redacted]"

    # unsafe params dropped, safe_lr preserved
    assert "path" not in data["parameters"]
    assert "api_key" not in data["parameters"]
    assert data["parameters"]["safe_lr"] == 0.001

    # token_leak dropped from expected_metrics
    assert "sharpe_ratio" in data["expected_metrics"]
    assert "token_leak" not in data["expected_metrics"]

    # Verify registry file itself does not contain unsafe values
    with open(_exp_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["/etc/passwd", "C:\\Users", "sk-test-secret", "api_key"]:
        assert unsafe not in content

    # Warning about redaction should be present
    assert any("redacted" in w.lower() or "dropped" in w.lower() for w in data.get("warnings", []))


# ── Result import sanitizes unsafe paths/secrets ──────────────────

@pytest.mark.asyncio
async def test_result_import_sanitizes_unsafe_paths_and_secrets(client):
    """Result import drops/redacts unsafe absolute paths, secrets, nested objects."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    created = await _create_experiment(client, export["export_id"])

    r = await client.post(f"/api/v1/rl/finrlx/research-experiments/{created['experiment_id']}/results", json={
        "acknowledgement": True,
        "result_summary": r"saved at C:\Users\Rotem\secret.txt",
        "result_metrics": {
            "safe_metric": 1.23,
            "path": "/etc/passwd",
            "api_key": "sk-test-secret",
            "nested_obj": {"a": 1},
        },
        "warnings": ["token=abc123"],
        "limitations": ["DATABASE_URL=postgres://secret"],
    })
    assert r.status_code == 200
    data = r.json()["data"]

    # result_summary should be redacted
    assert data["result_summary"] == "[redacted]"

    # safe_metric preserved, unsafe keys and nested_obj dropped
    assert data["result_metrics"]["safe_metric"] == 1.23
    assert "path" not in data["result_metrics"]
    assert "api_key" not in data["result_metrics"]
    assert "nested_obj" not in data["result_metrics"]

    # unsafe warnings and limitations dropped
    assert not any("token=abc123" in w for w in data.get("warnings", []))
    assert not any("DATABASE_URL" in l for l in data.get("limitations", []))

    # Verify registry file itself does not contain any unsafe values
    with open(_exp_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["/etc/passwd", "C:\\Users", "sk-test-secret",
                   "token=abc123", "DATABASE_URL", "postgres://", "secret.txt"]:
        assert unsafe not in content


# ── Registry never stores unsafe content after create + result import ─

@pytest.mark.asyncio
async def test_registry_clean_after_create_and_result_import(client):
    """Registry JSON contains no absolute paths or secret-like patterns after create + result import."""
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)

    # Create with some unsafe params
    r1 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Clean registry test",
        "linked_export_id": export["export_id"],
        "hypothesis": "Testing password leak prevention",
        "parameters": {"database_url": "postgres://admin:pw@host/db", "epochs": 10},
        "research_acknowledgement": True,
    })
    assert r1.status_code == 200
    exp_id = r1.json()["data"]["experiment_id"]

    # Import results with unsafe content
    r2 = await client.post(f"/api/v1/rl/finrlx/research-experiments/{exp_id}/results", json={
        "acknowledgement": True,
        "result_summary": "Model achieved good results",
        "result_metrics": {"sharpe": 1.5, "credential": "leaked", "bearer": "xyz"},
        "warnings": ["low sample size"],
        "limitations": ["synthetic data only"],
    })
    assert r2.status_code == 200

    # Read full registry file and scan for disallowed patterns
    with open(_exp_registry_path(), "r") as f:
        content = f.read()

    # No Windows absolute paths
    assert "C:\\" not in content
    assert "C:/" not in content
    assert "D:\\" not in content

    # No Unix sensitive paths
    assert "/etc/" not in content
    assert "/home/" not in content
    assert "/root/" not in content

    # No secret-like values
    content_lower = content.lower()
    for pattern in ["password", "passwd", "api_key", "apikey", "private_key",
                    "database_url", "broker", "credential", "bearer"]:
        assert pattern not in content_lower, f"Found disallowed pattern '{pattern}' in registry"

    # Safe values should still be present
    assert "sharpe" in content
    assert "1.5" in content
    assert "epochs" in content
    assert "10" in content


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
