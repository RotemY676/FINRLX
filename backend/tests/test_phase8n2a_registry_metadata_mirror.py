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


# US-P0-03: this module used to shadow conftest's `client` with an
# unauthenticated one. Now that the RL surface is auth-gated at the router
# level that shadow produced 401s, so it is removed and the shared
# (bearer-carrying) fixture is used instead. Keeping a local anonymous client
# here would only re-test the gate, which test_p0_rl_authz.py already does.


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


def _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=False, content=None):
    """Helper: point all 4 registries to tmp_path files."""
    specs = [
        ("_exports_dir", "_registry_path", "exports", "export_registry.json"),
        ("_experiments_dir", "_experiment_registry_path", "experiments", "experiment_registry.json"),
        ("_comparisons_dir", "_comparison_registry_path", "comparisons", "comparison_registry.json"),
        ("_readiness_dir", "_readiness_registry_path", "readiness", "readiness_registry.json"),
    ]
    paths = {}
    for dir_fn, path_fn, subdir, filename in specs:
        d = tmp_path / subdir
        if create_files:
            d.mkdir(exist_ok=True)
        f = d / filename
        if create_files and content and subdir in content:
            d.mkdir(exist_ok=True)
            f.write_text(json.dumps(content[subdir]))
        dir_str, file_str = str(d), str(f)
        monkeypatch.setattr(FinRLXResearchService, dir_fn, staticmethod(lambda ds=dir_str: ds))
        monkeypatch.setattr(FinRLXResearchService, path_fn, staticmethod(lambda fs=file_str: fs))
        paths[subdir] = {"dir": d, "file": f}
    return paths


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


# ── 2. Candidate builder covers all four registry kinds (real) ──

def test_candidate_builder_all_four_kinds(tmp_path, monkeypatch):
    """Candidates include all four registry kinds when all registries have items."""
    content = {
        "exports": {"version": 1, "exports": [
            {"export_id": "e1", "name": "Export 1", "lifecycle_state": "active", "warnings": [], "limitations": []}
        ]},
        "experiments": {"version": 1, "experiments": [
            {"experiment_id": "x1", "name": "Exp 1", "lifecycle_state": "planned", "warnings": [], "limitations": []}
        ]},
        "comparisons": {"version": 1, "comparisons": [
            {"comparison_id": "c1", "name": "Cmp 1", "lifecycle_state": "active", "experiment_ids": [], "warnings": [], "limitations": []}
        ]},
        "readiness": {"version": 1, "readiness_reviews": [
            {"readiness_id": "r1", "name": "Rev 1", "readiness_state": "draft", "warnings": [], "limitations": []}
        ]},
    }
    _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=True, content=content)

    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()
    kinds = {c["registry_kind"] for c in candidates}
    expected = {"dataset_export", "experiment", "comparison", "readiness_review"}
    assert expected.issubset(kinds), f"Expected {expected}, got {kinds}"
    for k in expected:
        assert any(c["registry_kind"] == k for c in candidates), f"No candidate for {k}"


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

    content = {
        "exports": {"version": 1, "exports": [{
            "export_id": "test-export-001",
            "name": "Test Export",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 10,
            "checksum": "abc123safe",
            "fingerprint": "fp001",
            "export_path": "research/test.jsonl",
            "warnings": [],
            "limitations": [],
            "research_only": True,
        }]},
    }
    paths = _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=True, content=content)

    r = await client.post(
        "/api/v1/rl/finrlx/registry-metadata/sync",
        json={"dry_run": False},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["dry_run"] is False
    assert data["inserted_count"] >= 1

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

    content = {
        "exports": {"version": 1, "exports": [{
            "export_id": "idempotent-test-001",
            "name": "Idempotent Test",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 5,
            "warnings": [],
            "limitations": [],
        }]},
    }
    _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=True, content=content)

    r1 = await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})
    assert r1.status_code == 200
    after_first_count = await _count_mirror_rows()

    r2 = await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})
    assert r2.status_code == 200
    after_second_count = await _count_mirror_rows()

    assert after_second_count == after_first_count


# ── 6. Unique constraint behavior ──

@pytest.mark.asyncio
async def test_unique_constraint_prevents_duplicates(client, tmp_path, monkeypatch):
    """Unique constraint on (registry_kind, record_id) prevents duplicate rows."""
    await _clear_mirror_table()

    content = {
        "exports": {"version": 1, "exports": [{
            "export_id": "unique-test-001",
            "name": "Unique Test",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 1,
            "warnings": [],
            "limitations": [],
        }]},
    }
    _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=True, content=content)

    await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})
    await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(sa_func.count()).select_from(ResearchRegistryMetadata).where(
                ResearchRegistryMetadata.record_id == "unique-test-001"
            )
        )
        count = result.scalar()
        assert count == 1


