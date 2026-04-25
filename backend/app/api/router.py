"""Central API router. All v1 routes are registered here."""
from fastapi import APIRouter

from app.api.v1.overview import router as overview_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.decision import router as decision_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.replay import router as replay_router
from app.api.v1.backtests import router as backtests_router
from app.api.v1.paper import router as paper_router
from app.api.v1.engines import router as engines_router
from app.api.v1.regime import router as regime_router
from app.api.v1.ops import router as ops_router
from app.api.v1.scenario import router as scenario_router
from app.api.v1.actions import router as actions_router
from app.api.v1.pricechart import router as pricechart_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.features import router as features_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.publication import router as publication_router
from app.api.v1.models import router as models_router
from app.api.v1.model_validation import router as model_validation_router
from app.api.v1.model_promotion import router as model_promotion_router
from app.api.v1.ml_ops import router as ml_ops_router
from app.api.v1.policies import router as policies_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.universe import router as universe_router
from app.api.v1.rl import router as rl_router
from app.api.v1.rl_training import router as rl_training_router
from app.api.v1.rl_benchmark import router as rl_benchmark_router
from app.api.v1.rl_finrlx import router as rl_finrlx_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(overview_router, tags=["overview"])
api_router.include_router(recommendations_router, tags=["recommendations"])
api_router.include_router(decision_router, tags=["decision"])
api_router.include_router(comparison_router, tags=["comparison"])
api_router.include_router(replay_router, tags=["replay"])
api_router.include_router(backtests_router, tags=["backtests"])
api_router.include_router(paper_router, tags=["paper"])
api_router.include_router(engines_router, tags=["engines"])
api_router.include_router(regime_router, tags=["regime"])
api_router.include_router(ops_router, tags=["ops"])
api_router.include_router(scenario_router, tags=["scenario"])
api_router.include_router(actions_router, tags=["actions"])
api_router.include_router(pricechart_router, tags=["pricechart"])
api_router.include_router(ingest_router, tags=["ingestion"])
api_router.include_router(features_router, tags=["features"])
api_router.include_router(pipeline_router, tags=["pipeline"])
api_router.include_router(publication_router, tags=["publication"])
api_router.include_router(models_router, tags=["models"])
api_router.include_router(model_validation_router, tags=["model-validation"])
api_router.include_router(model_promotion_router, tags=["model-promotion"])
api_router.include_router(ml_ops_router, tags=["ml-ops"])
api_router.include_router(policies_router, tags=["policies"])
api_router.include_router(integrations_router, tags=["integrations"])
api_router.include_router(universe_router, tags=["universes"])
api_router.include_router(rl_router, tags=["rl"])
api_router.include_router(rl_training_router, tags=["rl-training"])
api_router.include_router(rl_benchmark_router, tags=["rl-benchmark"])
api_router.include_router(rl_finrlx_router, tags=["rl-finrlx"])
api_router.include_router(health_router, tags=["health"])
