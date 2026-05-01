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
POST /api/v1/rl/finrlx/research-experiments
GET  /api/v1/rl/finrlx/research-experiments
GET  /api/v1/rl/finrlx/research-experiments/{experiment_id}
POST /api/v1/rl/finrlx/research-experiments/{experiment_id}/state
POST /api/v1/rl/finrlx/research-experiments/{experiment_id}/results
GET  /api/v1/rl/finrlx/research-experiments/{experiment_id}/verify
POST /api/v1/rl/finrlx/research-experiments/rebuild-registry
POST /api/v1/rl/finrlx/experiment-comparisons
GET  /api/v1/rl/finrlx/experiment-comparisons
GET  /api/v1/rl/finrlx/experiment-comparisons/{comparison_id}
POST /api/v1/rl/finrlx/experiment-comparisons/{comparison_id}/archive
GET  /api/v1/rl/finrlx/experiment-comparisons/{comparison_id}/verify
POST /api/v1/rl/finrlx/experiment-comparisons/rebuild-registry
POST /api/v1/rl/finrlx/research-readiness
GET  /api/v1/rl/finrlx/research-readiness
GET  /api/v1/rl/finrlx/research-readiness/{readiness_id}
POST /api/v1/rl/finrlx/research-readiness/{readiness_id}/state
POST /api/v1/rl/finrlx/research-readiness/{readiness_id}/archive
GET  /api/v1/rl/finrlx/research-readiness/{readiness_id}/verify
POST /api/v1/rl/finrlx/research-readiness/rebuild-registry

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


def _handle_corrupt_registry(exc: FinRLXResearchService.RegistryCorruptError):
    raise HTTPException(status_code=409, detail=str(exc))


