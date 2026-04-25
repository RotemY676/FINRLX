"""ML Ops observability service.

Phase 6D: aggregates ML model health, validation, promotion, shadow status,
and warnings into a single ops-oriented summary.

Does NOT activate ML or change any model status.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.modeling import (
    ModelDefinition, ModelRun, ModelPrediction,
    ModelValidationReport, MLPromotionReview,
)


class MLOpsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_definition(self, model_key: str) -> ModelDefinition | None:
        return (await self.db.execute(
            select(ModelDefinition).where(ModelDefinition.key == model_key)
        )).scalar_one_or_none()

    async def _get_latest_predict_run(self, model_key: str) -> ModelRun | None:
        return (await self.db.execute(
            select(ModelRun)
            .where(ModelRun.model_key == model_key)
            .where(ModelRun.run_type == "predict")
            .where(ModelRun.status == "completed")
            .order_by(ModelRun.completed_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def _get_latest_validation(self, model_key: str) -> ModelValidationReport | None:
        return (await self.db.execute(
            select(ModelValidationReport)
            .where(ModelValidationReport.model_key == model_key)
            .order_by(ModelValidationReport.evaluated_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def _get_latest_promotion(self, model_key: str) -> MLPromotionReview | None:
        return (await self.db.execute(
            select(MLPromotionReview)
            .where(MLPromotionReview.model_key == model_key)
            .order_by(MLPromotionReview.reviewed_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def _get_prediction_count(self, run_id: str) -> int:
        return (await self.db.execute(
            select(func.count()).select_from(ModelPrediction)
            .where(ModelPrediction.model_run_id == run_id)
        )).scalar() or 0

    def _recommend_action(
        self,
        pred_run: ModelRun | None,
        val_report: ModelValidationReport | None,
        promo: MLPromotionReview | None,
    ) -> str:
        if not pred_run:
            return "run_predictions"
        if not val_report:
            return "run_validation"
        if val_report.promotion_readiness == "not_ready":
            return "investigate_model"
        if val_report.sample_count < 20:
            return "needs_more_data"
        if not promo:
            return "run_promotion_review"
        if promo.recommendation == "needs_more_data":
            return "needs_more_data"
        if promo.recommendation == "eligible_for_review":
            return "eligible_for_manual_review"
        if promo.recommendation in ("promising_shadow", "not_ready"):
            return "keep_shadow"
        if promo.recommendation == "reject":
            return "investigate_model"
        return "keep_shadow"

    async def get_model_health(self, model_key: str) -> dict:
        defn = await self._get_definition(model_key)
        pred_run = await self._get_latest_predict_run(model_key)
        pred_count = await self._get_prediction_count(pred_run.id) if pred_run else 0

        return {
            "model_key": model_key,
            "model_name": defn.name if defn else None,
            "status": defn.status if defn else "unknown",
            "is_shadow": defn.is_shadow if defn else True,
            "model_type": defn.model_type if defn else None,
            "latest_prediction_run_id": pred_run.id if pred_run else None,
            "latest_prediction_status": pred_run.status if pred_run else None,
            "prediction_count": pred_count,
        }

    async def get_shadow_status(self, model_key: str) -> dict:
        defn = await self._get_definition(model_key)
        promo = await self._get_latest_promotion(model_key)
        return {
            "model_key": model_key,
            "is_shadow": defn.is_shadow if defn else True,
            "still_shadow": True,
            "live_pipeline_influence": False,
            "promotion_review_recommendation": promo.recommendation if promo else None,
            "promotion_review_decision": promo.decision if promo else None,
        }

    async def get_validation_summary(self, model_key: str) -> dict:
        val = await self._get_latest_validation(model_key)
        return {
            "model_key": model_key,
            "latest_validation_report_id": val.id if val else None,
            "validation_status": val.status if val else None,
            "validation_sample_count": val.sample_count if val else None,
            "directional_accuracy": val.directional_accuracy if val else None,
            "calibration_error": val.calibration_error if val else None,
            "promotion_readiness": val.promotion_readiness if val else None,
            "warnings": val.warnings if val else None,
        }

    async def get_promotion_summary(self, model_key: str) -> dict:
        promo = await self._get_latest_promotion(model_key)
        if not promo:
            return {
                "model_key": model_key,
                "latest_promotion_review_id": None,
                "promotion_review_recommendation": None,
                "promotion_review_decision": None,
                "baseline_total_return": None,
                "shadow_total_return": None,
                "total_return_delta": None,
                "max_drawdown_delta": None,
                "sharpe_delta": None,
                "warnings": None,
            }
        bm = promo.baseline_metrics or {}
        sm = promo.shadow_metrics or {}
        d = promo.metric_deltas or {}
        return {
            "model_key": model_key,
            "latest_promotion_review_id": promo.id,
            "promotion_review_recommendation": promo.recommendation,
            "promotion_review_decision": promo.decision,
            "baseline_total_return": bm.get("total_return"),
            "shadow_total_return": sm.get("total_return"),
            "total_return_delta": d.get("total_return_delta"),
            "max_drawdown_delta": d.get("max_drawdown_delta"),
            "sharpe_delta": d.get("sharpe_ratio_delta"),
            "warnings": promo.warnings,
        }

    async def get_ml_warnings(self, model_key: str) -> list[dict]:
        warnings = []
        val = await self._get_latest_validation(model_key)
        promo = await self._get_latest_promotion(model_key)
        pred_run = await self._get_latest_predict_run(model_key)

        if not pred_run:
            warnings.append({"level": "info", "message": "No predictions yet — run predictions first"})
        if not val:
            warnings.append({"level": "info", "message": "No validation report — run validation"})
        elif val.sample_count < 20:
            warnings.append({"level": "warning", "message": f"Validation sample_count={val.sample_count} < 20 minimum"})
        if val and val.promotion_readiness == "not_ready":
            warnings.append({"level": "warning", "message": "Validation readiness: not_ready"})

        if promo and promo.warnings:
            for w in promo.warnings:
                warnings.append({"level": "warning", "message": w})

        warnings.append({"level": "info", "message": "ML is shadow-only — excluded from live pipeline"})
        return warnings

    async def get_ml_ops_summary(self) -> dict:
        """Full ML ops summary combining all sub-summaries."""
        model_key = "ml_return_forecaster"
        defn = await self._get_definition(model_key)
        pred_run = await self._get_latest_predict_run(model_key)
        pred_count = await self._get_prediction_count(pred_run.id) if pred_run else 0
        val = await self._get_latest_validation(model_key)
        promo = await self._get_latest_promotion(model_key)

        bm = promo.baseline_metrics or {} if promo else {}
        sm = promo.shadow_metrics or {} if promo else {}
        d = promo.metric_deltas or {} if promo else {}

        recommended_action = self._recommend_action(pred_run, val, promo)

        warnings = []
        if not pred_run:
            warnings.append({"level": "info", "message": "No predictions yet — run predictions first"})
        if not val:
            warnings.append({"level": "info", "message": "No validation report — run validation"})
        elif val.sample_count < 20:
            warnings.append({"level": "warning", "message": f"Validation sample_count={val.sample_count} < 20 minimum"})
        if val and val.promotion_readiness == "not_ready":
            warnings.append({"level": "warning", "message": "Validation readiness: not_ready"})
        if promo and promo.warnings:
            for w in promo.warnings:
                warnings.append({"level": "warning", "message": w})
        warnings.append({"level": "info", "message": "ML is shadow-only — excluded from live pipeline"})

        return {
            "model_key": model_key,
            "model_name": defn.name if defn else None,
            "status": defn.status if defn else "unknown",
            "is_shadow": defn.is_shadow if defn else True,
            "latest_prediction_run_id": pred_run.id if pred_run else None,
            "latest_prediction_status": pred_run.status if pred_run else None,
            "prediction_count": pred_count,
            "latest_validation_report_id": val.id if val else None,
            "validation_status": val.status if val else None,
            "validation_sample_count": val.sample_count if val else None,
            "directional_accuracy": val.directional_accuracy if val else None,
            "calibration_error": val.calibration_error if val else None,
            "promotion_readiness": val.promotion_readiness if val else None,
            "latest_promotion_review_id": promo.id if promo else None,
            "promotion_review_recommendation": promo.recommendation if promo else None,
            "promotion_review_decision": promo.decision if promo else None,
            "baseline_total_return": bm.get("total_return"),
            "shadow_total_return": sm.get("total_return"),
            "total_return_delta": d.get("total_return_delta"),
            "max_drawdown_delta": d.get("max_drawdown_delta"),
            "sharpe_delta": d.get("sharpe_ratio_delta"),
            "still_shadow": True,
            "live_pipeline_influence": False,
            "warnings": warnings,
            "recommended_operator_action": recommended_action,
        }

    async def get_ops_ml_block(self) -> dict:
        """Compact ML block for inclusion in /ops endpoint."""
        total = (await self.db.execute(
            select(func.count()).select_from(ModelDefinition)
        )).scalar() or 0
        active = (await self.db.execute(
            select(func.count()).select_from(ModelDefinition)
            .where(ModelDefinition.status.in_(["active", "experimental"]))
        )).scalar() or 0
        shadow = (await self.db.execute(
            select(func.count()).select_from(ModelDefinition)
            .where(ModelDefinition.is_shadow == True)  # noqa: E712
        )).scalar() or 0

        val = await self._get_latest_validation("ml_return_forecaster")
        promo = await self._get_latest_promotion("ml_return_forecaster")

        warning_count = 0
        if val and val.sample_count < 20:
            warning_count += 1
        if val and val.promotion_readiness == "not_ready":
            warning_count += 1
        if promo and promo.warnings:
            warning_count += len(promo.warnings)

        return {
            "total_models": total,
            "active_models": active,
            "shadow_models": shadow,
            "latest_validation_status": val.status if val else None,
            "promotion_readiness": val.promotion_readiness if val else None,
            "warning_count": warning_count,
            "any_model_influences_live_pipeline": False,
            "ml_is_shadow_only": True,
        }
