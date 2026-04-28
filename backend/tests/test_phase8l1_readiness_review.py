"""Phase 8L.1 tests: research readiness review gates."""
import json
import os
import pytest

from app.services.finrlx_research import FinRLXResearchService


def _rd_registry_path():
    return FinRLXResearchService._readiness_registry_path()


def _cmp_registry_path():
    return FinRLXResearchService._comparison_registry_path()


def _exp_registry_path():
    return FinRLXResearchService._experiment_registry_path()


def _clear_rd_registry():
    path = _rd_registry_path()
    if os.path.exists(path):
        os.remove(path)


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
        "name": "Readiness Test Export",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    return r.json()["data"]


async def _setup_comparison(client) -> str:
    """Create export, 2 experiments with results, and a comparison. Return comparison_id."""
    _clear_rd_registry()
    _clear_cmp_registry()
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    # Exp 1
    r1 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Exp A", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    eid1 = r1.json()["data"]["experiment_id"]
    await client.post(f"/api/v1/rl/finrlx/research-experiments/{eid1}/results", json={
        "acknowledgement": True, "result_summary": "A results",
        "result_metrics": {"sharpe_ratio": 1.5, "max_drawdown": -0.08},
    })
    await client.post(f"/api/v1/rl/finrlx/research-experiments/{eid1}/state", json={
        "lifecycle_state": "completed", "acknowledgement": True,
    })
    # Exp 2
    r2 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "Exp B", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    eid2 = r2.json()["data"]["experiment_id"]
    await client.post(f"/api/v1/rl/finrlx/research-experiments/{eid2}/results", json={
        "acknowledgement": True, "result_summary": "B results",
        "result_metrics": {"sharpe_ratio": 1.2, "max_drawdown": -0.05},
    })
    await client.post(f"/api/v1/rl/finrlx/research-experiments/{eid2}/state", json={
        "lifecycle_state": "completed", "acknowledgement": True,
    })
    # Comparison
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Readiness Cmp", "experiment_ids": [eid1, eid2],
        "metric_priority": ["sharpe_ratio"], "research_acknowledgement": True,
    })
    return cr.json()["data"]["comparison_id"]


# ── Registry creation ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_readiness_registry_created_when_missing(client):
    _clear_rd_registry()
    reg = FinRLXResearchService.load_readiness_registry()
    assert reg["version"] == 1
    assert isinstance(reg["readiness_reviews"], list)
    assert os.path.exists(_rd_registry_path())


# ── Create requires acknowledgement ──────────────────────────────

@pytest.mark.asyncio
async def test_create_requires_acknowledgement(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": False,
    })
    assert r.status_code == 422


# ── Create requires valid comparison ─────────────────────────────

@pytest.mark.asyncio
async def test_create_requires_valid_comparison(client):
    _clear_rd_registry()
    _clear_cmp_registry()
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Test", "linked_comparison_id": "nonexistent",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


# ── Create succeeds ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_succeeds(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Valid Review", "linked_comparison_id": cmp_id,
        "operator_notes": "Testing readiness", "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["readiness_id"] is not None
    assert data["status"] == "created"
    assert data["readiness_state"] == "draft"


# ── Safety flags ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_includes_safety_flags(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Safety Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["research_only"] is True
    assert data["offline_only"] is True
    assert data["no_production_influence"] is True
    assert data["not_eligible_for_promotion"] is True
    assert data["safety_flags"]["research_only"] is True


# ── Links comparison, experiments, exports ────────────────────────

