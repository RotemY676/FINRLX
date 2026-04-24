"""Paper portfolio service.

Phase 5C: simulated portfolio tracking from published recommendations.
All fills are paper — no broker/execution.
"""
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation import PaperPortfolio
from app.models.recommendation import Recommendation, RecommendationWeight
from app.models.ingestion import MarketBar
from app.models.reference import Asset
from app.models.ops import AuditEvent
from app.models.base import gen_uuid


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
        now = datetime.now(timezone.utc)

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
        for aid, info in holdings.items():
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

        now = datetime.now(timezone.utc)
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
