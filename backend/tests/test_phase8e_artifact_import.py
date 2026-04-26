"""Phase 8E tests: research artifact import & validation."""
import pytest


def _sample_artifact(**overrides) -> dict:
    """Build a valid sample research artifact."""
    base = {
        "artifact_type": "finrlx_cpu_rl_research_artifact",
        "schema_version": "1.0",
        "research_only": True,
        "offline_only": True,
        "shadow_only": True,
        "not_eligible_for_promotion": True,
        "live_pipeline_influence": False,
        "no_broker_execution": True,
        "no_publication_influence": True,
        "no_recommendation_pollution": True,
        "algorithm": "PPO",
        "real_neural_training": True,
        "cpu_only": True,
        "synthetic_data": True,
        "dataset_summary": {"row_count": 60, "synthetic": True, "source": "test"},
        "training_config": {"algorithm": "PPO", "timesteps": 200, "seed": 42},
        "training_metrics": {"timesteps": 200, "algorithm": "PPO", "seed": 42,
                             "total_reward": 0.01, "training_duration_ms": 500},
        "artifact_created_at": "2026-04-26T12:00:00Z",
        "warnings": ["Synthetic data test artifact."],
    }
    base.update(overrides)
    return base


# ── Validate artifact ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_valid_artifact(client):
    """validate-research-artifact accepts valid sample artifact."""
    r = await client.post("/api/v1/rl/finrlx/validate-research-artifact", json={
        "artifact": _sample_artifact(),
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is True
    assert data["errors"] == []
    assert data["artifact_hash"] is not None
    assert data["safety_flags"]["research_only"] is True


@pytest.mark.asyncio
async def test_validate_rejects_missing_fields(client):
    """validate-research-artifact rejects artifact with missing required fields."""
    bad = {"algorithm": "PPO"}
    r = await client.post("/api/v1/rl/finrlx/validate-research-artifact", json={
        "artifact": bad,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["valid"] is False
    assert len(data["errors"]) > 0


@pytest.mark.asyncio
async def test_validate_rejects_live_pipeline_influence(client):
    """validate-research-artifact rejects live_pipeline_influence=true."""
    r = await client.post("/api/v1/rl/finrlx/validate-research-artifact", json={
        "artifact": _sample_artifact(live_pipeline_influence=True),
    })
    data = r.json()["data"]
    assert data["valid"] is False
    assert any("live_pipeline_influence" in e for e in data["errors"])


@pytest.mark.asyncio
async def test_validate_rejects_no_broker_false(client):
    """validate-research-artifact rejects no_broker_execution=false."""
    r = await client.post("/api/v1/rl/finrlx/validate-research-artifact", json={
        "artifact": _sample_artifact(no_broker_execution=False),
    })
    data = r.json()["data"]
    assert data["valid"] is False
    assert any("no_broker_execution" in e for e in data["errors"])


@pytest.mark.asyncio
async def test_validate_rejects_promotion_eligible(client):
    """validate-research-artifact rejects not_eligible_for_promotion=false."""
    r = await client.post("/api/v1/rl/finrlx/validate-research-artifact", json={
        "artifact": _sample_artifact(not_eligible_for_promotion=False),
    })
    data = r.json()["data"]
    assert data["valid"] is False
    assert any("not_eligible_for_promotion" in e for e in data["errors"])


@pytest.mark.asyncio
async def test_validate_rejects_invalid_algorithm(client):
    """validate-research-artifact rejects invalid algorithm."""
    r = await client.post("/api/v1/rl/finrlx/validate-research-artifact", json={
        "artifact": _sample_artifact(algorithm="DQN"),
    })
    data = r.json()["data"]
    assert data["valid"] is False
    assert any("algorithm" in e for e in data["errors"])


# ── Import artifact ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_requires_acknowledgement(client):
    """import-research-artifact requires import_acknowledgement=true."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": False,
        "source": "test",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_artifact_import_rejected(client):
    """Invalid artifact import returns 422 and creates no candidate."""
    r1 = await client.get("/api/v1/rl/finrlx/candidates")
    before = len(r1.json()["data"])

    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": {"algorithm": "PPO"},
        "import_acknowledgement": True,
        "source": "test",
    })
    assert r.status_code == 422

    r2 = await client.get("/api/v1/rl/finrlx/candidates")
    assert len(r2.json()["data"]) == before


@pytest.mark.asyncio
async def test_valid_import_creates_candidate(client):
    """Valid artifact import creates a research-only candidate."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test_suite",
        "notes": "Phase 8E test import",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "imported"
    assert data["policy_candidate_id"] is not None
    assert data["imported_from_artifact"] is True
    assert data["policy_type"] == "finrlx_cpu_ppo_research_import"
    assert data["training_mode"] == "imported_cpu_ppo_research"
    assert data["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_imported_candidate_has_safety_flags(client):
    """Imported candidate has safety_flags."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test",
    })
    data = r.json()["data"]
    sf = data["safety_flags"]
    assert sf["research_only"] is True
    assert sf["offline_only"] is True
    assert sf["no_broker_execution"] is True
    assert sf["no_publication_influence"] is True


@pytest.mark.asyncio
async def test_imported_candidate_has_artifact_hash(client):
    """Imported candidate has deterministic artifact_hash."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test",
    })
    data = r.json()["data"]
    assert data["artifact_hash"] is not None
    assert len(data["artifact_hash"]) == 32  # SHA-256 truncated


@pytest.mark.asyncio
async def test_imported_candidate_isolation_all_blocked(client):
    """Imported candidate isolation blocks all five actions."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test",
    })
    cid = r.json()["data"]["policy_candidate_id"]
    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}/isolation")
    assert r2.status_code == 200
    iso = r2.json()["data"]
    assert iso["all_blocked"] is True
    assert iso["checks"]["promotion_blocked"] is True
    assert iso["checks"]["publication_blocked"] is True
    assert iso["checks"]["live_recommendation_blocked"] is True
    assert iso["checks"]["overview_influence_blocked"] is True
    assert iso["checks"]["broker_execution_blocked"] is True


@pytest.mark.asyncio
async def test_import_captures_fingerprints(client):
    """Import captures production_fingerprints/component_checks."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test",
    })
    fp = r.json()["data"]["production_fingerprints"]
    assert fp is not None
    assert "component_checks" in fp
    assert "recommendations_current" in fp["component_checks"]
    assert "publication_status" in fp["component_checks"]
    assert "overview" in fp["component_checks"]
    assert "unchanged" in fp


@pytest.mark.asyncio
async def test_import_creates_audit_events(client):
    """Import creates persisted audit events."""
    from tests.conftest import test_session_factory
    from sqlalchemy import select
    from app.models.ops import AuditEvent

    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(algorithm="A2C"),
        "import_acknowledgement": True,
        "source": "audit_test",
    })
    assert r.status_code == 200

    async with test_session_factory() as db:
        events = (await db.execute(
            select(AuditEvent)
            .where(AuditEvent.object_type == "finrlx_research")
            .where(AuditEvent.action.like("finrlx_research_artifact_import_%"))
            .order_by(AuditEvent.occurred_at.desc())
        )).scalars().all()

    actions = {e.action for e in events}
    assert "finrlx_research_artifact_import_requested" in actions
    assert "finrlx_research_artifact_import_completed" in actions

    completed = next(e for e in events if e.action == "finrlx_research_artifact_import_completed")
    cd = completed.details or {}
    assert cd.get("candidate_id") is not None
    assert cd.get("policy_type") == "finrlx_cpu_a2c_research_import"
    assert cd.get("artifact_hash") is not None
    assert cd.get("safety_flags", {}).get("research_only") is True
    assert cd.get("isolation_checks", {}).get("promotion_blocked") is True
    assert cd.get("component_checks") is not None
    assert "production_fingerprints_unchanged" in cd


