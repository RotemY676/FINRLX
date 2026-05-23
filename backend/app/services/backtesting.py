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
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.ingestion import MarketBar
from app.models.reference import Asset, Universe, UniverseMembership
from app.models.validation import BacktestExperiment
from app.services.engines import EngineService
from app.services.features import FeatureService
from app.services.pipeline import DecisionPipelineService

DEFAULT_COST_BPS = 10  # 10 bps per trade


def _calc_calmar(annualized_return: float | None, max_drawdown: float | None) -> float | None:
    """Calmar ratio = annualized return / |max drawdown|.

    Conventions match the rest of this service: `max_drawdown` is stored as a
    negative number (e.g. -0.21 for a 21% drawdown). A zero drawdown returns
    None (undefined ratio) rather than +inf. Any None input returns None.
    """
    if annualized_return is None or max_drawdown is None:
        return None
    denom = abs(max_drawdown)
    if denom == 0:
        return None
    return round(annualized_return / denom, 2)


# Phase 19D: tickers that backtests are compared against as passive benchmarks.
# Tickers must exist as MarketBar rows (queried by ticker, not asset_id) for
# the comparison to be computed; if a ticker has no bars in the requested
# window we return None for that benchmark rather than failing the backtest.
DEFAULT_BENCHMARK_TICKERS = ("SPY", "QQQ")


REBALANCE_WEEKLY = "weekly"
REBALANCE_MONTHLY = "monthly"


