"""FinRL-X research spike endpoints.

GET  /api/v1/rl/finrlx/status
GET  /api/v1/rl/finrlx/dependencies
POST /api/v1/rl/finrlx/validate-dataset
POST /api/v1/rl/finrlx/train-research
POST /api/v1/rl/finrlx/train-cpu-prototype
POST /api/v1/rl/finrlx/validate-research-artifact
POST /api/v1/rl/finrlx/import-research-artifact
GET  /api/v1/rl/finrlx/candidates
GET  /api/v1/rl/finrlx/candidates/{candidate_id}
GET  /api/v1/rl/finrlx/candidates/{candidate_id}/isolation
GET  /api/v1/rl/finrlx/candidates/{candidate_id}/benchmark-eligibility
POST /api/v1/rl/finrlx/candidates/{candidate_id}/benchmark
GET  /api/v1/rl/finrlx/candidates/{candidate_id}/benchmarks
POST /api/v1/rl/finrlx/dataset-export
GET  /api/v1/rl/finrlx/dataset-exports
GET  /api/v1/rl/finrlx/dataset-exports/{export_id}
POST /api/v1/rl/finrlx/dataset-exports/{export_id}/mark-stale
GET  /api/v1/rl/finrlx/dataset-exports/{export_id}/verify
POST /api/v1/rl/finrlx/dataset-exports/rebuild-registry

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


def _parse_date(value: str | None, field_name: str) -> date | None:
    """Parse a date string safely, raising HTTP 422 on invalid format."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail=f"Invalid {field_name}. Expected YYYY-MM-DD.")


class FinRLXCPUPrototypeRequest(BaseModel):
    name: str = "CPU-only Research Prototype"
    algorithm: str = "PPO"
    start_date: str | None = None
    end_date: str | None = None
    timesteps: int = 50
    seed: int = 42
    research_acknowledgement: bool = False


class FinRLXCandidateBenchmarkRequest(BaseModel):
    name: str = "Imported Candidate Benchmark"
    start_date: str | None = None
    end_date: str | None = None
    include_baselines: bool = True
    research_acknowledgement: bool = False


class FinRLXValidateArtifactRequest(BaseModel):
    artifact: dict


class FinRLXImportArtifactRequest(BaseModel):
    artifact: dict
    import_acknowledgement: bool = False
    source: str = "unknown"
    notes: str | None = None


class FinRLXDatasetExportRequest(BaseModel):
    name: str = "Local Research Dataset Export"
    candidate_id: str | None = None
    benchmark_report_id: str | None = None
    start_date: str = ""
    end_date: str = ""
    include_features: bool = True
    include_targets: bool = True
    include_warnings: bool = True
    format: str = "jsonl"
    research_acknowledgement: bool = False


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


@router.get("/rl/finrlx/dependencies", response_model=ApiResponse[dict])
async def get_dependencies(db: AsyncSession = Depends(get_db)):
    return ApiResponse(meta=make_meta(), data=FinRLXResearchService.get_neural_dependency_status())


@router.post("/rl/finrlx/train-cpu-prototype", response_model=ApiResponse[dict])
async def train_cpu_prototype(body: FinRLXCPUPrototypeRequest, db: AsyncSession = Depends(get_db)):
    if not body.research_acknowledgement:
        raise HTTPException(status_code=422, detail="Research acknowledgement required.")
    if body.algorithm.upper() not in ("PPO", "A2C"):
        raise HTTPException(status_code=422, detail="Algorithm must be PPO or A2C.")
    if body.timesteps > 500:
        raise HTTPException(status_code=422, detail="Timesteps capped at 500 for research prototype.")
    svc = FinRLXResearchService(db)
    sd = _parse_date(body.start_date, "start_date")
    ed = _parse_date(body.end_date, "end_date")
    if sd and ed and sd > ed:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date.")
    try:
        result = await svc.train_cpu_prototype(body.name, body.algorithm.upper(), sd, ed, body.timesteps, body.seed)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.post("/rl/finrlx/validate-dataset", response_model=ApiResponse[dict])
