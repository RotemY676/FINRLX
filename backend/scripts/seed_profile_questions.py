"""Seed the ``profile_questions`` catalog (Phase W-1).

Idempotent: skips questions whose ``code`` already exists.

Question set design (sources documented in DOCS/handoff/PHASE_W1_INVESTOR_PROFILE_SCHEMA.md):

* Step 2 — Knowledge & experience (MiFID II §1): 4 items.
* Step 3 — Financial situation (MiFID II §2): 4 items, banded only.
* Step 4 — Risk tolerance: 8 items distilled from Grable-Lytton 1999.
* Step 5 — Investment objectives: 3 items.
* Step 6 — Universe & sector preferences: 4 items.
* Step 7 — Operational preferences: 3 items.

Steps 1 (Welcome) and 8 (Review) have no questions — they're UI-only.

Run with: ``python -m scripts.seed_profile_questions`` from the backend
directory.
"""
from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.profile import ProfileQuestion

# ── Choice helpers ───────────────────────────────────────────────────


def _gl_choices(labels: list[str]) -> str:
    """Grable-Lytton-style choice list: each label scored 1..N."""
    return json.dumps(
        [{"value": str(i + 1), "label": label, "score": i + 1} for i, label in enumerate(labels)]
    )


def _enum_choices(values: list[tuple[str, str]]) -> str:
    """Plain enum-style choices: (value, label) tuples, no scoring."""
    return json.dumps([{"value": v, "label": label} for v, label in values])


def _multi_choices(values: list[tuple[str, str]]) -> str:
    """Multi-select choices stored same as enum; consumer handles multi."""
    return _enum_choices(values)


# ── Question catalog ─────────────────────────────────────────────────


