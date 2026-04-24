"""Seed script: populates the database with realistic demo data.

Run: python -m seed
Requires:
  1. DATABASE_URL env var or .env file pointing to a running database
  2. Migrations must be run first: alembic upgrade head
"""
import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy import text
from app.core.database import engine, async_session_factory
from app.models import (
    Asset, Universe, UniverseMembership,
    Recommendation, RecommendationWeight,
    SelectionRun, AllocationResult, TimingResult, RiskOverlayResult,
    BacktestExperiment, PaperPortfolio, ReplaySnapshot,
    SignalRun, SignalOutput, AuditEvent,
)

random.seed(42)


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
    ("AAPL", 0.15, 0.12, 0.03, "overweight", "Strong earnings beat, positive news sentiment"),
    ("MSFT", 0.14, 0.13, 0.01, "overweight", "Cloud growth acceleration, stable fundamentals"),
    ("GOOGL", 0.12, 0.11, 0.01, "overweight", "Ad revenue recovery, AI tailwinds"),
    ("AMZN", 0.10, 0.10, 0.00, "neutral", "Mixed signals: retail soft, AWS strong"),
    ("JPM", 0.10, 0.09, 0.01, "overweight", "Rate environment favorable, strong buyback"),
    ("JNJ", 0.08, 0.09, -0.01, "neutral", "Defensive hold, stable dividend"),
    ("XOM", 0.06, 0.09, -0.03, "underweight", "Declining price momentum, sector rotation"),
    ("PG", 0.08, 0.08, 0.00, "neutral", "Stable consumer staples anchor"),
    ("NVDA", 0.08, 0.10, -0.02, "overweight", "Risk-adjusted down from 10% due to concentration cap"),
    ("V", 0.09, 0.09, 0.00, "neutral", "Consistent payments growth, fair value"),
]

# ── Engine definitions matching design handoff (comparison.jsx) ──
ENGINE_DEFS = [
    {
        "key": "momentum", "name": "Momentum", "version": "v3.2",
        "stance": "buy", "confidence": 0.82, "weight": 0.28, "risk": "Moderate", "horizon": "3M",
        "drivers": ["9-wk price acceleration", "Factor tilt: momentum +0.62σ", "Sector leadership persistence"],
        "ignores": ["Options positioning", "Near-term earnings quality"],
        "note": "High conviction long; engine capped at 28% weight in risk-on regimes.",
        "freshness_min": 2,
    },
    {
        "key": "fundamentals", "name": "Fundamentals", "version": "v2.8",
        "stance": "buy", "confidence": 0.71, "weight": 0.24, "risk": "Moderate", "horizon": "6M",
        "drivers": ["EPS revisions +4.8% median", "Data-center guidance raise", "Margin expansion vs peers"],
        "ignores": ["Short-term flow & positioning"],
        "note": "Served fallback path during 09:20 data lag; attribution partial.",
        "freshness_min": 3,
    },
    {
        "key": "narrative", "name": "Narrative LLM", "version": "v1.4",
        "stance": "hold", "confidence": 0.58, "weight": 0.18, "risk": "Elevated", "horizon": "3M",
        "drivers": ["Mixed sentiment: supply-chain risk", "Sector tone softened −0.22", "Retail interest plateau"],
        "ignores": ["Quantitative factor exposure"],
        "note": "Dissents on direction; flags Taiwan logistics narrative as unresolved.",
        "freshness_min": 5,
    },
    {
        "key": "riskparity", "name": "Risk-parity", "version": "v2.1",
        "stance": "hold", "confidence": 0.54, "weight": 0.18, "risk": "Low", "horizon": "6M",
        "drivers": ["Correlation to top-5 0.71 (high)", "Realized vol 34% (elevated)", "Diversification-cost binding"],
        "ignores": ["Momentum signal", "News flow"],
        "note": "Trim bias under current concentration; not a directional view.",
        "freshness_min": 2,
    },
    {
        "key": "flow", "name": "Flow / options", "version": "v1.9",
        "stance": "sell", "confidence": 0.49, "weight": 0.12, "risk": "High", "horizon": "1M",
        "drivers": ["Put/call skew widening", "Negative gamma through 950", "Dealer hedging cross-flow"],
        "ignores": ["Earnings revisions", "Macro regime"],
        "note": "Confidence capped while options IV is stale (14m).",
        "freshness_min": 14,
    },
]