@pytest.mark.asyncio
async def test_rejected_import_creates_audit_event(client):
    """Rejected import creates audit event."""
    from tests.conftest import test_session_factory
    from sqlalchemy import select
    from app.models.ops import AuditEvent

    await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": {"bad": True},
        "import_acknowledgement": True,
        "source": "reject_test",
    })

    async with test_session_factory() as db:
        events = (await db.execute(
            select(AuditEvent)
            .where(AuditEvent.action == "finrlx_research_artifact_import_rejected")
        )).scalars().all()

    assert len(events) >= 1
    matching = [e for e in events if (e.details or {}).get("source") == "reject_test"]
    assert len(matching) >= 1
    rd = matching[0].details or {}
    assert len(rd.get("validation_errors", [])) > 0


@pytest.mark.asyncio
async def test_imported_candidate_in_list(client):
    """Imported candidate appears in candidate list."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test",
    })
    cid = r.json()["data"]["policy_candidate_id"]

    r2 = await client.get("/api/v1/rl/finrlx/candidates")
    ids = [c["id"] for c in r2.json()["data"]]
    assert cid in ids


@pytest.mark.asyncio
async def test_imported_candidate_detail(client):
    """Imported candidate detail shows artifact metadata."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "test",
    })
    cid = r.json()["data"]["policy_candidate_id"]

    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["policy_type"] == "finrlx_cpu_ppo_research_import"
    assert data["safety_flags"]["research_only"] is True


