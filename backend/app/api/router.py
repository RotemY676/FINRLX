"""Central API router. All v1 routes are registered here."""
from fastapi import APIRouter

from app.api.v1.actions import router as actions_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.auth import router as auth_router
from app.api.v1.backtests import router as backtests_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.decision import router as decision_router
from app.api.v1.engines import router as engines_router
from app.api.v1.features import router as features_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.flags import router as flags_router
from app.api.v1.health import router as health_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.ml_ops import router as ml_ops_router
from app.api.v1.model_promotion import router as model_promotion_router
from app.api.v1.model_validation import router as model_validation_router
from app.api.v1.models import router as models_router
from app.api.v1.news import router as news_router
from app.api.v1.operator import router as operator_router
from app.api.v1.ops import router as ops_router
from app.api.v1.ops_jobs import router as ops_jobs_router
from app.api.v1.ops_users import router as ops_users_router
from app.api.v1.overview import router as overview_router
from app.api.v1.paper import router as paper_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.policies import router as policies_router
from app.api.v1.pricechart import router as pricechart_router
from app.api.v1.profile import router as profile_router
from app.api.v1.publication import router as publication_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.regime import router as regime_router
from app.api.v1.replay import router as replay_router
from app.api.v1.risk import router as risk_router
from app.api.v1.rl import router as rl_router
from app.api.v1.rl_benchmark import router as rl_benchmark_router
from app.api.v1.rl_finrlx import router as rl_finrlx_router
from app.api.v1.rl_training import router as rl_training_router
from app.api.v1.saved_views import router as saved_views_router
from app.api.v1.scenario import router as scenario_router
from app.api.v1.templates import router as templates_router
from app.api.v1.universe import router as universe_router

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
api_router.include_router(ops_jobs_router, tags=["ops-jobs"])
api_router.include_router(ops_users_router, tags=["ops-users"])
api_router.include_router(feedback_router, tags=["feedback"])
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
api_router.include_router(profile_router, tags=["profile"])
api_router.include_router(integrations_router, tags=["integrations"])
api_router.include_router(universe_router, tags=["universes"])
api_router.include_router(risk_router, tags=["risk"])
api_router.include_router(news_router, tags=["news"])
api_router.include_router(operator_router, tags=["operator"])
api_router.include_router(assistant_router, tags=["assistant"])
api_router.include_router(saved_views_router, tags=["saved-views"])
api_router.include_router(templates_router, tags=["templates"])
api_router.include_router(rl_router, tags=["rl"])
api_router.include_router(rl_training_router, tags=["rl-training"])
api_router.include_router(rl_benchmark_router, tags=["rl-benchmark"])
api_router.include_router(rl_finrlx_router, tags=["rl-finrlx"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(flags_router, tags=["flags"])
