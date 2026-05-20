"""Paper portfolio service.

Phase 5C: simulated portfolio tracking from published recommendations.
All fills are paper — no broker/execution.
"""
import math
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.ingestion import MarketBar
from app.models.ops import AuditEvent
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.reference import Asset
from app.models.validation import PaperPortfolio, PaperTrade, PaperValuationSnapshot


class PaperPortfolioService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_latest_prices(self, asset_ids: list[str]) -> dict[str, float]:
        """Get latest close price for each asset from market_bars."""
        prices = {}
        for aid in asset_ids:
            row = (await self.db.execute(
                select(MarketBar.close)
                .where(MarketBar.asset_id == aid)
                .order_by(MarketBar.bar_date.desc())
                .limit(1)
            )).scalar()
            if row is not None:
                prices[aid] = row
        return prices

    async def create_from_recommendation(
        self,
        recommendation_id: str,
        starting_value: float = 100000.0,
        allow_unpublished: bool = False,
    ) -> PaperPortfolio:
        """Create a paper portfolio from a recommendation's weights."""
        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )).scalar_one_or_none()

        if not rec:
            raise ValueError("Recommendation not found")

        if rec.status not in ("published", "published_with_warning") and not allow_unpublished:
            raise ValueError(f"Only published recommendations can create paper portfolios (current: {rec.status})")

        # Get weights
        wt_rows = (await self.db.execute(
            select(RecommendationWeight, Asset.ticker)
            .outerjoin(Asset, RecommendationWeight.asset_id == Asset.id)
            .where(RecommendationWeight.recommendation_id == recommendation_id)
        )).all()

        if not wt_rows:
            raise ValueError("Recommendation has no weights")

        # Get latest prices
        asset_ids = [w.asset_id for w, _ in wt_rows]
        prices = await self._get_latest_prices(asset_ids)

        # Build holdings
        holdings = {}
        total_allocated = 0.0
        for w, ticker in wt_rows:
            price = prices.get(w.asset_id, 0)
            target_value = starting_value * w.target_weight
            quantity = int(target_value / price) if price > 0 else 0
            actual_value = quantity * price
            holdings[w.asset_id] = {
                "ticker": ticker or "???",
                "target_weight": w.target_weight,
                "current_weight": w.target_weight,  # at creation, current = target
                "quantity": quantity,
                "last_price": price,
                "target_value": round(target_value, 2),
                "current_value": round(actual_value, 2),
            }
            total_allocated += w.target_weight

        cash_weight = round(max(0, 1.0 - total_allocated), 4)
        now = datetime.now(UTC)

        source_type = "recommendation_paper"
        if allow_unpublished and rec.status not in ("published", "published_with_warning"):
            source_type = "test_paper"

        events = [{
            "timestamp": now.isoformat(),
            "event_type": "creation",
            "message": f"Paper portfolio created from recommendation {recommendation_id[:8]}… with {len(holdings)} positions",
            "metadata": {"recommendation_id": recommendation_id, "starting_value": starting_value},
        }]

        # Deactivate any existing active portfolio
        active = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.is_active == True)  # noqa: E712
        )).scalars().all()
        for p in active:
            p.is_active = False

        pp = PaperPortfolio(
            id=gen_uuid(),
            name=f"Paper — {rec.rationale_summary[:50] if rec.rationale_summary else 'Recommendation'}",
            is_active=True,
            current_holdings=holdings,
            cash_weight=cash_weight,
            portfolio_value=starting_value,
            last_rebalance_at=now,
            total_rebalances=0,
            source_recommendation_id=recommendation_id,
            source_type=source_type,
            events_log=events,
        )
        self.db.add(pp)

        self.db.add(AuditEvent(
            actor="paper_service", action="paper_create",
            object_type="paper_portfolio", object_id=pp.id,
            details={"recommendation_id": recommendation_id, "positions": len(holdings)},
            occurred_at=now,
        ))

        await self.db.commit()

        # Generate initial buy trades
        await self._create_trades_for_creation(pp)

        return pp

    async def compute_drift(self, portfolio_id: str) -> dict:
        """Recompute current weights from latest market prices."""
        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        if not pp:
            raise ValueError("Portfolio not found")

        holdings = pp.current_holdings or {}
        asset_ids = list(holdings.keys())
        prices = await self._get_latest_prices(asset_ids)

        total_value = 0.0
        for aid, info in holdings.items():
            qty = info.get("quantity", 0)
            price = prices.get(aid, info.get("last_price", 0))
            info["last_price"] = price
            info["current_value"] = round(qty * price, 2)
            total_value += info["current_value"]

        # Add cash
        cash_value = pp.portfolio_value * pp.cash_weight
        total_value += cash_value

        # Recompute weights
        drifts = []
        for _aid, info in holdings.items():
            if total_value > 0:
                info["current_weight"] = round(info["current_value"] / total_value, 4)
            drift = round(info["current_weight"] - info["target_weight"], 4)
            info["drift"] = drift
            if abs(drift) > 0.01:
                drifts.append({"ticker": info.get("ticker", "?"), "drift": drift})

        pp.current_holdings = holdings
        pp.portfolio_value = round(total_value, 2)
        await self.db.commit()

        return {
            "portfolio_id": portfolio_id,
            "total_value": round(total_value, 2),
            "cash_weight": pp.cash_weight,
            "drifted_positions": drifts,
            "drift_count": len(drifts),
            "max_drift": max((abs(d["drift"]) for d in drifts), default=0),
        }

    async def rebalance_from_recommendation(self, portfolio_id: str, recommendation_id: str) -> PaperPortfolio:
        """Rebalance paper portfolio from a new recommendation."""
        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        if not pp:
            raise ValueError("Portfolio not found")

        rec = (await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )).scalar_one_or_none()
        if not rec:
            raise ValueError("Recommendation not found")

        wt_rows = (await self.db.execute(
            select(RecommendationWeight, Asset.ticker)
            .outerjoin(Asset, RecommendationWeight.asset_id == Asset.id)
            .where(RecommendationWeight.recommendation_id == recommendation_id)
        )).all()

        asset_ids = [w.asset_id for w, _ in wt_rows]
        prices = await self._get_latest_prices(asset_ids)
        old_holdings = pp.current_holdings or {}

        # Build new holdings
        new_holdings = {}
        total_allocated = 0.0
        turnover = 0.0
        trade_count = 0

        for w, ticker in wt_rows:
            price = prices.get(w.asset_id, 0)
            target_value = pp.portfolio_value * w.target_weight
            quantity = int(target_value / price) if price > 0 else 0
            actual_value = quantity * price

            old_weight = old_holdings.get(w.asset_id, {}).get("target_weight", 0)
            turnover += abs(w.target_weight - old_weight)
            if w.target_weight != old_weight:
                trade_count += 1

            new_holdings[w.asset_id] = {
                "ticker": ticker or "???",
                "target_weight": w.target_weight,
                "current_weight": w.target_weight,
                "quantity": quantity,
                "last_price": price,
                "target_value": round(target_value, 2),
                "current_value": round(actual_value, 2),
            }
            total_allocated += w.target_weight

        now = datetime.now(UTC)
        pp.current_holdings = new_holdings
        pp.cash_weight = round(max(0, 1.0 - total_allocated), 4)
        pp.source_recommendation_id = recommendation_id
        pp.last_rebalance_at = now
        pp.total_rebalances += 1

        events = pp.events_log or []
        events.append({
            "timestamp": now.isoformat(),
            "event_type": "rebalance",
            "message": f"Rebalance #{pp.total_rebalances}: {trade_count} trades, turnover {turnover:.1%}",
            "metadata": {"recommendation_id": recommendation_id, "trade_count": trade_count, "turnover": round(turnover, 4)},
        })
        pp.events_log = events

        await self.db.commit()
        return pp

    async def get_portfolios(self) -> list[PaperPortfolio]:
        return list((await self.db.execute(
            select(PaperPortfolio).order_by(PaperPortfolio.created_at.desc())
        )).scalars().all())

    async def get_portfolio(self, portfolio_id: str) -> PaperPortfolio | None:
        return (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()

    async def get_current(self) -> PaperPortfolio | None:
        return (await self.db.execute(
            select(PaperPortfolio)
            .where(PaperPortfolio.is_active == True)  # noqa: E712
            .order_by(PaperPortfolio.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()

    # ── Trades ────────────────────────────────────────────────────────

    async def _create_trades_for_creation(self, pp: PaperPortfolio, backfill: bool = False) -> int:
        """Create simulated buy trades for initial portfolio creation.

        If backfill=True, checks for existing trades first to avoid duplicates.
        """
        # Check if trades already exist for this portfolio
        existing = (await self.db.execute(
            select(func.count()).select_from(PaperTrade)
            .where(PaperTrade.portfolio_id == pp.id)
        )).scalar() or 0
        if existing > 0:
            return 0  # already has trades

        holdings = pp.current_holdings or {}
        trade_date = pp.created_at or datetime.now(UTC)

        # For backfill, try to get actual prices from market_bars
        asset_ids = list(holdings.keys())
        bar_prices = await self._get_latest_prices(asset_ids) if backfill else {}

        count = 0
        for aid, info in holdings.items():
            qty = info.get("quantity", 0)
            price = bar_prices.get(aid) or info.get("last_price", 0)
            if qty > 0 or info.get("target_weight", 0) > 0:
                if qty == 0 and price > 0:
                    # Estimate quantity from target value
                    target_val = (pp.portfolio_value or 100000) * info.get("target_weight", 0)
                    qty = int(target_val / price) if price > 0 else 0
                self.db.add(PaperTrade(
                    id=gen_uuid(), portfolio_id=pp.id,
                    recommendation_id=pp.source_recommendation_id,
                    trade_date=trade_date, asset_id=aid, ticker=info.get("ticker", "?"),
                    side="buy", quantity=max(qty, 0), price=price,
                    notional=round(max(qty, 0) * price, 2),
                    weight_delta=info.get("target_weight", 0),
                    reason="backfilled_initial_holding" if backfill else "Initial allocation from recommendation",
                ))
                count += 1
        if count > 0:
            await self.db.commit()
        return count

    async def get_trades(self, portfolio_id: str) -> list[PaperTrade]:
        return list((await self.db.execute(
            select(PaperTrade).where(PaperTrade.portfolio_id == portfolio_id)
            .order_by(PaperTrade.trade_date.desc())
        )).scalars().all())

    # ── Valuation snapshots ───────────────────────────────────────────

    async def _get_prices_on_date(self, asset_ids: list[str], on_date: date) -> dict[str, float]:
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

    async def generate_valuation_snapshots(
        self, portfolio_id: str, start_date: date | None = None, end_date: date | None = None,
    ) -> list[PaperValuationSnapshot]:
        """Generate daily valuation snapshots from market_bars. Backfills trades if missing."""
        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        if not pp:
            raise ValueError("Portfolio not found")

        # Backfill trades if holdings exist but no trades
        await self._create_trades_for_creation(pp, backfill=True)

        holdings = pp.current_holdings or {}
        if not holdings:
            return []

        asset_ids = list(holdings.keys())
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Check existing snapshots to avoid duplicates
        existing = (await self.db.execute(
            select(PaperValuationSnapshot.valuation_date)
            .where(PaperValuationSnapshot.portfolio_id == portfolio_id)
        )).scalars().all()
        existing_dates = {d.date() if hasattr(d, 'date') else d for d in existing}

        starting_value = pp.portfolio_value or 100000.0
        cash_value = starting_value * pp.cash_weight
        snapshots = []
        prev_value = None
        peak = 0.0

        d = start_date
        while d <= end_date:
            if d.weekday() >= 5:
                d += timedelta(days=1)
                continue
            if d in existing_dates:
                d += timedelta(days=1)
                continue

            prices = await self._get_prices_on_date(asset_ids, d)
            invested = 0.0
            for aid, info in holdings.items():
                qty = info.get("quantity", 0)
                price = prices.get(aid, info.get("last_price", 0))
                invested += qty * price

            total = invested + cash_value
            daily_ret = None
            if prev_value and prev_value > 0:
                daily_ret = round((total - prev_value) / prev_value, 6)
            cum_ret = round((total - starting_value) / starting_value, 6)

            if total > peak:
                peak = total
            dd = round((peak - total) / peak, 6) if peak > 0 else 0.0

            snap = PaperValuationSnapshot(
                id=gen_uuid(), portfolio_id=portfolio_id,
                valuation_date=datetime(d.year, d.month, d.day, tzinfo=UTC),
                portfolio_value=round(total, 2),
                cash_value=round(cash_value, 2),
                invested_value=round(invested, 2),
                daily_return=daily_ret,
                cumulative_return=cum_ret,
                max_drawdown_to_date=round(-dd, 6),
            )
            self.db.add(snap)
            snapshots.append(snap)
            prev_value = total
            d += timedelta(days=1)

        await self.db.commit()
        return snapshots

    async def get_valuation_snapshots(self, portfolio_id: str) -> list[PaperValuationSnapshot]:
        return list((await self.db.execute(
            select(PaperValuationSnapshot)
            .where(PaperValuationSnapshot.portfolio_id == portfolio_id)
            .order_by(PaperValuationSnapshot.valuation_date)
        )).scalars().all())

    async def get_performance_summary(self, portfolio_id: str) -> dict:
        """Compute performance metrics from valuation snapshots."""
        snaps = await self.get_valuation_snapshots(portfolio_id)
        if not snaps:
            return {"status": "no_data", "message": "No valuation snapshots. Call recompute first."}

        values = [s.portfolio_value for s in snaps]
        returns = [s.daily_return for s in snaps if s.daily_return is not None]
        starting = values[0] if values else 100000
        ending = values[-1] if values else starting
        total_ret = (ending - starting) / starting if starting > 0 else 0
        days = len(snaps)

        ann_ret = None
        if days > 20:
            ann_ret = round((1 + total_ret) ** (252 / max(days, 1)) - 1, 4)

        vol = None
        sharpe = None
        if len(returns) >= 5:
            mean_r = sum(returns) / len(returns)
            var = sum((r - mean_r) ** 2 for r in returns) / len(returns)
            daily_std = math.sqrt(var)
            vol = round(daily_std * math.sqrt(252), 4)
            if vol > 0:
                sharpe = round((mean_r * 252) / vol, 2)

        max_dd = min((s.max_drawdown_to_date or 0) for s in snaps) if snaps else 0

        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        trade_count = (await self.db.execute(
            select(func.count()).select_from(PaperTrade)
            .where(PaperTrade.portfolio_id == portfolio_id)
        )).scalar() or 0

        # Performance basis
        original_start = pp.portfolio_value if pp else 100000
        basis_warnings = []
        if abs(starting - original_start) > 1.0:
            basis_warnings.append(
                "Performance is measured from first available valuation snapshot, not original starting cash."
            )

        start_date_str = snaps[0].valuation_date.isoformat()[:10] if snaps else None
        end_date_str = snaps[-1].valuation_date.isoformat()[:10] if snaps else None

        return {
            "status": "computed",
            "total_return": round(total_ret, 4),
            "annualized_return": ann_ret,
            "max_drawdown": round(max_dd, 4),
            "volatility": vol,
            "sharpe_ratio": sharpe,
            "starting_value": round(starting, 2),
            "ending_value": round(ending, 2),
            "cash_drag": round(pp.cash_weight if pp else 0, 4),
            "trade_count": trade_count,
            "total_rebalances": pp.total_rebalances if pp else 0,
            "snapshot_count": len(snaps),
            "days": days,
            "performance_basis": "first_available_snapshot",
            "basis_start_date": start_date_str,
            "basis_end_date": end_date_str,
            "warnings": basis_warnings,
        }

    # ── Attribution ───────────────────────────────────────────────────

    async def get_asset_attribution(self, portfolio_id: str) -> list[dict]:
        """Per-asset contribution to portfolio return.

        Uses valuation snapshots to determine start/end dates, then queries
        market_bars for actual start/end prices per asset. This produces
        real attribution — not zeros from stale holdings JSON.
        """
        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        if not pp:
            return []

        holdings = pp.current_holdings or {}
        asset_ids = list(holdings.keys())

        # Determine attribution window from snapshots or portfolio dates
        snaps = await self.get_valuation_snapshots(portfolio_id)
        if snaps:
            start_dt = snaps[0].valuation_date
            end_dt = snaps[-1].valuation_date
            start_d = start_dt.date() if hasattr(start_dt, 'date') else start_dt
            end_d = end_dt.date() if hasattr(end_dt, 'date') else end_dt
        else:
            end_d = date.today()
            start_d = end_d - timedelta(days=30)

        # Get actual prices from market_bars at start and end of window
        start_prices = await self._get_prices_on_date(asset_ids, start_d)
        end_prices = await self._get_prices_on_date(asset_ids, end_d)

        attrib = []
        warnings = []
        for aid, info in holdings.items():
            ticker = info.get("ticker", "?")
            weight = info.get("target_weight", 0)
            sp = start_prices.get(aid)
            ep = end_prices.get(aid)

            if sp and ep and sp > 0:
                asset_return = (ep - sp) / sp
                contribution = weight * asset_return
                quality = "ok"
            else:
                asset_return = 0.0
                contribution = 0.0
                quality = "partial"
                warnings.append(f"{ticker}: missing price data for attribution")

            attrib.append({
                "asset_id": aid,
                "ticker": ticker,
                "starting_weight": weight,
                "current_weight": info.get("current_weight", weight),
                "asset_return": round(asset_return, 4),
                "contribution": round(contribution, 4),
                "quality": quality,
                "start_price": round(sp, 2) if sp else None,
                "end_price": round(ep, 2) if ep else None,
            })

        return attrib

    async def get_decision_attribution(self, portfolio_id: str) -> list[dict]:
        """Per-decision (rebalance) contribution."""
        pp = (await self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        )).scalar_one_or_none()
        if not pp:
            return []

        events = pp.events_log or []
        result = []
        for ev in events:
            meta = ev.get("metadata", {})
            result.append({
                "event_type": ev.get("event_type"),
                "recommendation_id": meta.get("recommendation_id"),
                "date": ev.get("timestamp"),
                "turnover": meta.get("turnover", 0),
                "trade_count": meta.get("trade_count", 0),
            })
        return result
