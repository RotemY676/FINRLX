"""RL environment endpoints.

GET  /api/v1/rl/status
GET  /api/v1/rl/environments
GET  /api/v1/rl/environments/{key}
POST /api/v1/rl/environments/{key}/validate
POST /api/v1/rl/simulations/run
GET  /api/v1/rl/runs
GET  /api/v1/rl/runs/{run_id}
GET  /api/v1/rl/runs/{run_id}/episodes
GET  /api/v1/rl/episodes/{episode_id}/steps
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.rl_environment import RLEnvironmentService

router = APIRouter()


class RLSimulationRequest(BaseModel):
    environment_key: str = "quantpipeline_offline_v1"
    start_date: str | None = None
    end_date: str | None = None
    agent_type: str = "heuristic_baseline"


def _env_dict(e) -> dict:
    return {
        "id": e.id, "key": e.key, "name": e.name, "description": e.description,
        "universe_id": e.universe_id,
        "state_schema": e.state_schema, "action_schema": e.action_schema,
        "reward_schema": e.reward_schema, "constraint_schema": e.constraint_schema,
        "status": e.status, "is_shadow_only": e.is_shadow_only,
    }


def _run_dict(r) -> dict:
    return {
        "id": r.id, "environment_key": r.environment_key,
        "run_type": r.run_type, "agent_type": r.agent_type,
        "status": r.status,
        "start_date": r.start_date.isoformat() if r.start_date else None,
        "end_date": r.end_date.isoformat() if r.end_date else None,
        "universe_id": r.universe_id,
        "metrics": r.metrics, "warnings": r.warnings,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }


def _episode_dict(ep) -> dict:
    return {
        "id": ep.id, "environment_run_id": ep.environment_run_id,
        "episode_index": ep.episode_index,
        "start_date": ep.start_date.isoformat() if ep.start_date else None,
        "end_date": ep.end_date.isoformat() if ep.end_date else None,
        "status": ep.status, "initial_value": ep.initial_value,
        "final_value": ep.final_value, "total_reward": ep.total_reward,
        "total_return": ep.total_return, "max_drawdown": ep.max_drawdown,
        "turnover": ep.turnover, "step_count": ep.step_count,
        "warnings": ep.warnings,
    }


def _step_dict(s) -> dict:
    return {
        "id": s.id, "episode_id": s.episode_id, "step_index": s.step_index,
        "as_of_date": s.as_of_date.isoformat() if s.as_of_date else None,
        "state": s.state, "action": s.action, "reward": s.reward,
        "portfolio_value": s.portfolio_value, "cash_weight": s.cash_weight,
        "exposure": s.exposure, "constraint_violations": s.constraint_violations,
    }


@router.get("/rl/status", response_model=ApiResponse[dict])
async def get_rl_status(db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    await svc.ensure_default_rl_environment()
    return ApiResponse(meta=make_meta(), data=await svc.get_status())


@router.get("/rl/environments", response_model=ApiResponse[list[dict]])
async def list_environments(db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    await svc.ensure_default_rl_environment()
    envs = await svc.get_environment_definitions()
    return ApiResponse(meta=make_meta(), data=[_env_dict(e) for e in envs])


@router.get("/rl/environments/{key}", response_model=ApiResponse[dict])
async def get_environment(key: str, db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    env = await svc.get_environment_definition(key)
    if not env:
        raise HTTPException(status_code=404, detail="RL environment not found")
    return ApiResponse(meta=make_meta(), data=_env_dict(env))


@router.post("/rl/environments/{key}/validate", response_model=ApiResponse[dict])
async def validate_environment(key: str, db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    return ApiResponse(meta=make_meta(), data=await svc.validate_environment(key))


@router.post("/rl/simulations/run", response_model=ApiResponse[dict])
async def run_simulation(body: RLSimulationRequest, db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    start = date.fromisoformat(body.start_date) if body.start_date else None
    end = date.fromisoformat(body.end_date) if body.end_date else None
    run = await svc.run_offline_simulation(body.environment_key, start, end, body.agent_type)
    return ApiResponse(meta=make_meta(warnings=run.warnings), data=_run_dict(run))


@router.get("/rl/runs", response_model=ApiResponse[list[dict]])
async def list_runs(db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    runs = await svc.get_runs()
    return ApiResponse(meta=make_meta(), data=[_run_dict(r) for r in runs])


@router.get("/rl/runs/{run_id}", response_model=ApiResponse[dict])
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    run = await svc.get_run_detail(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="RL run not found")
    return ApiResponse(meta=make_meta(), data=_run_dict(run))


@router.get("/rl/runs/{run_id}/episodes", response_model=ApiResponse[list[dict]])
async def get_run_episodes(run_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    episodes = await svc.get_episodes(run_id)
    return ApiResponse(meta=make_meta(), data=[_episode_dict(ep) for ep in episodes])


@router.get("/rl/episodes/{episode_id}/steps", response_model=ApiResponse[list[dict]])
async def get_episode_steps(episode_id: str, db: AsyncSession = Depends(get_db)):
    svc = RLEnvironmentService(db)
    steps = await svc.get_steps(episode_id)
    return ApiResponse(meta=make_meta(), data=[_step_dict(s) for s in steps])
