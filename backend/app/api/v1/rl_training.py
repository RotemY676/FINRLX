"""RL training harness endpoints.

GET  /api/v1/rl/agents
GET  /api/v1/rl/agents/{agent_key}
GET  /api/v1/rl/adapter/status
GET  /api/v1/rl/dataset/export
POST /api/v1/rl/train
GET  /api/v1/rl/training-runs
GET  /api/v1/rl/training-runs/{run_id}
GET  /api/v1/rl/policies
GET  /api/v1/rl/policies/{policy_snapshot_id}
POST /api/v1/rl/policies/{policy_snapshot_id}/evaluate
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.rl_training import RLTrainingService

router = APIRouter()


class RLTrainRequest(BaseModel):
    agent_key: str = "score_weighted_baseline"
    environment_key: str = "quantpipeline_offline_v1"
    train_start_date: str | None = None
    train_end_date: str | None = None


class RLEvaluateRequest(BaseModel):
    eval_start_date: str | None = None
    eval_end_date: str | None = None


def _agent_dict(a) -> dict:
    return {
        "id": a.id, "key": a.key, "name": a.name, "description": a.description,
        "agent_type": a.agent_type, "algorithm_family": a.algorithm_family,
        "status": a.status, "is_trainable": a.is_trainable,
        "is_shadow_only": a.is_shadow_only, "config_schema": a.config_schema,
    }


def _run_dict(r) -> dict:
    return {
        "id": r.id, "agent_key": r.agent_key, "environment_key": r.environment_key,
        "status": r.status,
        "train_start_date": r.train_start_date.isoformat() if r.train_start_date else None,
        "train_end_date": r.train_end_date.isoformat() if r.train_end_date else None,
        "config": r.config, "metrics": r.metrics, "warnings": r.warnings,
        "model_artifact_ref": r.model_artifact_ref,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }


def _snapshot_dict(s) -> dict:
    return {
        "id": s.id, "training_run_id": s.training_run_id,
        "agent_key": s.agent_key, "environment_key": s.environment_key,
        "policy_type": s.policy_type, "policy_payload": s.policy_payload,
        "metrics": s.metrics,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.get("/rl/agents", response_model=ApiResponse[list[dict]])
async def list_agents(db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    await svc.ensure_default_agent_definitions()
    agents = await svc.get_agent_definitions()
    return ApiResponse(meta=make_meta(), data=[_agent_dict(a) for a in agents])


@router.get("/rl/agents/{agent_key}", response_model=ApiResponse[dict])
async def get_agent(agent_key: str, db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    agent = await svc.get_agent_definition(agent_key)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(meta=make_meta(), data=_agent_dict(agent))


@router.get("/rl/adapter/status", response_model=ApiResponse[dict])
async def get_adapter_status(db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    await svc.ensure_default_agent_definitions()
    return ApiResponse(meta=make_meta(), data=await svc.get_adapter_status())


@router.get("/rl/dataset/export", response_model=ApiResponse[list[dict]])
async def export_dataset(
    environment_key: str = "quantpipeline_offline_v1",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db),
):
    svc = RLTrainingService(db)
    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None
    rows = await svc.export_training_dataset(environment_key, sd, ed, limit)
    return ApiResponse(meta=make_meta(), data=rows)


@router.post("/rl/train", response_model=ApiResponse[dict])
async def train_agent(body: RLTrainRequest, db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    sd = date.fromisoformat(body.train_start_date) if body.train_start_date else None
    ed = date.fromisoformat(body.train_end_date) if body.train_end_date else None
    run = await svc.train_agent(body.agent_key, body.environment_key, sd, ed)
    return ApiResponse(meta=make_meta(warnings=run.warnings), data=_run_dict(run))


@router.get("/rl/training-runs", response_model=ApiResponse[list[dict]])
async def list_training_runs(db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    runs = await svc.get_training_runs()
    return ApiResponse(meta=make_meta(), data=[_run_dict(r) for r in runs])


@router.get("/rl/training-runs/{run_id}", response_model=ApiResponse[dict])
async def get_training_run(run_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    run = await svc.get_training_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return ApiResponse(meta=make_meta(), data=_run_dict(run))


@router.get("/rl/policies", response_model=ApiResponse[list[dict]])
async def list_policies(
    agent_key: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    svc = RLTrainingService(db)
    snapshots = await svc.get_policy_snapshots(agent_key)
    return ApiResponse(meta=make_meta(), data=[_snapshot_dict(s) for s in snapshots])


@router.get("/rl/policies/{policy_snapshot_id}", response_model=ApiResponse[dict])
async def get_policy(policy_snapshot_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLTrainingService(db)
    snap = await svc.get_policy_snapshot(policy_snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail="Policy snapshot not found")
    return ApiResponse(meta=make_meta(), data=_snapshot_dict(snap))


@router.post("/rl/policies/{policy_snapshot_id}/evaluate", response_model=ApiResponse[dict])
async def evaluate_policy(
    policy_snapshot_id: str,
    body: RLEvaluateRequest = RLEvaluateRequest(),
    db: AsyncSession = Depends(get_db),
):
    svc = RLTrainingService(db)
    sd = date.fromisoformat(body.eval_start_date) if body.eval_start_date else None
    ed = date.fromisoformat(body.eval_end_date) if body.eval_end_date else None
    result = await svc.evaluate_policy(policy_snapshot_id, sd, ed)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApiResponse(meta=make_meta(), data=result)
