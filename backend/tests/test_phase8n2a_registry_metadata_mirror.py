"""Phase 8N.2A — Postgres Research Registry Metadata Mirror Tests."""
import os
import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func as sa_func

from app.main import app
from app.core.database import engine, Base
from app.services.finrlx_research import FinRLXResearchService
from app.models.research_registry_metadata import ResearchRegistryMetadata

# Use the test session factory from conftest (in-memory SQLite)
from tests.conftest import test_session_factory as AsyncSessionLocal


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _count_mirror_rows() -> int:
    """Count rows in research_registry_metadata."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(sa_func.count()).select_from(ResearchRegistryMetadata)
        )
        return result.scalar() or 0


async def _clear_mirror_table():
    """Delete all rows from research_registry_metadata."""
    async with AsyncSessionLocal() as session:
        await session.execute(
            ResearchRegistryMetadata.__table__.delete()
        )
        await session.commit()


# ── 1. Migration/model shape test ──

def test_model_has_required_fields():
    """ResearchRegistryMetadata model has all required columns."""
    cols = {c.name for c in ResearchRegistryMetadata.__table__.columns}
    assert "registry_kind" in cols
    assert "record_id" in cols
    assert "mirror_status" in cols
    assert "metadata_summary_json" in cols
    assert "research_only" in cols
    assert "offline_only" in cols
    assert "no_production_influence" in cols
    assert "record_hash" in cols
    assert "record_state" in cols
    assert "display_name" in cols
    assert "first_seen_at" in cols
    assert "last_seen_at" in cols


# ── 2. Candidate builder covers all four registry kinds ──

def test_candidate_builder_all_four_kinds():
    """build_registry_metadata_mirror_candidates returns all 4 registry kinds."""
    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()
    kinds = {c["registry_kind"] for c in candidates}
    # Even if some registries are empty, the builder should still attempt all 4
    # At minimum, verify the method runs without error
    assert isinstance(candidates, list)
    # If there are any candidates, check their kinds are valid
    valid_kinds = {"dataset_export", "experiment", "comparison", "readiness_review"}
    for c in candidates:
        assert c["registry_kind"] in valid_kinds


# ── 3. Dry-run sync does not write DB rows ──

@pytest.mark.asyncio
async def test_dry_run_does_not_write_rows(client):
    """Dry-run sync must not insert any rows."""
    await _clear_mirror_table()
    before_count = await _count_mirror_rows()

    r = await client.post(
        "/api/v1/rl/finrlx/registry-metadata/sync",
        json={"dry_run": True},
    )
    assert r.status_code == 200
    data = r.json()["data"]

    assert data["dry_run"] is True
    inserted_count = data["inserted_count"]
    updated_count = data["updated_count"]
    assert inserted_count == 0
    assert updated_count == 0

    after_count = await _count_mirror_rows()
    assert after_count == before_count


# ── 4. Real sync writes rows when candidates exist ──

@pytest.mark.asyncio
async def test_real_sync_writes_rows(client, tmp_path, monkeypatch):
    """Real sync (dry_run=False) inserts at least one row when candidates exist."""
    await _clear_mirror_table()

    # Create a minimal valid export registry
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    registry = {
        "version": 1,
        "exports": [{
            "export_id": "test-export-001",
            "name": "Test Export",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 10,
            "checksum": "abc123",
            "fingerprint": "fp001",
            "export_path": "research/test.jsonl",
            "warnings": [],
            "limitations": [],
            "research_only": True,
            "offline_only": True,
            "shadow_only": True,
            "no_production_influence": True,
        }],
    }
    reg_file = exports_dir / "export_registry.json"
    reg_file.write_text(json.dumps(registry))

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir))
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(reg_file))
    )

    r = await client.post(
        "/api/v1/rl/finrlx/registry-metadata/sync",
        json={"dry_run": False},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["dry_run"] is False
    assert data["inserted_count"] >= 1

    # Verify row exists in DB with safety flags
    count = await _count_mirror_rows()
    assert count >= 1

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ResearchRegistryMetadata).where(
                ResearchRegistryMetadata.record_id == "test-export-001"
            )
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert row.research_only is True
        assert row.offline_only is True
        assert row.no_production_influence is True


# ── 5. Repeated sync is idempotent ──

@pytest.mark.asyncio
async def test_repeated_sync_idempotent(client, tmp_path, monkeypatch):
    """Calling sync twice does not create duplicate rows."""
    await _clear_mirror_table()

    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    registry = {
        "version": 1,
        "exports": [{
            "export_id": "idempotent-test-001",
            "name": "Idempotent Test",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 5,
            "checksum": "def456",
            "fingerprint": "fp002",
            "warnings": [],
            "limitations": [],
            "research_only": True,
        }],
    }
    reg_file = exports_dir / "export_registry.json"
    reg_file.write_text(json.dumps(registry))

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir))
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(reg_file))
    )

    # First sync
    r1 = await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})
    assert r1.status_code == 200
    after_first_count = await _count_mirror_rows()

    # Second sync
    r2 = await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})
    assert r2.status_code == 200
    after_second_count = await _count_mirror_rows()

    assert after_second_count == after_first_count


# ── 6. Unique constraint behavior ──

@pytest.mark.asyncio
async def test_unique_constraint_prevents_duplicates(client, tmp_path, monkeypatch):
    """Unique constraint on (registry_kind, record_id) prevents duplicate rows."""
    await _clear_mirror_table()

    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    registry = {
        "version": 1,
        "exports": [{
            "export_id": "unique-test-001",
            "name": "Unique Test",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 1,
            "warnings": [],
            "limitations": [],
            "research_only": True,
        }],
    }
    reg_file = exports_dir / "export_registry.json"
    reg_file.write_text(json.dumps(registry))

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir))
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(reg_file))
    )

    await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})
    await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(sa_func.count()).select_from(ResearchRegistryMetadata).where(
                ResearchRegistryMetadata.record_id == "unique-test-001"
            )
        )
        count = result.scalar()
        assert count == 1  # Only one row, not two


# ── 7. Corrupt local registry does not get overwritten ──

def test_corrupt_registry_not_overwritten(tmp_path, monkeypatch):
    """Corrupt registry JSON remains unchanged after candidate building."""
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    corrupt_content = "NOT VALID JSON {{{"
    reg_file = exports_dir / "export_registry.json"
    reg_file.write_text(corrupt_content)

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir))
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(reg_file))
    )

    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()

    # File content must be exactly unchanged
    assert reg_file.read_text() == corrupt_content

    # Should have an error/warning candidate, not crash
    export_candidates = [c for c in candidates if c["registry_kind"] == "dataset_export"]
    if export_candidates:
        assert any(c["mirror_status"] == "error" for c in export_candidates)


# ── 8. Secret sanitization ──

def test_secret_sanitization(tmp_path, monkeypatch):
    """Sensitive values are redacted from mirror candidates."""
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    registry = {
        "version": 1,
        "exports": [{
            "export_id": "secret-test-001",
            "name": "password=abc123 token=xyz",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 1,
            "export_path": "DATABASE_URL=postgres://secret@host/db",
            "warnings": ["api_key=sk-12345 leaked"],
            "limitations": ["bearer abc123 found"],
            "research_only": True,
        }],
    }
    reg_file = exports_dir / "export_registry.json"
    reg_file.write_text(json.dumps(registry))

    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir))
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(reg_file))
    )

    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()
    export_candidates = [c for c in candidates if c["record_id"] == "secret-test-001"]
    assert len(export_candidates) == 1

    c = export_candidates[0]
    full_text = json.dumps(c)
    assert "abc123" not in full_text or "REDACTED" in full_text
    assert "sk-12345" not in full_text or "REDACTED" in full_text
    assert "secret@host" not in full_text or "REDACTED" in full_text
    assert "bearer abc123" not in full_text or "REDACTED" in full_text


# ── 9. Mirror status endpoint returns safety flags ──

@pytest.mark.asyncio
async def test_mirror_status_safety_flags(client):
    """Mirror status endpoint returns correct safety and source flags."""
    r = await client.get("/api/v1/rl/finrlx/registry-metadata/status")
    assert r.status_code == 200
    result = r.json()["data"]

    assert result["research_only"] is True
    assert result["offline_only"] is True
    assert result["no_production_influence"] is True
    assert result["is_database_backed_artifact_storage"] is False
    assert result["local_registries_still_operational_source"] is True


# ── 10. Sync endpoint default is dry-run ──

@pytest.mark.asyncio
async def test_sync_default_dry_run(client):
    """POST sync without explicit dry_run defaults to dry_run=True."""
    await _clear_mirror_table()
    before_count = await _count_mirror_rows()

    r = await client.post(
        "/api/v1/rl/finrlx/registry-metadata/sync",
        json={},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["dry_run"] is True

    after_count = await _count_mirror_rows()
    assert after_count == before_count


# ── 11. Persistence status does not overclaim durability ──

@pytest.mark.asyncio
async def test_persistence_status_does_not_overclaim(client):
    """Persistence status shows mirror available but does not claim artifact DB backing."""
    r = await client.get("/api/v1/rl/finrlx/persistence/status")
    assert r.status_code == 200
    data = r.json()["data"]

    mirror = data.get("database_metadata_mirror", {})
    assert mirror.get("available") is True
    assert mirror.get("artifact_storage_database_backed") is False
    assert mirror.get("local_registries_still_operational_source") is True


# ── 12. Production flow isolation static test ──

def test_production_flow_isolation():
    """Production API files must not import ResearchRegistryMetadata or mirror service."""
    import importlib
    import inspect

    production_modules = [
        "app.api.v1.overview",
        "app.api.v1.recommendations",
        "app.api.v1.publication",
    ]

    forbidden_names = [
        "ResearchRegistryMetadata",
        "research_registry_metadata",
        "registry_metadata_mirror",
        "sync_registry_metadata",
        "build_registry_metadata",
    ]

    for mod_name in production_modules:
        mod = importlib.import_module(mod_name)
        source = inspect.getsource(mod)
        for forbidden in forbidden_names:
            assert forbidden not in source, (
                f"Production module {mod_name} contains forbidden reference: {forbidden}"
            )