# ── Candidate metadata exposure (Phase 8E.1) ─────────────────────────

@pytest.mark.asyncio
async def test_imported_candidate_detail_has_artifact_metadata(client):
    """GET /candidates/{id} returns imported_from_artifact, artifact_hash, artifact_summary."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "metadata_test",
        "notes": "8E.1 metadata test",
    })
    cid = r.json()["data"]["policy_candidate_id"]

    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["imported_from_artifact"] is True
    assert data["artifact_hash"] is not None
    assert len(data["artifact_hash"]) == 32
    assert data["artifact_summary"] is not None
    assert data["artifact_summary"]["algorithm"] == "PPO"
    assert data["not_eligible_for_promotion"] is True
    assert data["source"] == "metadata_test"
    assert data["notes"] == "8E.1 metadata test"
    assert data["training_mode"] == "imported_cpu_ppo_research"
    assert data["real_neural_training"] is True


@pytest.mark.asyncio
async def test_non_imported_candidate_has_consistent_fields(client):
    """Non-imported candidate returns imported_from_artifact=false, null hash/summary."""
    r = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    cid = r.json()["data"]["policy_candidate_id"]

    r2 = await client.get(f"/api/v1/rl/finrlx/candidates/{cid}")
    data = r2.json()["data"]
    assert data["imported_from_artifact"] is False
    assert data["artifact_hash"] is None
    assert data["artifact_summary"] is None
    assert data["not_eligible_for_promotion"] is True


@pytest.mark.asyncio
async def test_candidate_list_includes_artifact_metadata(client):
    """Candidate list includes imported_from_artifact and artifact_hash."""
    r = await client.post("/api/v1/rl/finrlx/import-research-artifact", json={
        "artifact": _sample_artifact(),
        "import_acknowledgement": True,
        "source": "list_test",
    })
    cid = r.json()["data"]["policy_candidate_id"]

    r2 = await client.get("/api/v1/rl/finrlx/candidates")
    imported = next(c for c in r2.json()["data"] if c["id"] == cid)
    assert imported["imported_from_artifact"] is True
    assert imported["artifact_hash"] is not None


# ── Safety regressions ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_broker_execution(client):
    r = await client.post("/api/v1/rl/execute", json={})
    assert r.status_code in (404, 405, 422)


@pytest.mark.asyncio
async def test_recommendations_unaffected(client):
    r = await client.get("/api/v1/recommendations/current")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_overview_unaffected(client):
    r = await client.get("/api/v1/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_publication_unaffected(client):
    r = await client.get("/api/v1/publication/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_existing_benchmark_still_works(client):
    r = await client.post("/api/v1/rl/benchmarks/run", json={
        "start_date": "2026-03-15", "end_date": "2026-04-15",
    })
    assert r.json()["data"]["status"] in ("completed", "partial")


@pytest.mark.asyncio
async def test_phase8a_8b_8c_endpoints_still_work(client):
    r = await client.get("/api/v1/rl/finrlx/status")
    assert r.status_code == 200
    r2 = await client.post("/api/v1/rl/finrlx/validate-dataset", json={"limit": 3})
    assert r2.status_code == 200
    r3 = await client.post("/api/v1/rl/finrlx/train-research", json={
        "research_acknowledgement": True,
    })
    assert r3.json()["data"]["training_status"] == "completed"
    r4 = await client.post("/api/v1/rl/finrlx/train-cpu-prototype", json={
        "algorithm": "PPO", "research_acknowledgement": True,
    })
    assert r4.status_code == 200
