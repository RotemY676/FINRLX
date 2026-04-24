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
    BacktestExperiment, PaperPortfolio, ReplaySnapshot,
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

WEIGHT_DATA = [
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


async def seed():
    async with async_session_factory() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT count(*) FROM assets"))
        count = result.scalar()
        if count and count > 0:
            print(f"Database already has {count} assets. Skipping seed.")
            return

        now = datetime.now(timezone.utc)

        # ── Assets ──
        asset_ids = {}
        for a in ASSETS:
            asset_id = uid()
            asset_ids[a["ticker"]] = asset_id
            db.add(Asset(id=asset_id, **a))

        # ── Universe ──
        universe_id = uid()
        db.add(Universe(id=universe_id, name="US Large Cap Core", description="Core large-cap US equity universe"))
        for asset_id in asset_ids.values():
            db.add(UniverseMembership(universe_id=universe_id, asset_id=asset_id))

        # ── Published recommendation ──
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

        for ticker, tw, pw, delta, stance, rationale in WEIGHT_DATA:
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

        # ── Decision pipeline stages ──
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

        alloc_id = uid()
        db.add(AllocationResult(
            id=alloc_id,
            recommendation_id=rec_id,
            selection_run_id=sel_id,
            weights={asset_ids[t]: w for t, w, *_ in WEIGHT_DATA},
            method="signal-weighted with momentum tilt",
            rationale="Weights derived from composite signal scores with momentum overlay.",
        ))

        db.add(TimingResult(
            id=uid(),
            recommendation_id=rec_id,
            urgency="soon",
            horizon_days=5,
            rationale="No immediate catalyst, but positioning before earnings season.",
        ))

        db.add(RiskOverlayResult(
            id=uid(),
            recommendation_id=rec_id,
            pre_risk_weights={asset_ids[t]: w for t, w, *_ in WEIGHT_DATA},
            post_risk_weights={asset_ids[t]: w for t, w, *_ in WEIGHT_DATA},
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

        # ── Replay snapshots ──
        for stage_name, stage_data in [
            ("selection", {
                "included_count": 10, "excluded_count": 0,
                "rationale": "All 10 universe members passed selection filters.",
            }),
            ("allocation", {
                "method": "signal-weighted with momentum tilt",
                "weights": {t: w for t, w, *_ in WEIGHT_DATA},
            }),
            ("timing", {
                "urgency": "soon", "horizon_days": 5,
                "rationale": "Positioning before earnings season.",
            }),
            ("risk_overlay", {
                "portfolio_risk_score": 0.42,
                "adjustments": [{"ticker": "NVDA", "delta": -0.02, "reason": "Concentration cap"}],
                "constraints": ["max_single_position_8pct", "min_cash_0pct"],
            }),
            ("publication", {
                "status": "published",
                "confidence": {"model": 0.78, "data": 0.92, "operational": 0.95},
                "warnings": ["NVDA position capped by 8% concentration limit"],
                "weights": {t: w for t, w, *_ in WEIGHT_DATA},
            }),
        ]:
            db.add(ReplaySnapshot(
                id=uid(),
                recommendation_id=rec_id,
                stage=stage_name,
                snapshot_data=stage_data,
                captured_at=now - timedelta(hours=2, minutes=30 - 5 * ["selection", "allocation", "timing", "risk_overlay", "publication"].index(stage_name)),
            ))

        # ── Backtest experiment ──
        bt_start = now - timedelta(days=365)
        bt_end = now - timedelta(days=30)
        # Generate a simple equity curve (monthly, base 100)
        equity_curve = []
        val = 100.0
        import random
        random.seed(42)  # deterministic
        d = bt_start
        while d <= bt_end:
            equity_curve.append({"date": d.strftime("%Y-%m-%d"), "value": round(val, 2)})
            val *= 1 + random.gauss(0.008, 0.03)  # ~1% monthly return, 3% vol
            d += timedelta(days=30)
        equity_curve.append({"date": bt_end.strftime("%Y-%m-%d"), "value": round(val, 2)})
        total_return = (val - 100) / 100

        db.add(BacktestExperiment(
            id=uid(),
            name="Momentum Tilt v1 — 12-Month Walk-Forward",
            status="completed",
            policy_version_id=None,
            universe_id=universe_id,
            start_date=bt_start,
            end_date=bt_end,
            config={
                "strategy": "signal-weighted with momentum tilt",
                "rebalance_frequency": "monthly",
                "universe": "US Large Cap Core",
                "benchmark": "Equal Weight",
                "cost_model": "10bps round-trip",
                "lookback_window": "60 days",
                "walk_forward_splits": 4,
            },
            results_summary={
                "total_return": round(total_return, 4),
                "annualized_return": round(total_return * (365 / 335), 4),
                "max_drawdown": -0.087,
                "sharpe_ratio": 1.12,
                "volatility": 0.142,
                "total_trades": 48,
                "avg_turnover": 0.15,
                "equity_curve": equity_curve,
                "warnings": [
                    "Backtest uses simplified cost model (flat 10bps)",
                    "Walk-forward window covers only 12 months",
                ],
            },
            is_promoted=False,
        ))

        # ── Paper portfolio ──
        # Simulate holdings that have drifted slightly from target
        paper_holdings = {}
        paper_events = []
        for ticker, tw, *_ in WEIGHT_DATA:
            drift = random.uniform(-0.015, 0.015)
            paper_holdings[asset_ids[ticker]] = {
                "ticker": ticker,
                "target_weight": tw,
                "current_weight": round(tw + drift, 4),
            }

        paper_events.append({
            "timestamp": (now - timedelta(days=7)).isoformat(),
            "event_type": "creation",
            "description": "Paper portfolio created from published recommendation.",
        })
        paper_events.append({
            "timestamp": (now - timedelta(days=7)).isoformat(),
            "event_type": "rebalance",
            "description": "Initial allocation applied: 10 positions, 0% cash.",
        })
        paper_events.append({
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "event_type": "drift_alert",
            "description": "Portfolio drift exceeds 1% threshold on 3 positions.",
        })

        db.add(PaperPortfolio(
            id=uid(),
            name="Live Shadow — Momentum Tilt v1",
            is_active=True,
            current_holdings=paper_holdings,
            cash_weight=0.0,
            last_rebalance_at=now - timedelta(days=7),
            total_rebalances=1,
        ))

        await db.commit()
        print(
            f"Seeded: {len(ASSETS)} assets, 1 universe, 1 recommendation, "
            f"5 replay snapshots, 1 backtest, 1 paper portfolio"
        )


if __name__ == "__main__":
    asyncio.run(seed())
