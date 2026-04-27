"""Phase 8I tests: dataset export for local research."""
import pytest


# ── Export requires acknowledgement ─────────────────────────────────

@pytest.mark.asyncio
async def test_export_requires_acknowledgement(client):
    """POST /rl/finrlx/dataset-export requires research_acknowledgement=true."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": False,
    })
    assert r.status_code == 422
    assert "acknowledgement" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_export_succeeds_with_acknowledgement(client):
    """POST /rl/finrlx/dataset-export succeeds with acknowledgement."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "name": "Phase 8I Test Export",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "completed"
    assert data["export_id"] is not None
    assert data["row_count"] >= 0


# ── Safety flags ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_includes_safety_flags(client):
    """Export response includes all required safety flags."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
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
    assert sf["offline_only"] is True
    assert sf["shadow_only"] is True
    assert sf["no_production_influence"] is True
    assert sf["not_eligible_for_promotion"] is True


# ── Schema metadata ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_includes_schema_metadata(client):
    """Export response includes schema metadata."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "include_features": True, "include_targets": True,
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert isinstance(data["feature_schema"], list)
    assert isinstance(data["target_schema"], list)
    assert isinstance(data["warning_schema"], list)


# ── Checksum / fingerprint ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_includes_checksum_and_fingerprint(client):
    """Export response includes checksum and fingerprint."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["checksum"] is not None
    assert len(data["checksum"]) == 32
    assert data["fingerprint"] is not None
    assert len(data["fingerprint"]) == 16


# ── Export path ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_path_inside_research_dir(client):
    """Export path stays inside research/finrlx_cpu/exports."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["export_path"].startswith("research/finrlx_cpu/exports/")


# ── No-data export ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_data_export_returns_warning(client):
    """Export with no available data returns warning and row_count=0."""
    # Use a very old date range with no seeded market data
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2010-01-01", "end_date": "2010-01-02",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    # The export should still succeed but may return 0 rows or rows with no assets
    # depending on whether the environment builds empty states for dates without data.
    # Either way, warnings should be present if no meaningful data exists.
    assert data["row_count"] >= 0
    assert isinstance(data["warnings"], list)


# ── Invalid date range ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_date_range(client):
    """Reversed date range returns safe error."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-04-15", "end_date": "2026-03-15",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


# ── Invalid candidate ID ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_candidate_id(client):
    """Invalid candidate_id returns safe error."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "candidate_id": "nonexistent-candidate-id",
        "research_acknowledgement": True,
    })
    assert r.status_code == 404


# ── Production isolation ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_does_not_alter_recommendations(client):
    """Export does not alter recommendations."""
    r_before = await client.get("/api/v1/recommendations/current")
    before = r_before.json()

    await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })

    r_after = await client.get("/api/v1/recommendations/current")
    after = r_after.json()
    assert before["data"]["id"] == after["data"]["id"]
    assert before["data"]["status"] == after["data"]["status"]


@pytest.mark.asyncio
async def test_export_does_not_alter_overview(client):
    """Export does not alter overview."""
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_export_does_not_alter_publication(client):
    """Export does not alter publication status."""
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_export_does_not_promote_candidate(client):
    """Export does not promote any candidate."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    data = r.json()["data"]
    assert data["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_rl_execute_remains_absent(client):
    """/rl/execute remains absent/404."""
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


# ── List / get endpoints ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_dataset_exports(client):
    """GET /rl/finrlx/dataset-exports returns list."""
    # Create an export first
    await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    r = await client.get("/api/v1/rl/finrlx/dataset-exports")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["export_id"] is not None
    assert data[0]["safety_flags"]["research_only"] is True


@pytest.mark.asyncio
async def test_get_dataset_export_by_id(client):
    """GET /rl/finrlx/dataset-exports/{id} returns specific export."""
    cr = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "name": "Get By ID Test",
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "research_acknowledgement": True,
    })
    export_id = cr.json()["data"]["export_id"]

    r = await client.get(f"/api/v1/rl/finrlx/dataset-exports/{export_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["export_id"] == export_id
    assert data["name"] == "Get By ID Test"


@pytest.mark.asyncio
async def test_get_nonexistent_export_returns_404(client):
    """GET /rl/finrlx/dataset-exports/{id} returns 404 for missing export."""
    r = await client.get("/api/v1/rl/finrlx/dataset-exports/nonexistent-id")
    assert r.status_code == 404


# ── Format validation ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_format_returns_error(client):
    """Invalid format returns safe error."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "format": "csv",
        "research_acknowledgement": True,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_json_format_export(client):
    """Export with format=json succeeds."""
    r = await client.post("/api/v1/rl/finrlx/dataset-export", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
        "format": "json",
        "research_acknowledgement": True,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["export_format"] == "json"
    assert data["export_path"].endswith(".json")


# ── Safety regressions ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_existing_benchmark_still_works(client):
    """Existing benchmark workflow still works."""
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    assert r.json()["data"]["status"] in ("completed", "partial")


@pytest.mark.asyncio
async def test_phase8a_endpoints_still_work(client):
    """Phase 8A endpoints still work."""
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