@pytest.mark.asyncio
async def test_links_comparison_experiments_exports(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Link Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["linked_comparison_id"] == cmp_id
    assert len(data["linked_experiment_ids"]) == 2
    assert len(data["linked_export_ids"]) >= 1


# ── Evidence summary includes comparison ─────────────────────────

@pytest.mark.asyncio
async def test_evidence_includes_comparison_summary(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Evidence Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    ev = r.json()["data"]["evidence_summary"]
    assert "comparison" in ev
    assert ev["comparison"]["comparison_id"] == cmp_id


# ── Evidence includes metric coverage ────────────────────────────

@pytest.mark.asyncio
async def test_evidence_includes_metric_coverage(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Metric Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    ev = r.json()["data"]["evidence_summary"]
    assert "metric_coverage" in ev


# ── Findings include warnings when applicable ────────────────────

@pytest.mark.asyncio
async def test_findings_include_warnings(client):
    _clear_rd_registry()
    _clear_cmp_registry()
    _clear_exp_registry()
    _clear_export_registry()
    export = await _create_export(client)
    # Create experiment without results
    r1 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "No Res", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    r2 = await client.post("/api/v1/rl/finrlx/research-experiments", json={
        "name": "No Res B", "linked_export_id": export["export_id"],
        "research_acknowledgement": True,
    })
    eid1 = r1.json()["data"]["experiment_id"]
    eid2 = r2.json()["data"]["experiment_id"]
    cr = await client.post("/api/v1/rl/finrlx/experiment-comparisons", json={
        "name": "Inc Cmp", "experiment_ids": [eid1, eid2],
        "research_acknowledgement": True,
    })
    cmp_id = cr.json()["data"]["comparison_id"]
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Find Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    findings = r.json()["data"]["readiness_findings"]
    assert len(findings) > 0
    assert any("no result metrics" in f["message"].lower() for f in findings)


# ── Path safety ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_registry_paths_relative(client):
    path = _rd_registry_path()
    assert "research" in path
    assert "readiness" in path


@pytest.mark.asyncio
async def test_registry_no_absolute_paths(client):
    cmp_id = await _setup_comparison(client)
    await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Path Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    assert "C:\\" not in content
    assert "C:/" not in content


@pytest.mark.asyncio
async def test_registry_no_secrets(client):
    cmp_id = await _setup_comparison(client)
    await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Secret Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    for pat in ["PASSWORD", "SECRET", "API_KEY", "DATABASE_URL"]:
        assert pat not in content


# ── Sanitization ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sanitizes_unsafe_fields(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Safe name",
        "linked_comparison_id": cmp_id,
        "operator_notes": r"From C:\Users\Rotem\.env with database_url",
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["operator_notes"] == "[redacted]"
    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    assert "C:\\Users" not in content


# ── List newest first ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_newest_first(client):
    cmp_id = await _setup_comparison(client)
    r1 = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "First", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    r2 = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Second", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    r = await client.get("/api/v1/rl/finrlx/research-readiness")
    assert r.status_code == 200
    data = r.json()["data"]
    ids = [rv["readiness_id"] for rv in data]
    assert ids.index(r2.json()["data"]["readiness_id"]) < ids.index(r1.json()["data"]["readiness_id"])


# ── Get by ID ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_by_id(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Get Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    r = await client.get(f"/api/v1/rl/finrlx/research-readiness/{rid}")
    assert r.status_code == 200
    assert r.json()["data"]["readiness_id"] == rid
    assert "safety_flags" in r.json()["data"]


@pytest.mark.asyncio
async def test_invalid_id_returns_404(client):
    _clear_rd_registry()
    r = await client.get("/api/v1/rl/finrlx/research-readiness/nonexistent")
    assert r.status_code == 404


# ── State update ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_state_update_requires_acknowledgement(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "State Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    r = await client.post(f"/api/v1/rl/finrlx/research-readiness/{rid}/state", json={
        "readiness_state": "needs_more_evidence", "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_state_update_rejects_invalid_state(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Invalid State", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    r = await client.post(f"/api/v1/rl/finrlx/research-readiness/{rid}/state", json={
        "readiness_state": "production_ready", "acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_research_review_ready_requires_checklist(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Gate Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    # Try to go directly to research_review_ready without checklist
    r = await client.post(f"/api/v1/rl/finrlx/research-readiness/{rid}/state", json={
        "readiness_state": "research_review_ready", "acknowledgement": True,
    })
    assert r.status_code == 422
    assert "checklist" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_state_update_succeeds(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Update Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    r = await client.post(f"/api/v1/rl/finrlx/research-readiness/{rid}/state", json={
        "readiness_state": "needs_more_evidence", "acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["readiness_state"] == "needs_more_evidence"


# ── Archive ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_archive_requires_acknowledgement(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Archive Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    r = await client.post(f"/api/v1/rl/finrlx/research-readiness/{rid}/archive", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_archive_succeeds(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Archive OK", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    r = await client.post(f"/api/v1/rl/finrlx/research-readiness/{rid}/archive", json={
        "acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["readiness_state"] == "archived"


# ── Verify read-only ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_is_read_only(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Verify RO", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    with open(_rd_registry_path(), "r") as f:
        before = f.read()
    r = await client.get(f"/api/v1/rl/finrlx/research-readiness/{rid}/verify")
    assert r.status_code == 200
    with open(_rd_registry_path(), "r") as f:
        after = f.read()
    assert before == after


@pytest.mark.asyncio
async def test_verify_reports_missing_comparison(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Verify Missing", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    _clear_cmp_registry()
    r = await client.get(f"/api/v1/rl/finrlx/research-readiness/{rid}/verify")
    assert r.status_code == 200
    assert r.json()["data"]["healthy"] is False
    assert any("comparison" in w.lower() for w in r.json()["data"]["warnings"])


@pytest.mark.asyncio
async def test_verify_reports_missing_experiment(client):
    cmp_id = await _setup_comparison(client)
    cr = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Verify Exp", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    rid = cr.json()["data"]["readiness_id"]
    _clear_exp_registry()
    r = await client.get(f"/api/v1/rl/finrlx/research-readiness/{rid}/verify")
    assert r.status_code == 200
    assert r.json()["data"]["healthy"] is False


# ── Corrupt registries ───────────────────────────────────────────

def _corrupt_rd_registry():
    path = _rd_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("{{{bad")


@pytest.mark.asyncio
async def test_corrupt_readiness_registry_not_overwritten(client):
    _corrupt_rd_registry()
    reg = FinRLXResearchService.load_readiness_registry()
    assert reg.get("registry_corrupt") is True
    with open(_rd_registry_path(), "r") as f:
        assert "{{{bad" in f.read()
    _clear_rd_registry()


@pytest.mark.asyncio
async def test_corrupt_readiness_registry_returns_409(client):
    _corrupt_rd_registry()
    r = await client.get("/api/v1/rl/finrlx/research-readiness")
    assert r.status_code == 409
    _clear_rd_registry()


@pytest.mark.asyncio
async def test_corrupt_comparison_registry_returns_error(client):
    _clear_rd_registry()
    path = _cmp_registry_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("{{{bad")
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Test", "linked_comparison_id": "x", "research_acknowledgement": True,
    })
    assert r.status_code in (409, 422)
    _clear_cmp_registry()


@pytest.mark.asyncio
async def test_rebuild_requires_acknowledgement(client):
    r = await client.post("/api/v1/rl/finrlx/research-readiness/rebuild-registry", json={
        "acknowledgement": False,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rebuild_succeeds(client):
    _corrupt_rd_registry()
    r = await client.post("/api/v1/rl/finrlx/research-readiness/rebuild-registry", json={
        "acknowledgement": True,
    })
    assert r.status_code == 200
    assert r.json()["data"]["rebuilt"] is True
    _clear_rd_registry()


# ── Production isolation ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_does_not_trigger_training(client):
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.json()["data"]["training_mode"] == "stubbed"


@pytest.mark.asyncio
async def test_does_not_trigger_benchmark(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "No Bench", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    assert r.json()["data"]["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_does_not_alter_recommendations(client):
    r_before = await client.get("/api/v1/recommendations/current")
    before = r_before.json()
    cmp_id = await _setup_comparison(client)
    await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Iso Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    r_after = await client.get("/api/v1/recommendations/current")
    after = r_after.json()
    assert before["data"]["id"] == after["data"]["id"]


@pytest.mark.asyncio
async def test_does_not_alter_overview(client):
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_does_not_alter_publication(client):
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_does_not_promote_candidates(client):
    cmp_id = await _setup_comparison(client)
    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Promo Test", "linked_comparison_id": cmp_id, "research_acknowledgement": True,
    })
    assert r.json()["data"]["not_eligible_for_promotion"] is True


# ── Readiness evidence sanitization (legacy unsafe data) ─────────

def _inject_unsafe_comparison_data(comparison_id: str):
    """Directly edit comparison_registry.json to simulate legacy unsafe data."""
    path = FinRLXResearchService._comparison_registry_path()
    with open(path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    for cmp in reg.get("comparisons", []):
        if cmp.get("comparison_id") == comparison_id:
            cmp["name"] = r"Loaded from C:\Users\Rotem\.env"
            cs = cmp.get("comparison_summary") or {}
            cs["metric_coverage"] = {
                "sharpe_ratio": {"available_count": 2, "missing_count": 0, "coverage_ratio": 1.0},
                "api_key": {"available_count": 1, "missing_count": 1, "coverage_ratio": 0.5},
                "/etc/passwd": {"available_count": 1, "missing_count": 1, "coverage_ratio": 0.5},
            }
            cs["missing_metrics"] = {
                "exp-1": ["DATABASE_URL", "/etc/passwd", "safe_metric"],
            }
            cmp["comparison_summary"] = cs
            cmp["warnings"] = ["token=abc123"]
            cmp["limitations"] = ["broker credential leaked"]
            break
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)


@pytest.mark.asyncio
async def test_readiness_sanitizes_legacy_unsafe_comparison_evidence(client):
    """Readiness evidence defensively sanitizes legacy unsafe comparison data."""
    cmp_id = await _setup_comparison(client)
    _inject_unsafe_comparison_data(cmp_id)

    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Legacy Sanitize", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]

    resp_str = json.dumps(data)
    for unsafe in ["C:\\Users", ".env", "/etc/passwd", "DATABASE_URL",
                    "token=abc123", "broker credential", "postgres://"]:
        assert unsafe not in resp_str, f"Found '{unsafe}' in readiness response"

    # safe metric keys should remain
    ev = data["evidence_summary"]
    assert "sharpe_ratio" in ev.get("metric_coverage", {})

    # Check registry file
    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["C:\\Users", ".env", "/etc/passwd", "DATABASE_URL",
                    "token=abc123", "broker credential", "postgres://"]:
        assert unsafe not in content, f"Found '{unsafe}' in readiness registry"


@pytest.mark.asyncio
async def test_readiness_findings_do_not_leak_unsafe_text(client):
    """Readiness findings do not include unsafe lifecycle/registry text."""
    cmp_id = await _setup_comparison(client)
    # Inject unsafe lifecycle_state into experiment
    exp_path = _exp_registry_path()
    with open(exp_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    if reg.get("experiments"):
        reg["experiments"][0]["lifecycle_state"] = r"C:\Users\Rotem\secret"
    with open(exp_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Finding Sanitize", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    findings_str = json.dumps(r.json()["data"].get("readiness_findings", []))
    for unsafe in ["C:\\Users", "/etc/passwd", "DATABASE_URL", "api_key"]:
        assert unsafe not in findings_str, f"Found '{unsafe}' in findings"


@pytest.mark.asyncio
async def test_readiness_registry_clean_after_legacy_evidence(client):
    """Readiness registry contains no unsafe patterns after legacy data."""
    cmp_id = await _setup_comparison(client)
    _inject_unsafe_comparison_data(cmp_id)

    await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Registry Clean", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })

    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    content_lower = content.lower()

    for pattern in ["c:\\users", "/etc/", "postgres://"]:
        assert pattern not in content_lower, f"Found '{pattern}' in readiness registry"
    for pattern in ["api_key", "database_url", "credential"]:
        assert pattern not in content_lower, f"Found '{pattern}' in readiness registry"


# ── Nested metric coverage and linked ID sanitization ────────────

@pytest.mark.asyncio
async def test_readiness_sanitizes_metric_coverage_nested_values(client):
    """Metric coverage nested values are sanitized — only safe primitives stored."""
    cmp_id = await _setup_comparison(client)
    # Inject unsafe nested values into metric_coverage
    cmp_path = FinRLXResearchService._comparison_registry_path()
    with open(cmp_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    for cmp in reg.get("comparisons", []):
        if cmp.get("comparison_id") == cmp_id:
            cmp["comparison_summary"]["metric_coverage"] = {
                "sharpe_ratio": {
                    "available_count": 2,
                    "missing_count": 0,
                    "coverage_ratio": 1.0,
                    "debug_path": r"C:\Users\Rotem\.env",
                    "database_url": "postgres://secret",
                    "token": "abc123",
                },
            }
            break
    with open(cmp_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Nested MC Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]

    # Safe fields preserved
    ev = data["evidence_summary"]
    mc = ev.get("metric_coverage", {})
    assert "sharpe_ratio" in mc
    sr = mc["sharpe_ratio"]
    assert sr.get("available_count") == 2
    assert sr.get("missing_count") == 0
    assert sr.get("coverage_ratio") == 1.0

    # Unsafe nested values dropped
    assert "debug_path" not in sr
    assert "database_url" not in sr
    assert "token" not in sr

    # Registry file check
    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["C:\\Users", ".env", "database_url", "postgres://", "abc123"]:
        assert unsafe not in content, f"Found '{unsafe}' in readiness registry"


@pytest.mark.asyncio
async def test_readiness_sanitizes_legacy_unsafe_linked_ids(client):
    """Unsafe linked experiment/export IDs are dropped from readiness."""
    cmp_id = await _setup_comparison(client)
    # Inject unsafe IDs into comparison
    cmp_path = FinRLXResearchService._comparison_registry_path()
    with open(cmp_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    for cmp in reg.get("comparisons", []):
        if cmp.get("comparison_id") == cmp_id:
            # Add unsafe experiment IDs
            cmp["experiment_ids"].extend([
                r"C:\Users\Rotem\.env",
                "api_key=sk-test-secret",
            ])
            # Add unsafe export IDs in snapshots
            cmp["experiment_snapshots"].append({
                "experiment_id": "safe-snap",
                "linked_export_id": "/etc/passwd",
                "name": "test", "lifecycle_state": "completed",
                "result_metrics": {}, "warnings": [], "limitations": [],
            })
            cmp["experiment_snapshots"].append({
                "experiment_id": "safe-snap-2",
                "linked_export_id": "DATABASE_URL=postgres://secret",
                "name": "test2", "lifecycle_state": "completed",
                "result_metrics": {}, "warnings": [], "limitations": [],
            })
            break
    with open(cmp_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

    r = await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Linked ID Test", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]

    # Unsafe IDs should not be in linked lists
    resp_str = json.dumps(data)
    for unsafe in ["C:\\Users", ".env", "api_key", "sk-test-secret",
                    "/etc/passwd", "DATABASE_URL", "postgres://"]:
        assert unsafe not in resp_str, f"Found '{unsafe}' in response"

    # Registry file check
    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    for unsafe in ["C:\\Users", "sk-test-secret", "/etc/passwd", "DATABASE_URL", "postgres://"]:
        assert unsafe not in content, f"Found '{unsafe}' in readiness registry"


@pytest.mark.asyncio
async def test_readiness_registry_clean_after_nested_and_id_injection(client):
    """Full registry scan after nested metric and linked ID injection."""
    cmp_id = await _setup_comparison(client)
    cmp_path = FinRLXResearchService._comparison_registry_path()
    with open(cmp_path, "r", encoding="utf-8") as f:
        reg = json.load(f)
    for cmp in reg.get("comparisons", []):
        if cmp.get("comparison_id") == cmp_id:
            cmp["experiment_ids"].append("token=leaked")
            cmp["comparison_summary"]["metric_coverage"]["sharpe_ratio"] = {
                "available_count": 2, "coverage_ratio": 1.0,
                "secret": "password123", "broker": "cred",
            }
            break
    with open(cmp_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

    await client.post("/api/v1/rl/finrlx/research-readiness", json={
        "name": "Full Scan", "linked_comparison_id": cmp_id,
        "research_acknowledgement": True,
    })

    with open(_rd_registry_path(), "r") as f:
        content = f.read()
    content_lower = content.lower()

    for pattern in ["c:\\", "/etc/", "postgres://"]:
        assert pattern not in content_lower, f"Found '{pattern}'"
    for pattern in ["password123", "token=leaked"]:
        assert pattern not in content_lower, f"Found '{pattern}'"


@pytest.mark.asyncio
async def test_rl_execute_remains_absent(client):
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


# ── Regression ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_existing_pipeline_still_works(client):
    from datetime import date
    today = date.today().isoformat()
    r = await client.post("/api/v1/features/compute", json={"as_of": today})
    fs_id = r.json()["data"]["feature_set_id"]
    await client.post("/api/v1/engines/run", json={"feature_set_id": fs_id})
    r = await client.post("/api/v1/pipeline/run", json={"feature_set_id": fs_id})
    assert r.json()["data"]["status"] == "completed"