QUESTIONS: list[dict] = [
    # ── Step 2: Knowledge & experience (MiFID II §1)
    {
        "code": "K_01_LEVEL",
        "step": 2,
        "order_in_step": 1,
        "dimension": "knowledge",
        "text": "How would you rate your investing knowledge?",
        "helper_text": "Self-assessed familiarity with equities, ETFs, derivatives.",
        "choices_json": _enum_choices(
            [
                ("novice", "Novice — just starting"),
                ("intermediate", "Intermediate — comfortable with stocks/ETFs"),
                ("advanced", "Advanced — derivatives, hedging, factor investing"),
                ("expert", "Expert — professional or near-professional"),
            ]
        ),
    },
    {
        "code": "K_02_YEARS",
        "step": 2,
        "order_in_step": 2,
        "dimension": "knowledge",
        "text": "How many years have you been investing your own money?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("0", "Less than 1 year"),
                ("3", "1–3 years"),
                ("7", "3–7 years"),
                ("15", "More than 7 years"),
            ]
        ),
    },
    {
        "code": "K_03_INSTRUMENTS",
        "step": 2,
        "order_in_step": 3,
        "dimension": "knowledge",
        "text": "Which instruments have you traded in the last 5 years?",
        "helper_text": "Select all that apply.",
        "choices_json": _multi_choices(
            [
                ("equities", "Individual stocks"),
                ("etfs", "ETFs / mutual funds"),
                ("options", "Options"),
                ("futures", "Futures"),
                ("crypto", "Crypto"),
                ("bonds", "Bonds"),
            ]
        ),
    },
    {
        "code": "K_04_RESEARCH",
        "step": 2,
        "order_in_step": 4,
        "dimension": "knowledge",
        "text": "Do you read primary financial research (earnings reports, 10-Ks)?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("never", "Never"),
                ("occasionally", "Occasionally"),
                ("regularly", "Regularly"),
                ("professionally", "Professionally"),
            ]
        ),
    },
    # ── Step 3: Financial situation (MiFID II §2) — bands only
    {
        "code": "F_01_INVESTABLE",
        "step": 3,
        "order_in_step": 1,
        "dimension": "financial",
        "text": "What amount are you planning to invest through this platform?",
        "helper_text": "Approximate band only; we never ask for exact figures.",
        "choices_json": _enum_choices(
            [
                ("lt_10k", "Less than $10,000"),
                ("10k_50k", "$10,000 – $50,000"),
                ("50k_250k", "$50,000 – $250,000"),
                ("250k_1m", "$250,000 – $1,000,000"),
                ("gt_1m", "More than $1,000,000"),
            ]
        ),
    },
    {
        "code": "F_02_INCOME",
        "step": 3,
        "order_in_step": 2,
        "dimension": "financial",
        "text": "What is your approximate annual income (before tax)?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("lt_50k", "Less than $50,000"),
                ("50k_150k", "$50,000 – $150,000"),
                ("150k_500k", "$150,000 – $500,000"),
                ("gt_500k", "More than $500,000"),
            ]
        ),
    },
    {
        "code": "F_03_NET_WORTH",
        "step": 3,
        "order_in_step": 3,
        "dimension": "financial",
        "text": "What is your approximate liquid net worth?",
        "helper_text": "Excluding primary residence.",
        "choices_json": _enum_choices(
            [
                ("lt_100k", "Less than $100,000"),
                ("100k_500k", "$100,000 – $500,000"),
                ("500k_2m", "$500,000 – $2,000,000"),
                ("gt_2m", "More than $2,000,000"),
            ]
        ),
    },
    {
        "code": "F_04_DEPENDENCY",
        "step": 3,
        "order_in_step": 4,
        "dimension": "financial",
        "text": "If this investment lost 30% of its value, would your lifestyle be affected?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("severely", "Severely — it would force major changes"),
                ("noticeably", "Noticeably — uncomfortable but manageable"),
                ("slightly", "Slightly — minor adjustment"),
                ("not_at_all", "Not at all — it's discretionary capital"),
            ]
        ),
    },
    # ── Step 4: Risk tolerance — 8 distilled Grable-Lytton items (scored 1..4)
    {
        "code": "R_01_VOL_COMFORT",
        "step": 4,
        "order_in_step": 1,
        "dimension": "risk",
        "text": "How comfortable are you watching your portfolio swing 10% in a month?",
        "helper_text": "Source: Grable-Lytton 1999, item 5 family.",
        "choices_json": _gl_choices(
            [
                "Very uncomfortable",
                "Somewhat uncomfortable",
                "Somewhat comfortable",
                "Very comfortable",
            ]
        ),
    },
    {
        "code": "R_02_LOSS_REACTION",
        "step": 4,
        "order_in_step": 2,
        "dimension": "risk",
        "text": "If your portfolio dropped 20% in a year, what would you most likely do?",
        "helper_text": None,
        "choices_json": _gl_choices(
            [
                "Sell everything",
                "Sell some to reduce risk",
                "Hold and wait it out",
                "Buy more at lower prices",
            ]
        ),
    },
    {
        "code": "R_03_TRADEOFF",
        "step": 4,
        "order_in_step": 3,
        "dimension": "risk",
        "text": "Which best describes your return-vs-risk preference?",
        "helper_text": None,
        "choices_json": _gl_choices(
            [
                "Protect capital first, modest returns",
                "Mostly stable, accept some fluctuation",
                "Moderate growth, accept noticeable swings",
                "Maximize long-term growth, accept large swings",
            ]
        ),
    },
    {
        "code": "R_04_GAMBLE_GUARANTEE",
        "step": 4,
        "order_in_step": 4,
        "dimension": "risk",
        "text": "Would you take a guaranteed $1,000 over a 50/50 chance at $2,500?",
        "helper_text": "Source: Grable-Lytton 1999, certainty equivalent item.",
        "choices_json": _gl_choices(
            [
                "Always take the guarantee",
                "Usually take the guarantee",
                "Usually take the gamble",
                "Always take the gamble",
            ]
        ),
    },
    {
        "code": "R_05_INHERITANCE",
        "step": 4,
        "order_in_step": 5,
        "dimension": "risk",
        "text": "If you inherited $100,000, how would you most likely invest it?",
        "helper_text": None,
        "choices_json": _gl_choices(
            [
                "Savings account / money market",
                "Mostly bonds, some stocks",
                "Balanced stocks + bonds",
                "Mostly stocks, including growth names",
            ]
        ),
    },
    {
        "code": "R_06_FRIEND_TIP",
        "step": 4,
        "order_in_step": 6,
        "dimension": "risk",
        "text": "A friend gives you a speculative stock tip with 50/50 odds of tripling or losing half. How much of your investable amount would you put in?",
        "helper_text": None,
        "choices_json": _gl_choices(
            [
                "Nothing",
                "Less than 5%",
                "5–15%",
                "More than 15%",
            ]
        ),
    },
    {
        "code": "R_07_FAMILIARITY",
        "step": 4,
        "order_in_step": 7,
        "dimension": "risk",
        "text": "How familiar are you with managing financial risk?",
        "helper_text": None,
        "choices_json": _gl_choices(
            [
                "Not at all familiar",
                "Somewhat familiar",
                "Familiar",
                "Very familiar",
            ]
        ),
    },
    {
        "code": "R_08_DRAWDOWN_TOLERANCE",
        "step": 4,
        "order_in_step": 8,
        "dimension": "risk",
        "text": "What is the largest drawdown you could endure without losing sleep?",
        "helper_text": "A drawdown is the peak-to-trough decline.",
        "choices_json": _gl_choices(
            [
                "Up to 5%",
                "Up to 15%",
                "Up to 25%",
                "More than 25%",
            ]
        ),
    },
    # ── Step 5: Investment objectives
    {
        "code": "O_01_HORIZON",
        "step": 5,
        "order_in_step": 1,
        "dimension": "objectives",
        "text": "When do you expect to need most of this money back?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("lt_1y", "Within 1 year"),
                ("1y_3y", "1–3 years"),
                ("3y_5y", "3–5 years"),
                ("5y_10y", "5–10 years"),
                ("gt_10y", "More than 10 years"),
            ]
        ),
    },
    {
        "code": "O_02_PRIMARY_GOAL",
        "step": 5,
        "order_in_step": 2,
        "dimension": "objectives",
        "text": "What is the primary purpose of this portfolio?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("preservation", "Preserve capital"),
                ("income", "Generate income"),
                ("growth", "Grow capital steadily"),
                ("aggressive_growth", "Maximize long-term growth"),
            ]
        ),
    },
    {
        "code": "O_03_MAX_DD",
        "step": 5,
        "order_in_step": 3,
        "dimension": "objectives",
        "text": "What maximum drawdown should the system never exceed?",
        "helper_text": "We will cap recommendations to honor this constraint.",
        "choices_json": _enum_choices(
            [
                ("5", "5%"),
                ("15", "15%"),
                ("25", "25%"),
                ("40", "40%"),
            ]
        ),
    },
    # ── Step 6: Universe & sector preferences
    {
        "code": "U_01_REGION",
        "step": 6,
        "order_in_step": 1,
        "dimension": "universe",
        "text": "Which region do you want exposure to?",
        "helper_text": None,
        "choices_json": _enum_choices(
            [
                ("us", "US only"),
                ("eu", "EU only"),
                ("global", "Global"),
            ]
        ),
    },
    {
        "code": "U_02_SECTOR_WHITELIST",
        "step": 6,
        "order_in_step": 2,
        "dimension": "universe",
        "text": "Any sectors you want to focus on?",
        "helper_text": "Multi-select. Leave empty for no preference.",
        "choices_json": _multi_choices(
            [
                ("Technology", "Technology"),
                ("Healthcare", "Healthcare"),
                ("Financials", "Financials"),
                ("Energy", "Energy"),
                ("Consumer Discretionary", "Consumer Discretionary"),
                ("Consumer Staples", "Consumer Staples"),
                ("Industrials", "Industrials"),
                ("Materials", "Materials"),
                ("Utilities", "Utilities"),
                ("Real Estate", "Real Estate"),
                ("Communication Services", "Communication Services"),
            ]
        ),
        "is_required": False,
    },
    {
        "code": "U_03_SECTOR_BLACKLIST",
        "step": 6,
        "order_in_step": 3,
        "dimension": "universe",
        "text": "Any sectors you want to exclude?",
        "helper_text": "Multi-select. Common: tobacco, defense, fossil fuels.",
        "choices_json": _multi_choices(
            [
                ("Technology", "Technology"),
                ("Healthcare", "Healthcare"),
                ("Financials", "Financials"),
                ("Energy", "Energy"),
                ("Consumer Discretionary", "Consumer Discretionary"),
                ("Consumer Staples", "Consumer Staples"),
                ("Industrials", "Industrials"),
                ("Materials", "Materials"),
                ("Utilities", "Utilities"),
                ("Real Estate", "Real Estate"),
                ("Communication Services", "Communication Services"),
            ]
        ),
        "is_required": False,
    },
    {
        "code": "U_04_LEVERAGE",
        "step": 6,
        "order_in_step": 4,
        "dimension": "universe",
        "text": "Allow leveraged or inverse instruments?",
        "helper_text": "Most investors should answer 'No'.",
        "choices_json": _enum_choices(
            [
                ("no", "No, exclude them"),
                ("yes", "Yes, allow"),
            ]
        ),
    },
    # ── Step 7: Operational preferences
    {
        "code": "P_01_CURRENCY",
        "step": 7,
        "order_in_step": 1,
        "dimension": "operational",
        "text": "Your base currency for reporting?",
        "helper_text": "All P&L and valuations will be shown in this currency.",
        "choices_json": _enum_choices(
            [
                ("USD", "US Dollar (USD)"),
                ("EUR", "Euro (EUR)"),
                ("ILS", "Israeli Shekel (ILS)"),
                ("GBP", "British Pound (GBP)"),
            ]
        ),
    },
    {
        "code": "P_02_FREQUENCY",
        "step": 7,
        "order_in_step": 2,
        "dimension": "operational",
        "text": "How often do you want to act on recommendations?",
        "helper_text": "Drives the recommendation cadence.",
        "choices_json": _enum_choices(
            [
                ("monthly", "Monthly"),
                ("weekly", "Weekly"),
                ("daily", "Daily"),
            ]
        ),
    },
    {
        "code": "P_03_NOTIFICATIONS",
        "step": 7,
        "order_in_step": 3,
        "dimension": "operational",
        "text": "When should we notify you?",
        "helper_text": "You can change this later.",
        "choices_json": _enum_choices(
            [
                ("all", "Every new recommendation"),
                ("important", "Only high-confidence or breach events"),
                ("none", "Don't notify me — I'll check manually"),
            ]
        ),
    },
]