# ── Evidence items matching design handoff (modules.jsx EvidenceCard) ──
EVIDENCE_ITEMS = [
    {
        "order": 1, "title": "Earnings revisions",
        "body": "Remain the dominant driver. 18 of 24 sell-side analysts raised FY26 EPS estimates over the last 30 days; median revision concentrated in data-center segment guidance.",
        "delta_label": "+4.8%", "delta_direction": "pos", "source_engine": "fundamentals",
    },
    {
        "order": 2, "title": "Price momentum",
        "body": "In the top decile of the universe for a 9th consecutive week, with acceleration vs the equal-weight semi index. Factor attribution: momentum +0.62, quality +0.31.",
        "delta_label": "+0.62σ", "delta_direction": "pos", "source_engine": "momentum",
    },
    {
        "order": 3, "title": "Options positioning",
        "body": "Has rotated defensive. 30-day put/call skew widened; gamma exposure rolled negative through the 950 strike. Platform reads this as constructive-contrarian, not a breakdown.",
        "delta_label": "±0", "delta_direction": "neutral", "source_engine": "flow",
    },
    {
        "order": 4, "title": "News sentiment",
        "body": "Mixed. Supply-chain risk narrative re-emerged after the 16-Apr Taiwan logistics disruption; sector-level sentiment dropped but NVDA-specific remained positive.",
        "delta_label": "−0.22", "delta_direction": "neg", "source_engine": "narrative",
    },
    {
        "order": 5, "title": "Regime filter",
        "body": "Flags late-cycle risk-on with widening dispersion. Platform down-weights beta-carry engines by 15%; narrative & fundamentals engines unchanged.",
        "delta_label": "—", "delta_direction": "flat", "source_engine": None,
    },
]

# ── Activity events matching design handoff (overview.jsx ACTIVITY) ──
ACTIVITY_EVENTS = [
    {"kind": "publish", "actor": "R. Mikhailov", "what": "published current recommendation v4", "ago": "12m", "detail": "Momentum + earnings · horizon 3M"},
    {"kind": "breach", "actor": "system", "what": "sector limit approaching", "ago": "38m", "detail": "Semis 28.1% of 30% cap"},
    {"kind": "engine", "actor": "system", "what": "Flow/options engine down-weighted", "ago": "44m", "detail": "Data stale 14m · confidence capped"},
    {"kind": "note", "actor": "J. Park", "what": "added note to META thesis", "ago": "1h", "detail": "Earnings in 2 days · review synthesis"},
    {"kind": "defer", "actor": "A. Chen", "what": "deferred XOM short to tomorrow", "ago": "2h", "detail": "Awaiting crude inventory print"},
    {"kind": "incident", "actor": "Ops", "what": "reuters feed recovered", "ago": "3h", "detail": "Backfilled 09:14 → 09:27 · re-scored 11 recs"},
    {"kind": "backtest", "actor": "M. Alvarez", "what": "backtest #204 complete", "ago": "3h", "detail": "Momentum + quality · 5y IR 1.32"},
    {"kind": "publish", "actor": "R. Mikhailov", "what": "published REC-AAPL-L v2", "ago": "4h", "detail": "Services + buyback"},
]


def _ago_to_timedelta(ago: str) -> timedelta:
    if ago.endswith("m"):
        return timedelta(minutes=int(ago[:-1]))
    if ago.endswith("h"):
        return timedelta(hours=int(ago[:-1]))
    return timedelta(minutes=5)