@router.get("/rl/finrlx/dataset-exports", response_model=ApiResponse[list[dict]])
async def list_dataset_exports(
    lifecycle_state: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = FinRLXResearchService(db)
    try:
        data = svc.list_dataset_exports(lifecycle_state=lifecycle_state, limit=limit)
    except FinRLXResearchService.RegistryCorruptError as exc:
        _handle_corrupt_registry(exc)
    return ApiResponse(meta=make_meta(), data=data)


@router.get("/rl/finrlx/dataset-exports/{export_id}", response_model=ApiResponse[dict])
async def get_dataset_export(export_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.get_dataset_export(export_id)
    except FinRLXResearchService.RegistryCorruptError as exc:
        _handle_corrupt_registry(exc)
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
    try:
        result = svc.mark_dataset_export_stale(export_id, reason=body.reason)
    except FinRLXResearchService.RegistryCorruptError as exc:
        _handle_corrupt_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Dataset export not found in registry.")
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/dataset-exports/{export_id}/verify", response_model=ApiResponse[dict])
async def verify_dataset_export(export_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.verify_dataset_export_artifact(export_id)
    except FinRLXResearchService.RegistryCorruptError as exc:
        _handle_corrupt_registry(exc)
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


# ── Local Research Experiment Tracking (Phase 8J.1) ────────────────

class FinRLXCreateExperimentRequest(BaseModel):
    name: str
    linked_export_id: str
    hypothesis: str = ""
    method_notes: str = ""
    parameters: dict = {}
    expected_metrics: list = []
    research_acknowledgement: bool = False


class FinRLXExperimentStateRequest(BaseModel):
    lifecycle_state: str
    acknowledgement: bool = False
    reason: str | None = None


class FinRLXExperimentResultsRequest(BaseModel):
    acknowledgement: bool = False
    result_summary: str = ""
    result_metrics: dict = {}
    warnings: list = []
    limitations: list = []


def _handle_corrupt_experiment_registry(exc: FinRLXResearchService.ExperimentRegistryCorruptError):
    raise HTTPException(status_code=409, detail=str(exc))


@router.post("/rl/finrlx/research-experiments", response_model=ApiResponse[dict])
async def create_research_experiment(
    body: FinRLXCreateExperimentRequest, db: AsyncSession = Depends(get_db),
):
    if not body.research_acknowledgement:
        raise HTTPException(
            status_code=422,
            detail="Research acknowledgement required. Set research_acknowledgement=true "
                   "to confirm this is a research-only offline experiment.",
        )
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=422, detail="Experiment name must not be empty.")
    if not body.linked_export_id or not body.linked_export_id.strip():
        raise HTTPException(status_code=422, detail="linked_export_id is required.")

    svc = FinRLXResearchService(db)
    try:
        result = svc.create_research_experiment(
            name=body.name.strip(),
            linked_export_id=body.linked_export_id.strip(),
            hypothesis=body.hypothesis,
            method_notes=body.method_notes,
            parameters=body.parameters,
            expected_metrics=body.expected_metrics,
        )
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        _handle_corrupt_experiment_registry(exc)

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.get("/rl/finrlx/research-experiments", response_model=ApiResponse[list[dict]])
async def list_research_experiments(
    lifecycle_state: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = FinRLXResearchService(db)
    try:
        data = svc.list_research_experiments(lifecycle_state=lifecycle_state, limit=limit)
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        _handle_corrupt_experiment_registry(exc)
    return ApiResponse(meta=make_meta(), data=data)


@router.get("/rl/finrlx/research-experiments/{experiment_id}", response_model=ApiResponse[dict])
async def get_research_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.get_research_experiment(experiment_id)
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        _handle_corrupt_experiment_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Research experiment not found.")
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/research-experiments/{experiment_id}/state", response_model=ApiResponse[dict])
async def update_research_experiment_state(
    experiment_id: str, body: FinRLXExperimentStateRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to change experiment state.")
    svc = FinRLXResearchService(db)
    try:
        result = svc.update_research_experiment_state(experiment_id, body.lifecycle_state, reason=body.reason)
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        _handle_corrupt_experiment_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Research experiment not found.")
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/research-experiments/{experiment_id}/results", response_model=ApiResponse[dict])
async def import_research_experiment_results(
    experiment_id: str, body: FinRLXExperimentResultsRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(
            status_code=422,
            detail="Acknowledgement required. Set acknowledgement=true to confirm "
                   "this is a metadata-only offline result import.",
        )
    svc = FinRLXResearchService(db)
    try:
        result = svc.import_research_experiment_results(
            experiment_id=experiment_id,
            result_summary=body.result_summary,
            result_metrics=body.result_metrics,
            warnings=body.warnings,
            limitations=body.limitations,
        )
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        _handle_corrupt_experiment_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Research experiment not found.")
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/research-experiments/{experiment_id}/verify", response_model=ApiResponse[dict])
async def verify_research_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.verify_research_experiment(experiment_id)
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        _handle_corrupt_experiment_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Research experiment not found.")
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


class FinRLXRebuildExperimentRegistryRequest(BaseModel):
    acknowledgement: bool = False


@router.post("/rl/finrlx/research-experiments/rebuild-registry", response_model=ApiResponse[dict])
async def rebuild_experiment_registry(
    body: FinRLXRebuildExperimentRegistryRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to rebuild experiment registry.")
    svc = FinRLXResearchService(db)
    result = svc.rebuild_experiment_registry_from_files()
    return ApiResponse(meta=make_meta(), data=result)


# ── Offline Experiment Comparison Workbench (Phase 8K.1) ───────────

class FinRLXCreateComparisonRequest(BaseModel):
    name: str
    experiment_ids: list[str]
    metric_priority: list[str] = []
    notes: str = ""
    research_acknowledgement: bool = False


class FinRLXArchiveComparisonRequest(BaseModel):
    acknowledgement: bool = False
    reason: str | None = None


class FinRLXRebuildComparisonRegistryRequest(BaseModel):
    acknowledgement: bool = False


def _handle_corrupt_comparison_registry(exc: FinRLXResearchService.ComparisonRegistryCorruptError):
    raise HTTPException(status_code=409, detail=str(exc))


@router.post("/rl/finrlx/experiment-comparisons", response_model=ApiResponse[dict])
async def create_experiment_comparison(
    body: FinRLXCreateComparisonRequest, db: AsyncSession = Depends(get_db),
):
    if not body.research_acknowledgement:
        raise HTTPException(
            status_code=422,
            detail="Research acknowledgement required. Set research_acknowledgement=true "
                   "to confirm this is a research-only offline comparison.",
        )
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=422, detail="Comparison name must not be empty.")
    unique_ids = list(dict.fromkeys(body.experiment_ids))
    if len(unique_ids) < 2:
        raise HTTPException(status_code=422, detail="At least 2 unique experiment IDs are required.")

    svc = FinRLXResearchService(db)
    try:
        result = svc.create_experiment_comparison(
            name=body.name.strip(),
            experiment_ids=unique_ids,
            metric_priority=body.metric_priority,
            notes=body.notes,
        )
    except FinRLXResearchService.ComparisonRegistryCorruptError as exc:
        _handle_corrupt_comparison_registry(exc)
    except FinRLXResearchService.ExperimentRegistryCorruptError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.get("/rl/finrlx/experiment-comparisons", response_model=ApiResponse[list[dict]])
async def list_experiment_comparisons(
    lifecycle_state: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = FinRLXResearchService(db)
    try:
        data = svc.list_experiment_comparisons(lifecycle_state=lifecycle_state, limit=limit)
    except FinRLXResearchService.ComparisonRegistryCorruptError as exc:
        _handle_corrupt_comparison_registry(exc)
    return ApiResponse(meta=make_meta(), data=data)


@router.get("/rl/finrlx/experiment-comparisons/{comparison_id}", response_model=ApiResponse[dict])
async def get_experiment_comparison(comparison_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.get_experiment_comparison(comparison_id)
    except FinRLXResearchService.ComparisonRegistryCorruptError as exc:
        _handle_corrupt_comparison_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Experiment comparison not found.")
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/experiment-comparisons/{comparison_id}/archive", response_model=ApiResponse[dict])
async def archive_experiment_comparison(
    comparison_id: str, body: FinRLXArchiveComparisonRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to archive comparison.")
    svc = FinRLXResearchService(db)
    try:
        result = svc.archive_experiment_comparison(comparison_id, reason=body.reason)
    except FinRLXResearchService.ComparisonRegistryCorruptError as exc:
        _handle_corrupt_comparison_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Experiment comparison not found.")
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/experiment-comparisons/{comparison_id}/verify", response_model=ApiResponse[dict])
async def verify_experiment_comparison(comparison_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.verify_experiment_comparison(comparison_id)
    except FinRLXResearchService.ComparisonRegistryCorruptError as exc:
        _handle_corrupt_comparison_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Experiment comparison not found.")
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.post("/rl/finrlx/experiment-comparisons/rebuild-registry", response_model=ApiResponse[dict])
async def rebuild_comparison_registry(
    body: FinRLXRebuildComparisonRegistryRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to rebuild comparison registry.")
    svc = FinRLXResearchService(db)
    result = svc.rebuild_comparison_registry_from_files()
    return ApiResponse(meta=make_meta(), data=result)


# ── Research Readiness Review Gates (Phase 8L.1) ──────────────────

class FinRLXCreateReadinessRequest(BaseModel):
    name: str
    linked_comparison_id: str
    operator_notes: str = ""
    checklist: dict = {}
    research_acknowledgement: bool = False


class FinRLXReadinessStateRequest(BaseModel):
    readiness_state: str
    acknowledgement: bool = False
    reason: str | None = None


class FinRLXArchiveReadinessRequest(BaseModel):
    acknowledgement: bool = False
    reason: str | None = None


class FinRLXRebuildReadinessRegistryRequest(BaseModel):
    acknowledgement: bool = False


def _handle_corrupt_readiness_registry(exc: FinRLXResearchService.ReadinessRegistryCorruptError):
    raise HTTPException(status_code=409, detail=str(exc))


@router.post("/rl/finrlx/research-readiness", response_model=ApiResponse[dict])
async def create_research_readiness(
    body: FinRLXCreateReadinessRequest, db: AsyncSession = Depends(get_db),
):
    if not body.research_acknowledgement:
        raise HTTPException(status_code=422, detail="Research acknowledgement required.")
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=422, detail="Readiness review name must not be empty.")
    if not body.linked_comparison_id or not body.linked_comparison_id.strip():
        raise HTTPException(status_code=422, detail="linked_comparison_id is required.")

    svc = FinRLXResearchService(db)
    try:
        result = svc.create_research_readiness_review(
            name=body.name.strip(),
            linked_comparison_id=body.linked_comparison_id.strip(),
            operator_notes=body.operator_notes,
            checklist=body.checklist,
        )
    except FinRLXResearchService.ReadinessRegistryCorruptError as exc:
        _handle_corrupt_readiness_registry(exc)
    except FinRLXResearchService.ComparisonRegistryCorruptError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.get("/rl/finrlx/research-readiness", response_model=ApiResponse[list[dict]])
async def list_research_readiness(
    readiness_state: str | None = None, limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    svc = FinRLXResearchService(db)
    try:
        data = svc.list_research_readiness_reviews(readiness_state=readiness_state, limit=limit)
    except FinRLXResearchService.ReadinessRegistryCorruptError as exc:
        _handle_corrupt_readiness_registry(exc)
    return ApiResponse(meta=make_meta(), data=data)


@router.get("/rl/finrlx/research-readiness/{readiness_id}", response_model=ApiResponse[dict])
async def get_research_readiness(readiness_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.get_research_readiness_review(readiness_id)
    except FinRLXResearchService.ReadinessRegistryCorruptError as exc:
        _handle_corrupt_readiness_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Readiness review not found.")
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/research-readiness/{readiness_id}/state", response_model=ApiResponse[dict])
async def update_research_readiness_state(
    readiness_id: str, body: FinRLXReadinessStateRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required.")
    svc = FinRLXResearchService(db)
    try:
        result = svc.update_research_readiness_review_state(readiness_id, body.readiness_state, reason=body.reason)
    except FinRLXResearchService.ReadinessRegistryCorruptError as exc:
        _handle_corrupt_readiness_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Readiness review not found.")
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])
    return ApiResponse(meta=make_meta(), data=result)


@router.post("/rl/finrlx/research-readiness/{readiness_id}/archive", response_model=ApiResponse[dict])
async def archive_research_readiness(
    readiness_id: str, body: FinRLXArchiveReadinessRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required.")
    svc = FinRLXResearchService(db)
    try:
        result = svc.archive_research_readiness_review(readiness_id, reason=body.reason)
    except FinRLXResearchService.ReadinessRegistryCorruptError as exc:
        _handle_corrupt_readiness_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Readiness review not found.")
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/research-readiness/{readiness_id}/verify", response_model=ApiResponse[dict])
async def verify_research_readiness(readiness_id: str, db: AsyncSession = Depends(get_db)):
    svc = FinRLXResearchService(db)
    try:
        result = svc.verify_research_readiness_review(readiness_id)
    except FinRLXResearchService.ReadinessRegistryCorruptError as exc:
        _handle_corrupt_readiness_registry(exc)
    if not result:
        raise HTTPException(status_code=404, detail="Readiness review not found.")
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)


@router.post("/rl/finrlx/research-readiness/rebuild-registry", response_model=ApiResponse[dict])
async def rebuild_readiness_registry(
    body: FinRLXRebuildReadinessRegistryRequest, db: AsyncSession = Depends(get_db),
):
    if not body.acknowledgement:
        raise HTTPException(status_code=422, detail="Acknowledgement required to rebuild readiness registry.")
    svc = FinRLXResearchService(db)
    result = svc.rebuild_readiness_registry_from_files()
    return ApiResponse(meta=make_meta(), data=result)


@router.get("/rl/finrlx/persistence/status", response_model=ApiResponse)
async def get_persistence_status(db: AsyncSession = Depends(get_db)):
    """Research storage persistence and deployment status (read-only)."""
    result = FinRLXResearchService.get_persistence_status()
    return ApiResponse(meta=make_meta(warnings=result.get("warnings")), data=result)