class BacktestService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_universe_assets(self, universe_id: str | None) -> list[tuple[str, str]]:
        if not universe_id:
            # Phase 20.1 — deterministic + active-only default pick (same
            # rationale as pipeline.py and universe.get_default_universe).
            uni = (await self.db.execute(
                select(Universe.id)
                .where(Universe.is_active.is_(True))
                .order_by(Universe.created_at.asc())
                .limit(1)
            )).scalar()
            universe_id = uni
        if not universe_id:
            return []
        rows = (await self.db.execute(
            select(Asset.id, Asset.ticker)
            .join(UniverseMembership, UniverseMembership.asset_id == Asset.id)
            .where(UniverseMembership.universe_id == universe_id)
            .where(UniverseMembership.removed_at.is_(None))
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

    async def _compute_benchmark_metrics(
        self,
        ticker: str,
        rebalance_dates: list[date],
        end_date: date,
        periods_per_year: int,
    ) -> dict | None:
        """Compute buy-and-hold metrics for a benchmark ticker over the same
        rebalance grid as the strategy. Returns None when the ticker has no
        bars in the requested window so the UI can render "N/A" instead of
        a fabricated zero.

        Periodic returns are sampled at each rebalance date plus end_date,
        which makes Sharpe / vol directly comparable to the strategy (same
        sampling frequency, no leakage). max_drawdown tracks the running
        peak of the buy-and-hold equity series, signed negative to match
        the rest of this service.
        """
        if len(rebalance_dates) < 2:
            return None

        # Pull all bars for this ticker once; query by ticker (not asset_id)
        # so the helper works whether or not the benchmark is in any Universe.
        rows = (await self.db.execute(
            select(MarketBar.bar_date, MarketBar.close)
            .where(MarketBar.ticker == ticker)
            .where(MarketBar.bar_date >= rebalance_dates[0])
            .where(MarketBar.bar_date <= end_date)
            .order_by(MarketBar.bar_date.asc())
        )).all()
        if not rows:
            return None
        # Map dates → close to allow "most recent close on or before D" lookups.
        by_date: dict[date, float] = {r.bar_date: float(r.close) for r in rows}
        sorted_dates = sorted(by_date.keys())

        def close_at(target: date) -> float | None:
            # Find the most recent bar on or before `target`.
            lo, hi = 0, len(sorted_dates) - 1
            best = None
            while lo <= hi:
                mid = (lo + hi) // 2
                if sorted_dates[mid] <= target:
                    best = sorted_dates[mid]
                    lo = mid + 1
                else:
                    hi = mid - 1
            return by_date[best] if best is not None else None

        # Sample equity curve at each rebalance date + end_date.
        sample_dates = list(rebalance_dates) + [end_date]
        prices = [close_at(d) for d in sample_dates]
        # Filter out None head/tail caused by ticker coming online late.
        first_idx = next((i for i, p in enumerate(prices) if p is not None), None)
        if first_idx is None:
            return None
        prices = prices[first_idx:]
        if any(p is None for p in prices) or len(prices) < 2:
            return None

        # Normalize equity to base 100 to match the strategy's curve.
        base = prices[0]
        equity = [round(100.0 * p / base, 2) for p in prices]
        # Periodic returns between consecutive samples.
        period_returns: list[float] = []
        peak = equity[0]
        max_dd = 0.0
        for i in range(1, len(equity)):
            period_returns.append(equity[i] / equity[i - 1] - 1)
            if equity[i] > peak:
                peak = equity[i]
            dd = (peak - equity[i]) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        total_return = equity[-1] / equity[0] - 1
        days = (end_date - sample_dates[first_idx]).days
        annualized_return = None
        if days > 30:
            annualized_return = round((1 + total_return) ** (365 / max(days, 1)) - 1, 4)

        vol = None
        sharpe = None
        if len(period_returns) >= 2:
            mean_r = sum(period_returns) / len(period_returns)
            var = sum((r - mean_r) ** 2 for r in period_returns) / len(period_returns)
            period_std = math.sqrt(var)
            vol = round(period_std * math.sqrt(periods_per_year), 4)
            if vol > 0:
                sharpe = round((mean_r * periods_per_year) / vol, 2)

        max_dd_signed = round(-max_dd, 4)
        return {
            "total_return": round(total_return, 4),
            "annualized_return": annualized_return,
            "max_drawdown": max_dd_signed,
            "sharpe_ratio": sharpe,
            "calmar_ratio": _calc_calmar(annualized_return, max_dd_signed),
            "volatility": vol,
        }

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
        include_shadow_engines: bool = False,
    ) -> BacktestExperiment:
        """Run a walk-forward backtest using real market_bars and pipeline logic."""
        datetime.now(UTC)

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)

        # Create experiment record
        bt = BacktestExperiment(
            id=gen_uuid(), name=name, status="running",
            universe_id=universe_id,
            start_date=datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC),
            end_date=datetime(end_date.year, end_date.month, end_date.day, tzinfo=UTC),
            config={
                "rebalance_frequency": rebalance_frequency,
                "cost_bps": cost_bps,
                "methodology": "walk-forward",
                "pipeline": "Phase 4 pipeline (features → engines → selection → allocation → timing → risk)",
                "include_shadow_engines": include_shadow_engines,
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
                pipe_result = await pipe_svc.run_pipeline(
                    feature_set_id=fs.id, universe_id=universe_id,
                    include_shadow_engines=include_shadow_engines,
                )

                if pipe_result["status"] == "completed" and pipe_result.get("recommendation_id"):
                    # Tag backtest recommendation so it doesn't pollute live current
                    from app.models.recommendation import Recommendation as RecModel
                    from app.models.recommendation import RecommendationWeight
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
        max_drawdown_signed = round(-max_drawdown, 4)
        calmar = _calc_calmar(annualized_return, max_drawdown_signed)
        # Phase 19D: passive-benchmark comparison. Same rebalance grid and
        # periods_per_year scaling as the strategy, so Sharpe / vol / Calmar
        # are apples-to-apples. Each ticker is queried independently;
        # tickers without bars in the window simply yield None.
        periods_per_year_for_benchmark = 52 if rebalance_frequency == REBALANCE_WEEKLY else 12
        benchmark_metrics: dict[str, dict | None] = {}
        for bench_ticker in DEFAULT_BENCHMARK_TICKERS:
            try:
                benchmark_metrics[bench_ticker] = await self._compute_benchmark_metrics(
                    ticker=bench_ticker,
                    rebalance_dates=rebalance_dates,
                    end_date=end_date,
                    periods_per_year=periods_per_year_for_benchmark,
                )
            except Exception as e:  # noqa: BLE001 — benchmark failure must never fail the backtest
                warnings.append(f"Benchmark {bench_ticker} failed: {str(e)[:100]}")
                benchmark_metrics[bench_ticker] = None
        bt.results_summary = {
            "total_return": round(total_return, 4),
            "annualized_return": annualized_return,
            "max_drawdown": max_drawdown_signed,
            "sharpe_ratio": sharpe,
            "calmar_ratio": calmar,
            "volatility": vol,
            "total_trades": trade_count,
            "avg_turnover": avg_turnover,
            "win_rate": win_rate,
            "rebalance_count": len(rebalance_dates),
            "equity_curve": equity_curve,
            "decision_points": decision_points,
            "benchmark_metrics": benchmark_metrics,
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
            "include_shadow_engines": include_shadow_engines,
        }
        if include_shadow_engines:
            bt.results_summary["experimental_context"] = "ml_shadow"
            bt.results_summary["model_key"] = "ml_return_forecaster"

        # Phase C2 — backtest hygiene gate. Reads the just-written config +
        # results_summary, scores against the 5+ pathologies the skill
        # encodes (look-ahead, walk-forward declaration, rebalance count,
        # Sharpe inflation, per-period outliers). Output goes onto
        # results_summary["hygiene"] so the frontend + ops can inspect.
        # Blocks append warnings; status stays "completed" so the operator
        # gets a full record to review rather than a half-written row.
        from app.services import backtest_hygiene
        # Build decision_data_as_of map from the recommendation rows we tagged
        # during the run — gives the look-ahead rule something to check.
        decision_data_as_of: dict[str, date | str] = {}
        for dp in decision_points:
            rec_id = dp.get("recommendation_id")
            if rec_id and dp.get("date"):
                decision_data_as_of[rec_id] = dp["date"]
        hygiene_report = backtest_hygiene.evaluate(
            config=bt.config,
            results_summary=bt.results_summary,
            decision_data_as_of=decision_data_as_of or None,
        )
        bt.results_summary["hygiene"] = {
            "passed": hygiene_report.passed,
            "blocks": list(hygiene_report.block_violations),
            "warns": list(hygiene_report.warn_violations),
            "details": dict(hygiene_report.details),
        }
        if hygiene_report.block_violations:
            for blocked in hygiene_report.block_violations:
                bt.results_summary["warnings"].append(f"hygiene: {blocked}")

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
