"""FinRL-X research spike endpoints.

GET  /api/v1/rl/finrlx/status
POST /api/v1/rl/finrlx/validate-dataset
POST /api/v1/rl/finrlx/train-research
GET  /api/v1/rl/finrlx/candidates
GET  /api/v1/rl/finrlx/candidates/{candidate_id}

All endpoints are research-only, offline-only, shadow-only.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import make_meta
from app.schemas.common import ApiResponse
from app.services.finrlx_research import FinRLXResearchService

router = APIRouter()


class FinRLXValidateRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    limit: int = 10


class FinRLXTrainRequest(BaseModel):
    name: str = "FinRL-X Research Candidate"
    start_date: str | None = None
    end_date: str | None = None
    research_acknowledgement: bool = False


@router.get("/rl/finrlx/status", response_model=ApiResponse[dict])
async def get_finrlx_status(db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    return ApiResponse(meta=make_meta(), data=svc.get_adapter_info())


@router.post("/rl/finrlx/validate-dataset", response_model=ApiResponse[dict])
async def validate_dataset(body: FinRLXValidateRequest, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    sd = date.fromisoformat(body.start_date) if body.start_date else None
    ed = date.fromisoformat(body.end_date) if body.end_date else None
    result = await svc.validate_dataset_contract(sd, ed, body.limit)
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/train-research", response_model=ApiResponse[dict])
async def train_research(body: FinRLXTrainRequest, db: AsyncSession = Depends(get_db)):
    if not body.research_acknowledgement:
        raise HTTPException(
            status_code=422,
            detail="Research acknowledgement required. Set research_acknowledgement=true "
                   "to confirm this is a research-only offline training stub.",
        )
    svc = FinRLXResearchService(db)
    sd = date.fromisoformat(body.start_date) if body.start_date else None
    ed = date.fromisoformat(body.end_date) if body.end_date else None
    result = await svc.train_research_stub(body.name, sd, ed)
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.get("/rl/finrlx/candidates", response_model=ApiResponse[list[dict]])
async def list_candidates(db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_candidates())


@router.get("/rl/finrlx/candidates/{candidate_id}", response_model=ApiResponse[dict])
async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    result = await svc.get_candidate(candidate_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research candidate not found")
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/candidates/{candidate_id}/isolation", response_model=ApiResponse[dict])
async def get_candidate_isolation(candidate_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    candidate = await svc.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Research candidate not found")
    return ApiResponse(meta=make_meta(), data=svc.get_candidate_isolation(candidate_id))
