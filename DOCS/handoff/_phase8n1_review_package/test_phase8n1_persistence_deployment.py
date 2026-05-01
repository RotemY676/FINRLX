"""Phase 8N.1 — Persistence Status & Deployment Reality Gate Tests."""
import os
import json
import pytest

from app.services.finrlx_research import FinRLXResearchService


# ── Schema tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persistence_status_returns_200(client):
    """GET /persistence/status returns 200."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_persistence_status_schema(client):
    """Response contains all required top-level fields."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    data = r.json()["data"]
    assert "storage_mode" in data
    assert "storage_root" in data
    assert "is_local_file_backed" in data
    assert "is_database_backed" in data
    assert "is_persistent_volume_configured" in data
    assert "deployment_environment" in data
    assert "appears_containerized" in data
    assert "registry_statuses" in data
    assert "warnings" in data
    assert "limitations" in data
    assert "recommended_next_action" in data
    assert "research_only" in data
    assert "offline_only" in data
    assert "no_production_influence" in data


@pytest.mark.asyncio
async def test_persistence_status_all_four_registries(client):
    """Response includes status for all 4 registry categories."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    data = r.json()["data"]
    names = {s["registry_name"] for s in data["registry_statuses"]}
    assert "dataset_exports" in names
    assert "experiments" in names
    assert "comparisons" in names
    assert "readiness_reviews" in names


@pytest.mark.asyncio
async def test_persistence_status_local_file_backed(client):
    """Reports local file-backed mode."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    data = r.json()["data"]
    assert data["storage_mode"] == "local_file_backed"
    assert data["is_local_file_backed"] is True
    assert data["is_database_backed"] is False


# ── Safety invariant tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persistence_status_safety_invariants(client):
    """Safety invariant fields are all true."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    data = r.json()["data"]
    assert data["research_only"] is True
    assert data["offline_only"] is True
    assert data["no_production_influence"] is True


# ── Registry status tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_registry_status_fields(client):
    """Each registry status has the expected fields."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    data = r.json()["data"]
    for reg in data["registry_statuses"]:
        assert "registry_name" in reg
        assert "registry_kind" in reg
        assert "directory_path" in reg
        assert "registry_file_path" in reg
        assert "directory_exists" in reg
        assert "registry_file_exists" in reg
        assert "directory_readable" in reg
        assert "directory_writable" in reg
        assert "status" in reg
        assert "warnings" in reg
        assert reg["status"] in ("ok", "missing", "degraded", "unavailable")


# ── Missing directory test ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_directory_reported_truthfully(client, tmp_path, monkeypatch):
    """Missing directories are reported as missing, not silently treated as ok."""
    fake_root = str(tmp_path / "nonexistent_project")
    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: os.path.join(fake_root, "research", "finrlx_cpu", "exports")),
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: os.path.join(fake_root, "research", "finrlx_cpu", "exports", "export_registry.json")),
    )
    result = FinRLXResearchService.get_persistence_status()
    export_status = next(
        s for s in result["registry_statuses"] if s["registry_name"] == "dataset_exports"
    )
    assert export_status["directory_exists"] is False
    assert export_status["status"] in ("missing", "unavailable")


# ── Corrupt registry test ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_corrupt_registry_reported_as_degraded(client, tmp_path, monkeypatch):
    """Corrupt registry JSON is reported as degraded, not overwritten."""
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    registry_file = exports_dir / "export_registry.json"
    registry_file.write_text("NOT VALID JSON {{{")

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir)),
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(registry_file)),
    )

    result = FinRLXResearchService.get_persistence_status()
    export_status = next(
        s for s in result["registry_statuses"] if s["registry_name"] == "dataset_exports"
    )
    assert export_status["status"] in ("degraded", "unavailable")
    assert len(export_status["warnings"]) > 0

    # Verify file was NOT modified
    assert registry_file.read_text() == "NOT VALID JSON {{{"


# ── Read-only test ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persistence_status_is_read_only(client, tmp_path, monkeypatch):
    """Endpoint does not create or modify registry files."""
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    registry_file = exports_dir / "export_registry.json"
    registry_file.write_text('{"version":1,"exports":[]}')
    original_content = registry_file.read_text()

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir)),
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(registry_file)),
    )

    FinRLXResearchService.get_persistence_status()

    assert registry_file.read_text() == original_content


# ── Environment detection tests ───────────────────────────────────────


def test_railway_env_detected(monkeypatch):
    """Railway environment vars trigger railway detection."""
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "test-project")
    result = FinRLXResearchService.get_persistence_status()
    assert result["deployment_environment"] == "railway"
    assert result["appears_containerized"] is True


def test_persistent_volume_detected(monkeypatch):
    """RAILWAY_VOLUME_MOUNT_PATH triggers persistent volume flag."""
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "/data")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    result = FinRLXResearchService.get_persistence_status()
    assert result["is_persistent_volume_configured"] is True


def test_local_environment_default():
    """Without Railway/container vars, reports local."""
    result = FinRLXResearchService.get_persistence_status()
    # In local test, should be "local" (unless running in actual container)
    assert result["deployment_environment"] in ("local", "container", "unknown")


# ── Secret safety test ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_secrets_in_response(client, monkeypatch):
    """Response does not expose secret-like env vars."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://secret:password@host/db")
    monkeypatch.setenv("API_KEY", "sk-secret-key-12345")
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    body = r.text
    assert "secret:password" not in body
    assert "sk-secret-key" not in body
    assert "DATABASE_URL" not in body.replace("is_database_backed", "")


# ── Limitations test ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_limitations_present(client):
    """Response includes meaningful limitations."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    data = r.json()["data"]
    assert isinstance(data["limitations"], list)
    assert len(data["limitations"]) > 0
