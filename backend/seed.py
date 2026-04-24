"""Seed script: populates the database with realistic demo data.

Run: python -m seed
Requires:
  1. DATABASE_URL env var or .env file pointing to a running database
  2. Migrations must be run first: alembic upgrade head
     (seed does NOT create tables — that is the migration's job)
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import text
from app.core.database import engine, async_session_factory
from app.models import (
    Asset, Universe, UniverseMembership,
    Recommendation, RecommendationWeight,
    SelectionRun, AllocationResult, TimingResult, RiskOverlayResult,
)


def uid() -> str:
    return str(uuid.uuid4())


ASSETS = [
    {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "exchange": "NASDAQ"},
    {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology", "exchange": "NASDAQ"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "exchange": "NASDAQ"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "exchange": "NASDAQ"},
    {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials", "exchange": "NYSE"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "exchange": "NYSE"},
    {"ticker": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy", "exchange": "NYSE"},
    {"ticker": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Staples", "exchange": "NYSE"},
    {"ticker": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology", "exchange": "NASDAQ"},
    {"ticker": "V", "name": "Visa Inc.", "sector": "Financials", "exchange": "NYSE"},
]


async def seed():
    async with async_session_factory() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT count(*) FROM assets"))
        count = result.scalar()
        if count and count > 0:
            print(f"Database already has {count} assets. Skipping seed.")
            return

        # Create assets
        asset_ids = {}
        for a in ASSETS:
            asset_id = uid()
            asset_ids[a["ticker"]] = asset_id
            db.add(Asset(id=asset_id, **a))

        # Create universe
        universe_id = uid()
        db.add(Universe(id=universe_id, name="US Large Cap Core", description="Core large-cap US equity universe"))
        for asset_id in asset_ids.values():
            db.add(UniverseMembership(universe_id=universe_id, asset_id=asset_id))

        # Create a published recommendation
        now = datetime.now(timezone.utc)
        rec_id = uid()
        db.add(Recommendation(
            id=rec_id,
            universe_id=universe_id,
            status="published",
            published_at=now - timedelta(hours=2),
            model_confidence=0.78,
            data_confidence=0.92,
            operational_confidence=0.95,
            valid_from=now - timedelta(hours=2),
            valid_to=now + timedelta(days=5),
            rationale_summary=(
                "Moderate overweight in technology driven by strong earnings momentum and "
                "positive sentiment signals. Underweight energy on declining price momentum. "
                "Risk overlay reduced NVDA position due to concentration limits."
            ),
            warnings=["NVDA position capped by 8% concentration limit"],
            data_as_of=now - timedelta(hours=3),
        ))

        # Weights
        weight_data = [
            ("AAPL",  0.15, 0.12, 0.03,  "overweight",  "Strong earnings beat, positive news sentiment"),
            ("MSFT",  0.14, 0.13, 0.01,  "overweight",  "Cloud growth acceleration, stable fundamentals"),
            ("GOOGL", 0.12, 0.11, 0.01,  "overweight",  "Ad revenue recovery, AI tailwinds"),
            ("AMZN",  0.10, 0.10, 0.00,  "neutral",     "Mixed signals: retail soft, AWS strong"),
            ("JPM",   0.10, 0.09, 0.01,  "overweight",  "Rate environment favorable, strong buyback"),
            ("JNJ",   0.08, 0.09, -0.01, "neutral",     "Defensive hold, stable dividend"),
            ("XOM",   0.06, 0.09, -0.03, "underweight", "Declining price momentum, sector rotation"),
            ("PG",    0.08, 0.08, 0.00,  "neutral",     "Stable consumer staples anchor"),
            ("NVDA",  0.08, 0.10, -0.02, "overweight",  "Risk-adjusted down from 10% due to concentration cap"),
            ("V",     0.09, 0.09, 0.00,  "neutral",     "Consistent payments growth, fair value"),
        ]
        for ticker, tw, pw, delta, stance, rationale in weight_data:
            db.add(RecommendationWeight(
                id=uid(),
                recommendation_id=rec_id,
                asset_id=asset_ids[ticker],
                target_weight=tw,
                previous_weight=pw,
                delta=delta,
                stance=stance,
                rationale=rationale,
            ))

        # Selection run
        sel_id = uid()
        db.add(SelectionRun(
            id=sel_id,
            recommendation_id=rec_id,
            universe_id=universe_id,
            included_assets=[
                {"asset_id": asset_ids[t], "ticker": t, "reason": "Passed liquidity and coverage filters"}
                for t in asset_ids
            ],
            excluded_assets=[],
            rationale="All 10 universe members passed selection filters.",
        ))

        # Allocation
        alloc_id = uid()
        db.add(AllocationResult(
            id=alloc_id,
            recommendation_id=rec_id,
            selection_run_id=sel_id,
            weights={asset_ids[t]: w for t, w, *_ in weight_data},
            method="signal-weighted with momentum tilt",
            rationale="Weights derived from composite signal scores with momentum overlay.",
        ))

        # Timing
        db.add(TimingResult(
            id=uid(),
            recommendation_id=rec_id,
            urgency="soon",
            horizon_days=5,
            rationale="No immediate catalyst, but positioning before earnings season.",
        ))

        # Risk overlay
        db.add(RiskOverlayResult(
            id=uid(),
            recommendation_id=rec_id,
            pre_risk_weights={asset_ids[t]: w for t, w, *_ in weight_data},
            post_risk_weights={asset_ids[t]: w for t, w, *_ in weight_data},
            adjustments=[{
                "asset_id": asset_ids["NVDA"],
                "ticker": "NVDA",
                "reason": "Concentration cap at 8%",
                "delta": -0.02,
            }],
            constraints_applied=["max_single_position_8pct", "min_cash_0pct"],
            portfolio_risk_score=0.42,
            rationale="NVDA reduced from 10% to 8% due to single-position concentration limit.",
        ))

        await db.commit()
        print(f"Seeded: {len(ASSETS)} assets, 1 universe, 1 recommendation with {len(weight_data)} weights")


if __name__ == "__main__":
    asyncio.run(seed())