async def seed() -> dict[str, int]:
    """Insert any questions whose code is not yet present.

    Returns counts: ``{"inserted": N, "skipped": M, "total_now": T}``.
    """
    inserted = 0
    skipped = 0
    async with async_session_factory() as db:
        for q in QUESTIONS:
            exists = (
                await db.execute(
                    select(ProfileQuestion).where(ProfileQuestion.code == q["code"])
                )
            ).scalar_one_or_none()
            if exists is not None:
                skipped += 1
                continue
            db.add(
                ProfileQuestion(
                    code=q["code"],
                    step=q["step"],
                    order_in_step=q["order_in_step"],
                    dimension=q["dimension"],
                    text=q["text"],
                    helper_text=q.get("helper_text"),
                    choices_json=q["choices_json"],
                    is_required=q.get("is_required", True),
                    is_active=True,
                )
            )
            inserted += 1
        await db.commit()

        total_now = (
            await db.execute(select(ProfileQuestion))
        ).scalars().all()
        total = len(total_now)

    return {"inserted": inserted, "skipped": skipped, "total_now": total}


def main() -> None:
    result = asyncio.run(seed())
    print(
        f"profile_questions: inserted={result['inserted']} "
        f"skipped={result['skipped']} total_now={result['total_now']}"
    )


if __name__ == "__main__":
    main()
