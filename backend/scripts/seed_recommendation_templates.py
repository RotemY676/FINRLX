"""Seed the 5 pre-made ``recommendation_templates`` (Phase TPL-1).

Idempotent: skips templates whose ``key`` already exists. Each seed
honors the locked product decisions in
``project_phase_w_tpl_fx_op_decisions.md``:

* Capital Preservation — Conservative, 1y_3y, max DD 5%
* Balanced Growth — Moderate, 3y_5y, max DD 15%
* Long-Term Growth — Moderate-Aggressive, 5y_10y, max DD 25%
* Tech Growth — Aggressive, 5y_10y, max DD 40%, sector tilt Technology
* Income Focus — Moderate-Conservative, 3y_5y, max DD 15%,
  sector tilt Financials + Utilities (dividend-yielding sectors)

Run: ``python -m scripts.seed_recommendation_templates`` from backend/.
"""
from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.recommendation_template import RecommendationTemplate
from app.services.profile_mapping import derive_allocation

SEED_TEMPLATES: list[dict] = [
    {
        "key": "capital_preservation",
        "name": "Capital Preservation",
        "description": (
            "Protects principal first. Mostly defensive holdings, modest "
            "equity sleeve. Suited to a 1–3 year horizon."
        ),
        "badge": "Conservative",
        "risk_bucket": "conservative",
        "horizon_band": "1y_3y",
        "primary_goal": "preservation",
        "max_drawdown_pct": 5.0,
        "sector_whitelist_json": json.dumps([]),
        "sector_blacklist_json": json.dumps([]),
        "exclude_leverage": True,
        "base_currency": "USD",
        "trading_frequency": "monthly",
        "region_preference": "global",
    },
    {
        "key": "balanced_growth",
        "name": "Balanced Growth",
        "description": (
            "Classic balanced mix. Steady equity exposure with defensive "
            "ballast. Suited to a 3–5 year horizon."
        ),
        "badge": "Moderate",
        "risk_bucket": "moderate",
        "horizon_band": "3y_5y",
        "primary_goal": "growth",
        "max_drawdown_pct": 15.0,
        "sector_whitelist_json": json.dumps([]),
        "sector_blacklist_json": json.dumps([]),
        "exclude_leverage": True,
        "base_currency": "USD",
        "trading_frequency": "monthly",
        "region_preference": "global",
    },
    {
        "key": "long_term_growth",
        "name": "Long-Term Growth",
        "description": (
            "Tilts to equities for long-term compounding. Accepts notable "
            "drawdowns. Suited to a 5–10 year horizon."
        ),
        "badge": "Moderate-Aggressive",
        "risk_bucket": "moderate_aggressive",
        "horizon_band": "5y_10y",
        "primary_goal": "growth",
        "max_drawdown_pct": 25.0,
        "sector_whitelist_json": json.dumps([]),
        "sector_blacklist_json": json.dumps([]),
        "exclude_leverage": True,
        "base_currency": "USD",
        "trading_frequency": "monthly",
        "region_preference": "global",
    },
    {
        "key": "tech_growth",
        "name": "Tech Growth",
        "description": (
            "Concentrated growth tilt in Technology. Highest expected "
            "volatility — accept large drawdowns for compounding upside."
        ),
        "badge": "Aggressive",
        "risk_bucket": "aggressive",
        "horizon_band": "5y_10y",
        "primary_goal": "aggressive_growth",
        "max_drawdown_pct": 40.0,
        "sector_whitelist_json": json.dumps(["Technology"]),
        "sector_blacklist_json": json.dumps([]),
        "exclude_leverage": True,
        "base_currency": "USD",
        "trading_frequency": "weekly",
        "region_preference": "global",
    },
    {
        "key": "income_focus",
        "name": "Income Focus",
        "description": (
            "Leans on dividend-yielding sectors (Financials, Utilities) "
            "with capped drawdowns. Steady income with modest growth."
        ),
        "badge": "Moderate-Conservative",
        "risk_bucket": "moderate_conservative",
        "horizon_band": "3y_5y",
        "primary_goal": "income",
        "max_drawdown_pct": 15.0,
        "sector_whitelist_json": json.dumps(["Financials", "Utilities"]),
        "sector_blacklist_json": json.dumps([]),
        "exclude_leverage": True,
        "base_currency": "USD",
        "trading_frequency": "monthly",
        "region_preference": "global",
    },
]


def _allocation_summary(risk_bucket: str, horizon: str) -> str:
    """Return the (equity)/(defensive) split as a human label e.g. '60/40'."""
    targets = derive_allocation(risk_bucket, horizon)
    return f"{int(round(targets.equity_pct))}/{int(round(targets.defensive_pct))}"


async def seed() -> dict[str, int]:
    inserted = 0
    skipped = 0
    async with async_session_factory() as db:
        for t in SEED_TEMPLATES:
            exists = (
                await db.execute(
                    select(RecommendationTemplate).where(
                        RecommendationTemplate.key == t["key"]
                    )
                )
            ).scalar_one_or_none()
            if exists is not None:
                skipped += 1
                continue
            db.add(
                RecommendationTemplate(
                    key=t["key"],
                    name=t["name"],
                    description=t["description"],
                    badge=t["badge"],
                    risk_bucket=t["risk_bucket"],
                    horizon_band=t["horizon_band"],
                    primary_goal=t["primary_goal"],
                    max_drawdown_pct=t["max_drawdown_pct"],
                    sector_whitelist_json=t["sector_whitelist_json"],
                    sector_blacklist_json=t["sector_blacklist_json"],
                    exclude_leverage=t["exclude_leverage"],
                    base_currency=t["base_currency"],
                    trading_frequency=t["trading_frequency"],
                    region_preference=t["region_preference"],
                    is_seed=True,
                    is_active=True,
                    allocation_summary=_allocation_summary(
                        t["risk_bucket"], t["horizon_band"]
                    ),
                )
            )
            inserted += 1
        await db.commit()
        total_now = len(
            (await db.execute(select(RecommendationTemplate))).scalars().all()
        )
    return {"inserted": inserted, "skipped": skipped, "total_now": total_now}


def main() -> None:
    result = asyncio.run(seed())
    print(
        f"recommendation_templates: inserted={result['inserted']} "
        f"skipped={result['skipped']} total_now={result['total_now']}"
    )


if __name__ == "__main__":
    main()