async def validate_dataset(body: FinRLXValidateRequest, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    sd = _parse_date(body.start_date, "start_date")
    ed = _parse_date(body.end_date, "end_date")
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
    sd = _parse_date(body.start_date, "start_date")
    ed = _parse_date(body.end_date, "end_date")
    result = await svc.train_research_stub(body.name, sd, ed)
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.post("/rl/finrlx/validate-research-artifact", response_model=ApiResponse[dict])
async def validate_research_artifact(body: FinRLXValidateArtifactRequest, db: AsyncSession = Depends(get_db)):
    result = FinRLXResearchService.validate_research_artifact(body.artifact)
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.post("/rl/finrlx/import-research-artifact", response_model=ApiResponse[dict])
async def import_research_artifact(body: FinRLXImportArtifactRequest, db: AsyncSession = Depends(get_db)):
    if not body.import_acknowledgement:
        raise HTTPException(
            status_code=422,
            detail="Import acknowledgement required. Set import_acknowledgement=true "
                   "to confirm this artifact is research-only and not for production use.",
        )
    svc = FinRLXResearchService(db)
    result = await svc.import_research_artifact(body.artifact, body.source, body.notes)
    if result.get("status") == "rejected":
        raise HTTPException(status_code=422, detail=result.get("warnings", ["Artifact validation failed"]))
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


@router.get("/rl/finrlx/candidates/{candidate_id}/benchmark-eligibility", response_model=ApiResponse[dict])
async def get_benchmark_eligibility(candidate_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    result = await svc.check_benchmark_eligibility(candidate_id)
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/candidates/{candidate_id}/benchmark", response_model=ApiResponse[dict])
async def run_candidate_benchmark(
    candidate_id: str, body: FinRLXCandidateBenchmarkRequest, db: AsyncSession = Depends(get_db),
):
    if not body.research_acknowledgement:
        raise HTTPException(status_code=422, detail="Research acknowledgement required.")
    sd = _parse_date(body.start_date, "start_date")
    ed = _parse_date(body.end_date, "end_date")
    if sd and ed and sd > ed:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date.")
    svc = FinRLXResearchService(db)
    result = await svc.run_candidate_benchmark(candidate_id, body.name, sd, ed, body.include_baselines)
    if result.get("status") == "rejected":
        raise HTTPException(status_code=422, detail=result.get("reasons", ["Benchmark rejected"]))
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.get("/rl/finrlx/candidates/{candidate_id}/benchmarks", response_model=ApiResponse[list[dict]])
async def get_candidate_benchmarks(candidate_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    return ApiResponse(meta=make_meta(), data=await svc.get_candidate_benchmarks(candidate_id))


# ── Dataset Export for Local Research (Phase 8I) ─────────────────────

@router.post("/rl/finrlx/dataset-export", response_model=ApiResponse[dict])
async def create_dataset_export(body: FinRLXDatasetExportRequest, db: AsyncSession = Depends(get_db)):
    if not body.research_acknowledgement:
        raise HTTPException(
            status_code=422,
            detail="Research acknowledgement required. Set research_acknowledgement=true "
                   "to confirm this is a research-only offline dataset export.",
        )
    if body.format not in ("jsonl", "json"):
        raise HTTPException(status_code=422, detail="format must be 'jsonl' or 'json'.")
    sd = _parse_date(body.start_date, "start_date")
    ed = _parse_date(body.end_date, "end_date")
    if not sd or not ed:
        raise HTTPException(status_code=422, detail="start_date and end_date are required.")
    if sd > ed:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date.")

    svc = FinRLXResearchService(db)

    if body.candidate_id:
        candidate = await svc.get_candidate(body.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Research candidate not found.")

    result = await svc.export_local_research_dataset(
        name=body.name,
        candidate_id=body.candidate_id,
        benchmark_report_id=body.benchmark_report_id,
        start_date=sd,
        end_date=ed,
        include_features=body.include_features,
        include_targets=body.include_targets,
        include_warnings=body.include_warnings,
        export_format=body.format,
    )

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.get("/rl/finrlx/dataset-exports", response_model=ApiResponse[list[dict]])
async def list_dataset_exports(
    lifecycle_state: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = FinRLXResearchService(db)
    return ApiResponse(meta=make_meta(), data=svc.list_dataset_exports(lifecycle_state=lifecycle_state, limit=limit))


@router.get("/rl/finrlx/dataset-exports/{export_id}", response_model=ApiResponse[dict])
async def get_dataset_export(export_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    result = svc.get_dataset_export(export_id)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset export not found.")
    return ApiResponse(meta=make_meta(), data=result)


# ── Dataset Export Governance (Phase 8I.2) ───────────────────────────

class FinRLXMarkStaleRequest(BaseModel):
    acknowledgement: bool = False
    reason: str | None = None


class FinRLXRebuildRegistryRequest(BaseModel):
    acknowledgement: bool = False


@router.post("/rl/finrlx/dataset-exports/{export_id}/mark-stale", response_model=ApiResponse[dict])
async def mark_dataset_export_stale(
    export_id: str, body: FinRLXMarkStaleRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to mark export as stale.")
    svc = FinRLXResearchService(db)
    result = svc.mark_dataset_export_stale(export_id, reason=body.reason)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset export not found in registry.")
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/dataset-exports/{export_id}/verify", response_model=ApiResponse[dict])
async def verify_dataset_export(export_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    result = svc.verify_dataset_export_artifact(export_id)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset export not found in registry.")
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.post("/rl/finrlx/dataset-exports/rebuild-registry", response_model=ApiResponse[dict])
async def rebuild_dataset_export_registry(
    body: FinRLXRebuildRegistryRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to rebuild registry.")
    svc = FinRLXResearchService(db)
    result = svc.rebuild_dataset_export_registry_from_files()
    return ApiResponse(meta=make_meta(), data=result)