# ── 7. Corrupt local registry does not get overwritten ──

def test_corrupt_registry_not_overwritten(tmp_path, monkeypatch):
    """Corrupt registry JSON remains unchanged after candidate building."""
    corrupt_content = "NOT VALID JSON {{{"
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    reg_file = exports_dir / "export_registry.json"
    reg_file.write_text(corrupt_content)

    paths = _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=False)
    # Override exports specifically with the corrupt file
    monkeypatch.setattr(
        FinRLXResearchService, "_exports_dir",
        staticmethod(lambda: str(exports_dir))
    )
    monkeypatch.setattr(
        FinRLXResearchService, "_registry_path",
        staticmethod(lambda: str(reg_file))
    )

    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()

    # File must be exactly unchanged
    assert reg_file.read_text() == corrupt_content

    # Must have error candidate for dataset_export
    export_candidates = [c for c in candidates if c["registry_kind"] == "dataset_export"]
    assert export_candidates, "Expected at least one dataset_export candidate for corrupt registry"
    assert any(c["mirror_status"] == "error" for c in export_candidates)


# ── 8. Secret sanitization (strict) ──

def test_secret_sanitization_strict(tmp_path, monkeypatch):
    """Sensitive values are strictly absent from mirror candidates."""
    content = {
        "exports": {"version": 1, "exports": [{
            "export_id": "secret-test-001",
            "name": "password=abc123 token=xyz999",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 1,
            "export_path": "DATABASE_URL=postgres://secret@host/db",
            "warnings": ["api_key=sk-12345 leaked"],
            "limitations": ["bearer abc123 found"],
            "research_only": True,
        }]},
    }
    _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=True, content=content)

    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()
    export_candidates = [c for c in candidates if c.get("record_id") == "secret-test-001"]
    assert len(export_candidates) == 1

    c = export_candidates[0]
    full_text = json.dumps(c)

    # Strict absence — raw secrets must NOT appear
    assert "abc123" not in full_text
    assert "sk-12345" not in full_text
    assert "secret@host" not in full_text
    assert "xyz999" not in full_text
    assert "postgres://secret" not in full_text

    # REDACTED must appear (sanitizer replaced them)
    assert "REDACTED" in full_text


# ── 8b. DB-level sanitization test ──

@pytest.mark.asyncio
async def test_db_stored_values_sanitized(client, tmp_path, monkeypatch):
    """Stored DB rows do not contain raw secrets."""
    await _clear_mirror_table()

    content = {
        "exports": {"version": 1, "exports": [{
            "export_id": "db-secret-test-001",
            "name": "password=abc123 token=xyz999",
            "status": "completed",
            "lifecycle_state": "active",
            "row_count": 1,
            "export_path": "DATABASE_URL=postgres://secret@host/db",
            "warnings": ["api_key=sk-12345 leaked"],
            "limitations": ["bearer abc123 credentials=hidden"],
            "result_metrics": {"password": "abc123", "sharpe": 1.2},
            "research_only": True,
        }]},
    }
    _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=True, content=content)

    await client.post("/api/v1/rl/finrlx/registry-metadata/sync", json={"dry_run": False})

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ResearchRegistryMetadata).where(
                ResearchRegistryMetadata.record_id == "db-secret-test-001"
            )
        )
        row = result.scalar_one_or_none()
        assert row is not None

        stored_text = json.dumps({
            "summary": row.metadata_summary_json,
            "warnings": row.warnings_json,
            "limitations": row.limitations_json,
            "display_name": row.display_name,
            "artifact_path": row.artifact_path,
        })

        assert "abc123" not in stored_text
        assert "sk-12345" not in stored_text
        assert "postgres://secret" not in stored_text
        assert "secret@host" not in stored_text


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


# ── 13. Read-only: candidate building does not create missing files ──

def test_candidate_building_does_not_create_files(tmp_path, monkeypatch):
    """Candidate building must NOT create missing registry files."""
    paths = _monkeypatch_all_registries(monkeypatch, tmp_path, create_files=False)

    export_registry_path = paths["exports"]["file"]
    experiment_registry_path = paths["experiments"]["file"]
    comparison_registry_path = paths["comparisons"]["file"]
    readiness_registry_path = paths["readiness"]["file"]

    # Confirm none exist before
    assert not export_registry_path.exists()
    assert not experiment_registry_path.exists()
    assert not comparison_registry_path.exists()
    assert not readiness_registry_path.exists()

    # Run candidate builder
    candidates = FinRLXResearchService.build_registry_metadata_mirror_candidates()

    # All four files must still not exist
    assert not export_registry_path.exists()
    assert not experiment_registry_path.exists()
    assert not comparison_registry_path.exists()
    assert not readiness_registry_path.exists()

    # Method should not crash — returns empty or warning candidates
    assert isinstance(candidates, list)