async def seed():
    async with async_session_factory() as db:
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
        for aid in asset_ids.values():
            db.add(UniverseMembership(universe_id=universe_id, asset_id=aid))

        # ── Published recommendation ──
        rec_id = uid()
        db.add(Recommendation(
            id=rec_id, universe_id=universe_id, status="published",
            published_at=now - timedelta(hours=2),
            model_confidence=0.78, data_confidence=0.92, operational_confidence=0.95,
            valid_from=now - timedelta(hours=2), valid_to=now + timedelta(days=5),
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
                id=uid(), recommendation_id=rec_id, asset_id=asset_ids[ticker],
                target_weight=tw, previous_weight=pw, delta=delta, stance=stance, rationale=rationale,
            ))

        # ── Decision pipeline stages ──
        sel_id = uid()
        db.add(SelectionRun(
            id=sel_id, recommendation_id=rec_id, universe_id=universe_id,
            included_assets=[{"asset_id": asset_ids[t], "ticker": t, "reason": "Passed liquidity and coverage filters"} for t in asset_ids],
            excluded_assets=[], rationale="All 10 universe members passed selection filters.",
        ))
        db.add(AllocationResult(
            id=uid(), recommendation_id=rec_id, selection_run_id=sel_id,
            weights={asset_ids[t]: w for t, w, *_ in WEIGHT_DATA},
            method="signal-weighted with momentum tilt",
            rationale="Weights derived from composite signal scores with momentum overlay.",
        ))
        db.add(TimingResult(
            id=uid(), recommendation_id=rec_id, urgency="soon", horizon_days=5,
            rationale="No immediate catalyst, but positioning before earnings season.",
        ))
        db.add(RiskOverlayResult(
            id=uid(), recommendation_id=rec_id,
            pre_risk_weights={asset_ids[t]: w for t, w, *_ in WEIGHT_DATA},
            post_risk_weights={asset_ids[t]: w for t, w, *_ in WEIGHT_DATA},
            adjustments=[{"asset_id": asset_ids["NVDA"], "ticker": "NVDA", "reason": "Concentration cap at 8%", "delta": -0.02}],
            constraints_applied=["max_single_position_8pct", "min_cash_0pct"],
            portfolio_risk_score=0.42,
            rationale="NVDA reduced from 10% to 8% due to single-position concentration limit.",
        ))

        # ── Per-engine signal runs + outputs ──
        for eng in ENGINE_DEFS:
            run_id = uid()
            db.add(SignalRun(
                id=run_id, engine_name=eng["key"], engine_version=eng["version"],
                run_started_at=now - timedelta(minutes=eng["freshness_min"] + 1),
                run_completed_at=now - timedelta(minutes=eng["freshness_min"]),
                status="completed", data_as_of=now - timedelta(minutes=eng["freshness_min"]),
            ))
            # Create outputs for key assets (NVDA primary, plus a few others)
            for ticker in ["NVDA", "AAPL", "MSFT", "XOM", "GOOGL"]:
                stance_map = {
                    "momentum": {"NVDA": "buy", "AAPL": "buy", "MSFT": "buy", "XOM": "sell", "GOOGL": "buy"},
                    "fundamentals": {"NVDA": "buy", "AAPL": "buy", "MSFT": "hold", "XOM": "hold", "GOOGL": "buy"},
                    "narrative": {"NVDA": "hold", "AAPL": "hold", "MSFT": "hold", "XOM": "sell", "GOOGL": "hold"},
                    "riskparity": {"NVDA": "hold", "AAPL": "hold", "MSFT": "buy", "XOM": "hold", "GOOGL": "hold"},
                    "flow": {"NVDA": "sell", "AAPL": "hold", "MSFT": "hold", "XOM": "sell", "GOOGL": "hold"},
                }
                st = stance_map.get(eng["key"], {}).get(ticker, "hold")
                conf = round(eng["confidence"] + random.uniform(-0.08, 0.08), 2)
                db.add(SignalOutput(
                    id=uid(), signal_run_id=run_id, asset_id=asset_ids[ticker],
                    score=round(random.uniform(0.3, 0.9), 3), stance=st,
                    confidence=min(max(conf, 0.1), 0.99),
                    rationale=eng["note"],
                    artifacts={"drivers": eng["drivers"], "ignores": eng["ignores"],
                               "risk": eng["risk"], "horizon": eng["horizon"],
                               "weight": eng["weight"]},
                ))

        # ── Replay snapshots ──
        for stage_name, stage_data in [
            ("selection", {"included_count": 10, "excluded_count": 0, "rationale": "All 10 passed."}),
            ("allocation", {"method": "signal-weighted", "weights": {t: w for t, w, *_ in WEIGHT_DATA}}),
            ("timing", {"urgency": "soon", "horizon_days": 5}),
            ("risk_overlay", {"portfolio_risk_score": 0.42, "adjustments": [{"ticker": "NVDA", "delta": -0.02}]}),
            ("publication", {"status": "published", "confidence": {"model": 0.78, "data": 0.92, "operational": 0.95}}),
        ]:
            db.add(ReplaySnapshot(
                id=uid(), recommendation_id=rec_id, stage=stage_name, snapshot_data=stage_data,
                captured_at=now - timedelta(hours=2, minutes=30 - 5 * ["selection", "allocation", "timing", "risk_overlay", "publication"].index(stage_name)),
            ))

        # ── Backtest experiment ──
        bt_start = now - timedelta(days=365)
        bt_end = now - timedelta(days=30)
        equity_curve = []
        val = 100.0
        d = bt_start
        while d <= bt_end:
            equity_curve.append({"date": d.strftime("%Y-%m-%d"), "value": round(val, 2)})
            val *= 1 + random.gauss(0.008, 0.03)
            d += timedelta(days=30)
        equity_curve.append({"date": bt_end.strftime("%Y-%m-%d"), "value": round(val, 2)})
        total_return = (val - 100) / 100

        db.add(BacktestExperiment(
            id=uid(), name="Momentum Tilt v1 — 12-Month Walk-Forward", status="completed",
            universe_id=universe_id, start_date=bt_start, end_date=bt_end,
            config={"strategy": "signal-weighted with momentum tilt", "rebalance_frequency": "monthly",
                    "universe": "US Large Cap Core", "benchmark": "Equal Weight", "cost_model": "10bps round-trip",
                    "lookback_window": "60 days", "walk_forward_splits": 4},
            results_summary={"total_return": round(total_return, 4), "annualized_return": round(total_return * (365/335), 4),
                             "max_drawdown": -0.087, "sharpe_ratio": 1.12, "volatility": 0.142,
                             "total_trades": 48, "avg_turnover": 0.15, "equity_curve": equity_curve,
                             "warnings": ["Backtest uses simplified cost model (flat 10bps)", "Walk-forward window covers only 12 months"]},
            is_promoted=False,
        ))

        # ── Paper portfolio ──
        paper_holdings = {}
        for ticker, tw, *_ in WEIGHT_DATA:
            drift = random.uniform(-0.015, 0.015)
            paper_holdings[asset_ids[ticker]] = {"ticker": ticker, "target_weight": tw, "current_weight": round(tw + drift, 4)}

        db.add(PaperPortfolio(
            id=uid(), name="Live Shadow — Momentum Tilt v1", is_active=True,
            current_holdings=paper_holdings, cash_weight=0.0,
            last_rebalance_at=now - timedelta(days=7), total_rebalances=1,
        ))

        # ── Audit / activity events ──
        for ev in ACTIVITY_EVENTS:
            td = _ago_to_timedelta(ev["ago"])
            db.add(AuditEvent(
                id=uid(), actor=ev["actor"], action=ev["kind"],
                object_type="recommendation" if ev["kind"] in ("publish", "defer") else ev["kind"],
                details={"description": ev["what"], "detail": ev["detail"], "ago": ev["ago"]},
                occurred_at=now - td,
            ))

        await db.commit()
        print(
            f"Seeded: {len(ASSETS)} assets, 1 universe, 1 recommendation, "
            f"{len(ENGINE_DEFS)} engines × 5 assets = {len(ENGINE_DEFS)*5} signal outputs, "
            f"{len(EVIDENCE_ITEMS)} evidence items, {len(ACTIVITY_EVENTS)} audit events, "
            f"5 replay snapshots, 1 backtest, 1 paper portfolio"
        )


if __name__ == "__main__":
    asyncio.run(seed())
