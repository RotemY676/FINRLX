"""Test fixtures: in-memory SQLite database with seeded data."""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.models import (
    Asset, Universe, UniverseMembership,
    Recommendation, RecommendationWeight,
    SelectionRun, AllocationResult, TimingResult, RiskOverlayResult,
)

TEST_DB_URL = "sqlite+aiosqlite://"  # in-memory

engine = create_async_engine(TEST_DB_URL)
test_session_factory = async_sessionmaker(engine, expire_on_commit=False)


def uid():
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Create tables and seed once for the entire test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as db:
        # Create test assets
        asset_ids = {}
        for ticker, name in [("AAPL", "Apple Inc."), ("MSFT", "Microsoft Corp.")]:
            aid = uid()
            asset_ids[ticker] = aid
            db.add(Asset(id=aid, ticker=ticker, name=name, sector="Technology"))

        universe_id = uid()
        db.add(Universe(id=universe_id, name="Test Universe"))
        for aid in asset_ids.values():
            db.add(UniverseMembership(universe_id=universe_id, asset_id=aid))

        now = datetime.now(timezone.utc)
        rec_id = uid()
        db.add(Recommendation(
            id=rec_id,
            universe_id=universe_id,
            status="published",
            published_at=now - timedelta(hours=1),
            model_confidence=0.85,
            data_confidence=0.90,
            operational_confidence=0.95,
            valid_from=now - timedelta(hours=1),
            valid_to=now + timedelta(days=3),
            rationale_summary="Test recommendation",
            warnings=[],
            data_as_of=now - timedelta(hours=2),
        ))

        db.add(RecommendationWeight(
            id=uid(), recommendation_id=rec_id, asset_id=asset_ids["AAPL"],
            target_weight=0.60, previous_weight=0.50, delta=0.10, stance="overweight",
        ))
        db.add(RecommendationWeight(
            id=uid(), recommendation_id=rec_id, asset_id=asset_ids["MSFT"],
            target_weight=0.40, previous_weight=0.50, delta=-0.10, stance="underweight",
        ))

        # Decision pipeline stages
        sel_id = uid()
        db.add(SelectionRun(
            id=sel_id, recommendation_id=rec_id, universe_id=universe_id,
            included_assets=[
                {"asset_id": asset_ids["AAPL"], "ticker": "AAPL", "reason": "Passed filters"},
                {"asset_id": asset_ids["MSFT"], "ticker": "MSFT", "reason": "Passed filters"},
            ],
            excluded_assets=[], rationale="All passed.",
        ))
        db.add(AllocationResult(
            id=uid(), recommendation_id=rec_id, selection_run_id=sel_id,
            weights={asset_ids["AAPL"]: 0.60, asset_ids["MSFT"]: 0.40},
            method="equal-risk", rationale="Test allocation.",
        ))
        db.add(TimingResult(
            id=uid(), recommendation_id=rec_id,
            urgency="soon", horizon_days=3, rationale="Test timing.",
        ))
        db.add(RiskOverlayResult(
            id=uid(), recommendation_id=rec_id,
            portfolio_risk_score=0.35,
            adjustments=[], constraints_applied=["test_constraint"],
            rationale="No adjustments needed.",
        ))

        await db.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
