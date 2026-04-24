"""Backtest runner service.

Phase 5A: walk-forward simulation using real market_bars and pipeline logic.

Methodology:
  - Walk forward from start_date to end_date at rebalance_frequency intervals
  - At each rebalance date: compute features → run engines → run pipeline → get weights
  - Between rebalances: track portfolio value using actual bar close prices
  - Transaction cost: fixed bps deducted at each rebalance
  - Metrics: total return, annualized, max drawdown, volatility, Sharpe, turnover

Limitation: features/engines/pipeline are computed as-of each rebalance date using
market_bars available up to that date. This is a safe approximation — no future data
is used in feature computation since features query bars with bar_date <= as_of.
"""
import math
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import BacktestExperiment
from app.models.ingestion import MarketBar
from app.models.reference import Asset, Universe, UniverseMembership
from app.models.base import gen_uuid
from app.services.features import FeatureService
from app.services.engines import EngineService
from app.services.pipeline import DecisionPipelineService


DEFAULT_COST_BPS = 10  # 10 bps per trade
REBALANCE_WEEKLY = "weekly"
REBALANCE_MONTHLY = "monthly"


class BacktestService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_universe_assets(self, universe_id: str | None) -> list[tuple[str, str]]:
        if not universe_id:
            uni = (await self.db.execute(select(Universe.id).limit(1))).scalar()
            universe_id = uni
        if not universe_id:
            return []
        rows = (await self.db.execute(
            select(Asset.id, Asset.ticker)
            .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
            .where(UniverseMembership.universe_id == universe_id)
        )).all()
        return [(r.id, r.ticker) for r in rows]

    async def _get_bar_prices(self, asset_ids: list[str], on_date: date) -> dict[str, float]:
        """Get close prices for assets on or before a specific date."""
        prices = {}
        for aid in asset_ids:
            row = (await self.db.execute(
                select(MarketBar.close)
                .where(MarketBar.asset_id == aid)
                .where(MarketBar.bar_date <= on_date)
                .order_by(MarketBar.bar_date.desc())
                .limit(1)
            )).scalar()
            if row is not None:
                prices[aid] = row
        return prices

    def _generate_rebalance_dates(self, start: date, end: date, frequency: str) -> list[date]:
        """Generate rebalance dates between start and end."""
        dates = []
        d = start
        while d <= end:
            if d.weekday() < 5:  # skip weekends
                dates.append(d)
            if frequency == REBALANCE_MONTHLY:
                # Advance ~30 days
                d += timedelta(days=30)
                # Snap to next weekday
                while d.weekday() >= 5:
                    d += timedelta(days=1)
            else:  # weekly
                d += timedelta(days=7)
                while d.weekday() >= 5:
                    d += timedelta(days=1)
        return dates

    async def run_backtest(
        self,
        name: str = "Walk-Forward Backtest",
        start_date: date | None = None,
        end_date: date | None = None,
        universe_id: str | None = None,
        rebalance_frequency: str = REBALANCE_MONTHLY,
        cost_bps: int = DEFAULT_COST_BPS,
    ) -> BacktestExperiment:
        """Run a walk-forward backtest using real market_bars and pipeline logic."""
        now = datetime.now(timezone.utc)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        # Create experiment record
        bt = BacktestExperiment(
            id=gen_uuid(), name=name, status="running",
            universe_id=universe_id,
            start_date=datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc),
            end_date=datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc),
            config={
                "rebalance_frequency": rebalance_frequency,
                "cost_bps": cost_bps,
                "methodology": "walk-forward",
                "pipeline": "Phase 4 pipeline (features → engines → selection → allocation → timing → risk)",
            },
        )
        self.db.add(bt)
        await self.db.commit()

        assets = await self._get_universe_assets(universe_id)
        if not assets:
            bt.status = "failed"
            bt.results_summary = {"warnings": ["No assets in universe"]}
            await self.db.commit()
            return bt

        asset_ids = [a[0] for a in assets]
        rebalance_dates = self._generate_rebalance_dates(start_date, end_date, rebalance_frequency)

        if len(rebalance_dates) < 2:
            bt.status = "failed"
            bt.results_summary = {"warnings": ["Insufficient date range for backtest"]}
            await self.db.commit()
            return bt

        # Walk-forward simulation
        portfolio_value = 100.0
        equity_curve = [{"date": rebalance_dates[0].isoformat(), "value": 100.0}]
        current_weights: dict[str, float] = {}
        trade_count = 0
        turnover_sum = 0.0
        period_returns: list[float] = []
        peak = 100.0
        max_drawdown = 0.0
        warnings: list[str] = []
        decision_points: list[dict] = []

        for i, reb_date in enumerate(rebalance_dates):
            # Get prices at rebalance date
            prices = await self._get_bar_prices(asset_ids, reb_date)

            if i > 0 and current_weights:
                # Compute return from previous rebalance to now
                prev_prices_date = rebalance_dates[i - 1]
                prev_prices = await self._get_bar_prices(asset_ids, prev_prices_date)

                period_return = 0.0
                for aid, w in current_weights.items():
                    if aid in prices and aid in prev_prices and prev_prices[aid] > 0:
                        asset_return = (prices[aid] - prev_prices[aid]) / prev_prices[aid]
                        period_return += w * asset_return

                portfolio_value *= (1 + period_return)
                period_returns.append(period_return)

                # Track drawdown
                if portfolio_value > peak:
                    peak = portfolio_value
                dd = (peak - portfolio_value) / peak if peak > 0 else 0
                if dd > max_drawdown:
                    max_drawdown = dd

            equity_curve.append({"date": reb_date.isoformat(), "value": round(portfolio_value, 2)})

            # Compute new weights using pipeline as-of reb_date
            try:
                feat_svc = FeatureService(self.db)
                await feat_svc.ensure_default_definitions()
                fs = await feat_svc.compute_features(universe_id=universe_id, as_of=reb_date)

                eng_svc = EngineService(self.db)
                await eng_svc.ensure_default_engines()
                await eng_svc.run_engines(feature_set_id=fs.id)

                pipe_svc = DecisionPipelineService(self.db)
                pipe_result = await pipe_svc.run_pipeline(feature_set_id=fs.id, universe_id=universe_id)

                if pipe_result["status"] == "completed" and pipe_result.get("recommendation_id"):
                    # Tag backtest recommendation so it doesn't pollute live current
                    from app.models.recommendation import Recommendation as RecModel, RecommendationWeight
                    bt_rec = (await self.db.execute(
                        select(RecModel).where(RecModel.id == pipe_result["recommendation_id"])
                    )).scalar_one_or_none()
                    if bt_rec:
                        bt_rec.context = "backtest"

                    wt_rows = (await self.db.execute(
                        select(RecommendationWeight)
                        .where(RecommendationWeight.recommendation_id == pipe_result["recommendation_id"])
                    )).scalars().all()

                    new_weights = {w.asset_id: w.target_weight for w in wt_rows}

                    # Compute turnover
                    turnover = sum(abs(new_weights.get(a, 0) - current_weights.get(a, 0)) for a in set(list(new_weights.keys()) + list(current_weights.keys())))
                    turnover_sum += turnover
                    trade_count += sum(1 for a in new_weights if new_weights[a] != current_weights.get(a, 0))

                    # Apply transaction cost
                    cost = turnover * cost_bps / 10000
                    portfolio_value *= (1 - cost)

                    current_weights = new_weights

                    decision_points.append({
                        "date": reb_date.isoformat(),
                        "recommendation_id": pipe_result["recommendation_id"],
                        "positions": len(new_weights),
                        "turnover": round(turnover, 4),
                    })
                else:
                    warnings.append(f"Pipeline failed at {reb_date}: {pipe_result.get('message', 'unknown')}")

            except Exception as e:
                warnings.append(f"Error at {reb_date}: {str(e)[:100]}")

        # Final equity point
        equity_curve.append({"date": end_date.isoformat(), "value": round(portfolio_value, 2)})

        # Compute metrics
        total_return = (portfolio_value - 100) / 100
        n_periods = len(period_returns)
        days = (end_date - start_date).days

        annualized_return = None
        if days > 30:
            annualized_return = round((1 + total_return) ** (365 / max(days, 1)) - 1, 4)

        vol = None
        sharpe = None
        if n_periods >= 2:
            mean_r = sum(period_returns) / n_periods
            var = sum((r - mean_r) ** 2 for r in period_returns) / n_periods
            period_std = math.sqrt(var)
            # Annualize based on frequency
            periods_per_year = 52 if rebalance_frequency == REBALANCE_WEEKLY else 12
            vol = round(period_std * math.sqrt(periods_per_year), 4)
            if vol > 0:
                sharpe = round((mean_r * periods_per_year) / (vol), 2)

        avg_turnover = round(turnover_sum / max(n_periods, 1), 4) if n_periods > 0 else None
        win_rate = None
        if period_returns:
            wins = sum(1 for r in period_returns if r > 0)
            win_rate = round(wins / len(period_returns), 2)

        # Collect provenance from decision points
        rec_ids = [dp["recommendation_id"] for dp in decision_points if dp.get("recommendation_id")]
        feat_set_ids = set()
        sig_run_ids = set()
        for dp in decision_points:
            rid = dp.get("recommendation_id")
            if rid:
                from app.models.recommendation import Recommendation as RecModel
                r = (await self.db.execute(select(RecModel).where(RecModel.id == rid))).scalar_one_or_none()
                if r and r.source_feature_set_id:
                    feat_set_ids.add(r.source_feature_set_id)
                if r and r.source_signal_run_ids:
                    sig_run_ids.update(r.source_signal_run_ids)

        bt.status = "completed"
        bt.results_summary = {
            "total_return": round(total_return, 4),
            "annualized_return": annualized_return,
            "max_drawdown": round(-max_drawdown, 4),
            "sharpe_ratio": sharpe,
            "volatility": vol,
            "total_trades": trade_count,
            "avg_turnover": avg_turnover,
            "win_rate": win_rate,
            "rebalance_count": len(rebalance_dates),
            "equity_curve": equity_curve,
            "decision_points": decision_points,
            "warnings": warnings,
            # Provenance
            "source_type": "pipeline_backtest",
            "is_demo": False,
            "recommendation_ids": rec_ids,
            "source_feature_set_ids": list(feat_set_ids),
            "source_signal_run_ids": list(sig_run_ids),
            "market_bar_window": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "rebalance_dates": [d.isoformat() for d in rebalance_dates],
            "created_by_service": "BacktestService.run_backtest",
        }
        await self.db.commit()
        return bt

    async def get_backtest_status(self) -> dict:
        total = (await self.db.execute(
            select(func.count()).select_from(BacktestExperiment)
        )).scalar() or 0
        completed = (await self.db.execute(
            select(func.count()).select_from(BacktestExperiment)
            .where(BacktestExperiment.status == "completed")
        )).scalar() or 0
        return {"total": total, "completed": completed}
