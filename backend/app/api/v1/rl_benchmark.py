"""RL offline benchmarking endpoints.

POST /api/v1/rl/benchmarks/run
GET  /api/v1/rl/benchmarks
GET  /api/v1/rl/benchmarks/{benchmark_report_id}
POST /api/v1/rl/benchmarks/compare-policy
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import make_meta
from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.services.rl_benchmark import RLBenchmarkService

router = APIRouter()


class RLBenchmarkRunRequest(BaseModel):
    name: str = "Offline Agent Comparison"
    environment_key: str = "quantpipeline_offline_v1"
    start_date: str | None = None
    end_date: str | None = None
    agent_keys: list[str] | None = None
    policy_snapshot_ids: list[str] | None = None


class RLComparePolicyRequest(BaseModel):
    policy_snapshot_id: str
    environment_key: str = "quantpipeline_offline_v1"
    start_date: str | None = None
    end_date: str | None = None


def _report_dict(r) -> dict:
    return {
        "id": r.id, "name": r.name, "environment_key": r.environment_key,
        "universe_id": r.universe_id, "status": r.status,
        "start_date": r.start_date.isoformat() if r.start_date else None,
        "end_date": r.end_date.isoformat() if r.end_date else None,
        "compared_agents": r.compared_agents,
        "requested_agents": (r.dataset_lineage or {}).get("requested_agents", r.compared_agents),
        "executed_agents": (r.dataset_lineage or {}).get("executed_agents", r.compared_agents),
        "skipped_agents": (r.dataset_lineage or {}).get("skipped_agents", []),
        "is_complete_comparison": (r.dataset_lineage or {}).get("is_complete_comparison", True),
        "metrics_by_agent": r.metrics_by_agent,
        "reward_breakdown_by_agent": r.reward_breakdown_by_agent,
        "violations_by_agent": r.violations_by_agent,
        "forensic_summary": r.forensic_summary,
        "forensic_summary_by_agent": (r.dataset_lineage or {}).get("forensic_summary_by_agent"),
        "result_fingerprint": (r.dataset_lineage or {}).get("result_fingerprint"),
        "invariant_check_results": (r.dataset_lineage or {}).get("invariant_check_results"),
        "simulation_run_ids": r.simulation_run_ids,
        "policy_snapshot_ids": r.policy_snapshot_ids,
        "dataset_lineage": r.dataset_lineage,
        "safety_flags": r.safety_flags,
        "warnings": r.warnings,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }


@router.post("/rl/benchmarks/run", response_model=ApiResponse[dict])
async def run_benchmark(body: RLBenchmarkRunRequest, db: AsyncSession = Depends(get_db)):
    svc = RLBenchmarkService(db)
    sd = date.fromisoformat(body.start_date) if body.start_date else None
    ed = date.fromisoformat(body.end_date) if body.end_date else None
    report = await svc.run_benchmark(
        body.name, body.environment_key, sd, ed, body.agent_keys, body.policy_snapshot_ids,
    )
    return ApiResponse(meta=make_meta(warnings=report.warnings), data=_report_dict(report))


@router.get("/rl/benchmarks", response_model=ApiResponse[list[dict]])
async def list_benchmarks(db: AsyncSession = Depends(get_db)):
    svc = RLBenchmarkService(db)
    reports = await svc.get_benchmarks()
    return ApiResponse(meta=make_meta(), data=[_report_dict(r) for r in reports])


@router.get("/rl/benchmarks/audit", response_model=ApiResponse[list[dict]])
async def list_audit_events(db: AsyncSession = Depends(get_db)):
    svc = RLBenchmarkService(db)
    events = await svc.get_audit_events()
    return ApiResponse(meta=make_meta(), data=[_audit_dict(e) for e in events])


@router.get("/rl/benchmarks/{benchmark_report_id}", response_model=ApiResponse[dict])
async def get_benchmark(benchmark_report_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLBenchmarkService(db)
    report = await svc.get_benchmark(benchmark_report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Benchmark report not found")
    return ApiResponse(meta=make_meta(), data=_report_dict(report))


@router.post("/rl/benchmarks/compare-policy", response_model=ApiResponse[dict])
async def compare_policy(body: RLComparePolicyRequest, db: AsyncSession = Depends(get_db)):
    svc = RLBenchmarkService(db)
    sd = date.fromisoformat(body.start_date) if body.start_date else None
    ed = date.fromisoformat(body.end_date) if body.end_date else None
    report = await svc.compare_policy(body.policy_snapshot_id, body.environment_key, sd, ed)
    return ApiResponse(meta=make_meta(warnings=report.warnings), data=_report_dict(report))


def _audit_dict(e) -> dict:
    d = e.details or {}
    return {
        "id": e.id,
        "created_at": e.occurred_at.isoformat() if e.occurred_at else None,
        "event_type": d.get("event_type", e.action),
        "actor_type": d.get("actor_type", "system"),
        "source": d.get("source", "rl_benchmark"),
        "benchmark_report_id": e.object_id,
        "status": d.get("status"),
        "requested_agents": d.get("requested_agents"),
        "executed_agents": d.get("executed_agents"),
        "skipped_agents": d.get("skipped_agents"),
        "is_complete_comparison": d.get("is_complete_comparison"),
        "safety_flags": d.get("safety_flags"),
        "result_fingerprint": d.get("result_fingerprint"),
        "invariant_check_results": d.get("invariant_check_results"),
        "warnings": d.get("warnings"),
    }


@router.get("/rl/benchmarks/{benchmark_report_id}/audit", response_model=ApiResponse[list[dict]])
async def get_audit_for_report(benchmark_report_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLBenchmarkService(db)
    events = await svc.get_audit_for_report(benchmark_report_id)
    return ApiResponse(meta=make_meta(), data=[_audit_dict(e) for e in events])
