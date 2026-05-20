"""Test fixtures: in-memory SQLite database with seeded data."""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.rate_limit import limiter
from app.main import app
from app.models import (
    Asset, Universe, UniverseMembership,
    Recommendation, RecommendationWeight,
    SelectionRun, AllocationResult, TimingResult, RiskOverlayResult,
    AuditEvent, DataFeed, PolicyBreach, PublicationQueueEntry, Incident,
    SignalRun, SignalOutput,
    MarketBar, NewsEvent, IngestionManifest,
    FeatureDefinition, FeatureSet, FeatureValue,
    EngineDefinition,
)

# Disable rate-limiting in tests so the suite is hermetic. Endpoint decorators
# still parse; the limiter just doesn't enforce. Individual tests that need the
# limiter active flip it to True inside a try/finally.
limiter.enabled = False

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

        # Ops seed data
        db.add(DataFeed(id=uid(), name="Reuters · news intel", status="ok", lag="0s", coverage="99.8%", slo=0.98, last_checked_at=now))
        db.add(DataFeed(id=uid(), name="Options flow · CBOE", status="degraded", lag="14m", coverage="72%", slo=0.86, last_checked_at=now))

        db.add(PolicyBreach(id=uid(), kind="sector", label="Semis 28.1%/30%", utilization=0.937, trend="+0.8%", severity="high", related="NVDA", is_active=True))
        db.add(PolicyBreach(id=uid(), kind="oil", label="Energy 12%/10%", utilization=1.2, trend="+1.9%", severity="breach", related="Escalated", is_active=True))

        queue_id_1 = uid()
        db.add(PublicationQueueEntry(id=queue_id_1, recommendation_id="REC-NVDA-L", ticker="NVDA", stance="LONG", version="v4", submitted_ago="12m", submitter="R. Mikhailov", weight="+4.2%", confidence=0.74, flags=["sector cap"], priority="high", status="pending"))
        db.add(PublicationQueueEntry(id=uid(), recommendation_id="REC-XOM-S", ticker="XOM", stance="SHORT", version="v2", submitted_ago="22m", submitter="A. Chen", weight="-2.1%", confidence=0.68, flags=[], priority="mid", status="pending"))

        db.add(Incident(id=uid(), severity=2, title="Options flow feed latency spike", description="Confidence capped.", status="open", source="M. Alvarez"))

        db.add(AuditEvent(id=uid(), actor="R. Mikhailov", action="publish", object_type="recommendation", details={"description": "published rec v4", "ago": "12m"}, occurred_at=now - timedelta(minutes=12)))
        db.add(AuditEvent(id=uid(), actor="system", action="breach", object_type="breach", details={"description": "sector limit approaching", "ago": "38m"}, occurred_at=now - timedelta(minutes=38)))

        # Signal run for engine health
        run_id = uid()
        db.add(SignalRun(id=run_id, engine_name="momentum", engine_version="v3.2", run_started_at=now - timedelta(minutes=3), run_completed_at=now - timedelta(minutes=2), status="completed", data_as_of=now - timedelta(minutes=2)))
        db.add(SignalOutput(id=uid(), signal_run_id=run_id, asset_id=asset_ids["AAPL"], score=0.7, stance="buy", confidence=0.82, rationale="Test", artifacts={}))

        # Ingestion seed: 30 days of market bars for both assets + news
        bar_count = 0
        for ticker, aid in asset_ids.items():
            base_price = 195.0 if ticker == "AAPL" else 420.0
            for i in range(30):
                d = (now - timedelta(days=30 - i)).date()
                if d.weekday() >= 5:
                    continue
                price = base_price + i * 0.5
                db.add(MarketBar(
                    id=uid(), asset_id=aid, ticker=ticker,
                    bar_date=d, interval="1d",
                    open=round(price - 0.5, 2), high=round(price + 1.5, 2),
                    low=round(price - 1.5, 2), close=round(price, 2),
                    volume=20000000 + i * 100000, source="test",
                ))
                bar_count += 1

        # A few news events for sentiment features
        for i in range(5):
            d = now - timedelta(days=i + 1)
            db.add(NewsEvent(
                id=uid(), headline=f"AAPL test news {i}", source="test",
                published_at=d, tickers=["AAPL"],
                sentiment_score=0.3 + i * 0.1, sentiment_label="positive",
                category="test",
            ))

        db.add(IngestionManifest(
            id=uid(), source="test", kind="bars", status="completed",
            asset_count=2, row_count=bar_count,
            date_from=(now - timedelta(days=30)).date(), date_to=now.date(),
            started_at=now, completed_at=now,
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
