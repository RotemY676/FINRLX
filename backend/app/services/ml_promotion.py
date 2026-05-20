"""ML shadow backtest comparison and promotion governance service.

Phase 6C: compares baseline (deterministic-only) vs shadow (with ML) backtests,
evaluates promotion readiness gates, and persists promotion review reports.

Does NOT automatically promote ML or change engine active status.
"""
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.modeling import MLPromotionReview, ModelValidationReport
from app.models.validation import BacktestExperiment
from app.services.backtesting import BacktestService

MIN_SAMPLE_FOR_PROMOTION = 20
MIN_ACCURACY_FOR_PROMOTION = 0.52
MAX_DRAWDOWN_DELTA_PP = 0.05  # 5 percentage points
MAX_TURNOVER_RATIO = 2.0


def _extract_metrics(bt: BacktestExperiment) -> dict:
    """Extract comparable metrics from a backtest results_summary."""
    rs = bt.results_summary or {}
    return {
        "total_return": rs.get("total_return"),
        "annualized_return": rs.get("annualized_return"),
        "sharpe_ratio": rs.get("sharpe_ratio"),
        "max_drawdown": rs.get("max_drawdown"),
        "volatility": rs.get("volatility"),
        "avg_turnover": rs.get("avg_turnover"),
        "total_trades": rs.get("total_trades"),
        "win_rate": rs.get("win_rate"),
        "rebalance_count": rs.get("rebalance_count"),
    }


def _compute_deltas(baseline: dict, shadow: dict) -> dict:
    """Compute metric deltas: shadow - baseline."""
    deltas = {}
    for key in ["total_return", "annualized_return", "sharpe_ratio", "max_drawdown",
                 "volatility", "avg_turnover", "total_trades", "win_rate"]:
        bv = baseline.get(key)
        sv = shadow.get(key)
        if bv is not None and sv is not None:
            deltas[f"{key}_delta"] = round(sv - bv, 6)
        else:
            deltas[f"{key}_delta"] = None

    # Decision count delta (rebalance_count as proxy)
    bc = baseline.get("rebalance_count")
    sc = shadow.get("rebalance_count")
    deltas["decision_count_delta"] = (sc - bc) if bc is not None and sc is not None else None

    # Turnover delta
    bt_turn = baseline.get("avg_turnover")
    sh_turn = shadow.get("avg_turnover")
    deltas["turnover_delta"] = round(sh_turn - bt_turn, 6) if bt_turn is not None and sh_turn is not None else None

    # Trade count delta
    bt_tc = baseline.get("total_trades")
    sh_tc = shadow.get("total_trades")
    deltas["trade_count_delta"] = (sh_tc - bt_tc) if bt_tc is not None and sh_tc is not None else None

    return deltas


class MLPromotionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_latest_validation(self, model_key: str) -> ModelValidationReport | None:
        return (await self.db.execute(
            select(ModelValidationReport)
            .where(ModelValidationReport.model_key == model_key)
            .order_by(ModelValidationReport.evaluated_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def run_shadow_backtest_review(
        self,
        model_key: str = "ml_return_forecaster",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> MLPromotionReview:
        """Run baseline + shadow backtests and compare results."""
        datetime.now(UTC)
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        bt_svc = BacktestService(self.db)

        # 1. Run baseline backtest (deterministic engines only, no shadow)
        baseline_bt = await bt_svc.run_backtest(
            name="Promotion Review — Baseline",
            start_date=start_date, end_date=end_date,
            include_shadow_engines=False,
        )

        # 2. Run shadow backtest (includes ML shadow engines)
        shadow_bt = await bt_svc.run_backtest(
            name="Promotion Review — Shadow ML",
            start_date=start_date, end_date=end_date,
            include_shadow_engines=True,
        )

        # 3. Compare
        review = await self.compare_backtest_runs(baseline_bt.id, shadow_bt.id, model_key=model_key)
        return review

    async def compare_backtest_runs(
        self,
        baseline_backtest_id: str,
        shadow_backtest_id: str,
        model_key: str = "ml_return_forecaster",
    ) -> MLPromotionReview:
        """Compare two backtest runs and produce a promotion review report."""
        now = datetime.now(UTC)
        warnings = []

        baseline_bt = (await self.db.execute(
            select(BacktestExperiment).where(BacktestExperiment.id == baseline_backtest_id)
        )).scalar_one_or_none()
        shadow_bt = (await self.db.execute(
            select(BacktestExperiment).where(BacktestExperiment.id == shadow_backtest_id)
        )).scalar_one_or_none()

        if not baseline_bt or not shadow_bt:
            review = MLPromotionReview(
                id=gen_uuid(), model_key=model_key, model_version="v1",
                reviewed_at=now, baseline_backtest_id=baseline_backtest_id,
                shadow_backtest_id=shadow_backtest_id,
                sample_count=0, recommendation="not_ready",
                warnings=["Missing backtest(s)"],
            )
            self.db.add(review)
            await self.db.commit()
            return review

        if baseline_bt.status != "completed" or shadow_bt.status != "completed":
            warnings.append("One or both backtests did not complete successfully")

        baseline_metrics = _extract_metrics(baseline_bt)
        shadow_metrics = _extract_metrics(shadow_bt)
        deltas = _compute_deltas(baseline_metrics, shadow_metrics)

        # Get latest validation report
        val_report = await self._get_latest_validation(model_key)
        val_id = val_report.id if val_report else None

        # Add validation metrics to deltas if available
        if val_report:
            deltas["directional_accuracy"] = val_report.directional_accuracy
            deltas["calibration_error"] = val_report.calibration_error

        # Determine sample count from validation
        sample_count = val_report.sample_count if val_report else 0

        # Evaluate promotion readiness
        recommendation = self._evaluate_gates(
            baseline_metrics, shadow_metrics, deltas, val_report, sample_count, warnings,
        )

        review = MLPromotionReview(
            id=gen_uuid(), model_key=model_key, model_version="v1",
            reviewed_at=now,
            baseline_backtest_id=baseline_backtest_id,
            shadow_backtest_id=shadow_backtest_id,
            validation_report_id=val_id,
            baseline_metrics=baseline_metrics,
            shadow_metrics=shadow_metrics,
            metric_deltas=deltas,
            sample_count=sample_count,
            recommendation=recommendation,
            decision=None,
            warnings=warnings if warnings else None,
        )
        self.db.add(review)
        await self.db.commit()
        return review

    def _evaluate_gates(
        self,
        baseline: dict, shadow: dict, deltas: dict,
        val_report: ModelValidationReport | None,
        sample_count: int,
        warnings: list[str],
    ) -> str:
        """Apply promotion readiness gates. Returns recommendation string."""

        # Gate 1: sample count
        if sample_count < MIN_SAMPLE_FOR_PROMOTION:
            warnings.append(f"Sample count {sample_count} < {MIN_SAMPLE_FOR_PROMOTION} minimum")
            return "needs_more_data"

        # Gate 2: validation promotion_readiness
        if val_report and val_report.promotion_readiness == "not_ready":
            warnings.append("Validation promotion_readiness is not_ready")
            return "not_ready"

        # Gate 3: validation directional accuracy
        if val_report and val_report.directional_accuracy is not None:
            if val_report.directional_accuracy < MIN_ACCURACY_FOR_PROMOTION:
                warnings.append(
                    f"Directional accuracy {val_report.directional_accuracy:.1%} < {MIN_ACCURACY_FOR_PROMOTION:.0%}"
                )
                return "not_ready"

        # Gate 4: validation critical warnings
        if val_report and val_report.warnings:
            critical = [w for w in val_report.warnings if "critical" in w.lower()]
            if critical:
                warnings.append(f"Critical validation warnings: {critical}")
                return "reject"

        # Gate 5: shadow total_return vs baseline
        b_ret = baseline.get("total_return")
        s_ret = shadow.get("total_return")
        if b_ret is not None and s_ret is not None and s_ret < b_ret:
            warnings.append(
                f"Shadow return {s_ret:.4f} < baseline {b_ret:.4f} (delta {s_ret - b_ret:+.4f})"
            )
            # Not an automatic reject but noted — still could be promising_shadow

        # Gate 6: max drawdown not worse by more than 5pp
        b_dd = baseline.get("max_drawdown")
        s_dd = shadow.get("max_drawdown")
        if b_dd is not None and s_dd is not None:
            # max_drawdown is negative convention: -0.05 is 5% drawdown
            # Worse means more negative
            dd_delta = s_dd - b_dd  # negative if shadow is worse
            if dd_delta < -MAX_DRAWDOWN_DELTA_PP:
                warnings.append(
                    f"Shadow drawdown {s_dd:.4f} worse than baseline {b_dd:.4f} by {abs(dd_delta):.4f} "
                    f"(exceeds {MAX_DRAWDOWN_DELTA_PP} pp limit)"
                )
                return "reject"

        # Gate 7: turnover ratio
        b_turn = baseline.get("avg_turnover")
        s_turn = shadow.get("avg_turnover")
        if b_turn is not None and s_turn is not None and b_turn > 0:
            turn_ratio = s_turn / b_turn
            if turn_ratio > MAX_TURNOVER_RATIO:
                # Check if return improvement justifies it
                if b_ret is not None and s_ret is not None and s_ret > b_ret:
                    warnings.append(
                        f"Shadow turnover {turn_ratio:.1f}x baseline but return improved — acceptable"
                    )
                else:
                    warnings.append(
                        f"Shadow turnover {turn_ratio:.1f}x baseline exceeds {MAX_TURNOVER_RATIO}x limit "
                        f"without return improvement"
                    )
                    return "reject"

        # If we pass all gates, determine recommendation level
        if val_report and val_report.directional_accuracy is not None:
            if val_report.directional_accuracy >= 0.58:
                return "eligible_for_review"
            elif val_report.directional_accuracy >= MIN_ACCURACY_FOR_PROMOTION:
                return "promising_shadow"

        return "promising_shadow"

    async def evaluate_promotion_readiness(self, model_key: str) -> dict:
        """Quick evaluation of current promotion readiness without running backtests."""
        val_report = await self._get_latest_validation(model_key)
        latest_review = await self.get_latest_promotion_review(model_key)

        result = {
            "model_key": model_key,
            "still_shadow": True,
            "has_validation": val_report is not None,
            "has_promotion_review": latest_review is not None,
        }

        if val_report:
            result["validation_sample_count"] = val_report.sample_count
            result["directional_accuracy"] = val_report.directional_accuracy
            result["calibration_error"] = val_report.calibration_error
            result["validation_promotion_readiness"] = val_report.promotion_readiness

        if latest_review:
            result["latest_review_id"] = latest_review.id
            result["review_recommendation"] = latest_review.recommendation
            result["review_decision"] = latest_review.decision
            result["metric_deltas"] = latest_review.metric_deltas

        return result

    async def get_latest_promotion_review(self, model_key: str) -> MLPromotionReview | None:
        return (await self.db.execute(
            select(MLPromotionReview)
            .where(MLPromotionReview.model_key == model_key)
            .order_by(MLPromotionReview.reviewed_at.desc()).limit(1)
        )).scalar_one_or_none()

    async def get_promotion_review_history(self, model_key: str) -> list[MLPromotionReview]:
        return list((await self.db.execute(
            select(MLPromotionReview)
            .where(MLPromotionReview.model_key == model_key)
            .order_by(MLPromotionReview.reviewed_at.desc()).limit(20)
        )).scalars().all())

    async def get_review_by_id(self, review_id: str) -> MLPromotionReview | None:
        return (await self.db.execute(
            select(MLPromotionReview).where(MLPromotionReview.id == review_id)
        )).scalar_one_or_none()

    async def record_decision(
        self, review_id: str, decision: str,
    ) -> MLPromotionReview | None:
        """Record an operator decision on a promotion review.

        Accepted decisions: keep_shadow, request_more_data, eligible_for_review, reject.
        This does NOT activate ML in live scoring.
        """
        valid_decisions = {"keep_shadow", "request_more_data", "eligible_for_review", "reject"}
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of: {valid_decisions}")

        review = await self.get_review_by_id(review_id)
        if not review:
            return None

        review.decision = decision
        await self.db.commit()
        return review
