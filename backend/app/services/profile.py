"""Phase W-2 — investor profile scoring + persistence service.

Pure functions (`score_answers`, `bucket_from_score`) are testable
without a database; `ProfileService` handles persistence (one current
row per user + append-only revision history).

Risk-bucket thresholds (derived from Vanguard/Fidelity model-portfolio
breakpoints, divided into 5 equal-width bands across the 8-32 Grable-
Lytton subset range):

  8-12  conservative
  13-17 moderate_conservative
  18-22 moderate
  23-27 moderate_aggressive
  28-32 aggressive
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import (
    HORIZON_BANDS,
    INCOME_BANDS,
    INVESTABLE_BANDS,
    KNOWLEDGE_LEVELS,
    NET_WORTH_BANDS,
    PRIMARY_GOALS,
    REGION_PREFERENCES,
    SUPPORTED_BASE_CURRENCIES,
    TRADING_FREQUENCIES,
    InvestorProfile,
    InvestorProfileRevision,
    ProfileQuestion,
)

RISK_ITEM_PREFIX = "R_"  # all step-4 question codes start with R_
MIN_RISK_SCORE = 8
MAX_RISK_SCORE = 32

# (lower_inclusive, upper_inclusive, bucket_label)
RISK_BUCKET_BANDS: tuple[tuple[int, int, str], ...] = (
    (8, 12, "conservative"),
    (13, 17, "moderate_conservative"),
    (18, 22, "moderate"),
    (23, 27, "moderate_aggressive"),
    (28, 32, "aggressive"),
)


class ProfileValidationError(ValueError):
    """Raised when wizard answers fail validation (missing/invalid)."""


@dataclass(frozen=True)
class ScoredProfile:
    """Output of `score_answers`: ready to persist or echo to the client."""

    risk_score: int
    risk_bucket: str
    horizon_band: str
    primary_goal: str
    max_drawdown_pct: float
    knowledge_level: str
    years_investing: int
    instruments_traded: list[str]
    investable_amount_band: str
    income_band: str
    liquid_net_worth_band: str
    sector_whitelist: list[str]
    sector_blacklist: list[str]
    region_preference: str
    exclude_leverage: bool
    base_currency: str
    trading_frequency: str


# ── Pure scoring ─────────────────────────────────────────────────────


def bucket_from_score(risk_score: int) -> str:
    """Return the risk bucket label for a score in [8, 32]."""
    if not MIN_RISK_SCORE <= risk_score <= MAX_RISK_SCORE:
        raise ProfileValidationError(
            f"risk_score {risk_score} outside [{MIN_RISK_SCORE}, {MAX_RISK_SCORE}]"
        )
    for low, high, label in RISK_BUCKET_BANDS:
        if low <= risk_score <= high:
            return label
    # Unreachable given the range check above, but mypy wants it.
    raise ProfileValidationError(f"no bucket matched risk_score={risk_score}")


def _require(answers: dict[str, str | list[str]], code: str) -> str | list[str]:
    if code not in answers:
        raise ProfileValidationError(f"missing required answer: {code}")
    value = answers[code]
    if isinstance(value, str) and not value:
        raise ProfileValidationError(f"empty answer: {code}")
    return value


def _require_str(answers: dict[str, str | list[str]], code: str) -> str:
    value = _require(answers, code)
    if not isinstance(value, str):
        raise ProfileValidationError(f"{code} must be a single value, got list")
    return value


def _require_list(answers: dict[str, str | list[str]], code: str) -> list[str]:
    if code not in answers:
        return []
    value = answers[code]
    if isinstance(value, str):
        return [value] if value else []
    return list(value)


def _validate_enum(field: str, value: str, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise ProfileValidationError(
            f"{field}={value!r} is not one of {list(allowed)}"
        )
    return value


def score_answers(
    answers: dict[str, str | list[str]],
    risk_question_choices: dict[str, list[dict]],
) -> ScoredProfile:
    """Score raw wizard answers into a `ScoredProfile`.

    `risk_question_choices` maps a step-4 question code to its parsed
    `choices_json` (a list of `{value, label, score}` dicts). This is
    passed in rather than queried inside so the function stays pure +
    cheap to test.
    """
    # ── Risk score (step 4)
    risk_score = 0
    for code, choices in risk_question_choices.items():
        if not code.startswith(RISK_ITEM_PREFIX):
            continue
        chosen_value = _require_str(answers, code)
        match = next((c for c in choices if str(c.get("value")) == chosen_value), None)
        if match is None:
            raise ProfileValidationError(
                f"{code}={chosen_value!r} is not a valid choice"
            )
        score = match.get("score")
        if not isinstance(score, int) or not 1 <= score <= 4:
            raise ProfileValidationError(
                f"{code} choice {chosen_value!r} has invalid score {score!r}"
            )
        risk_score += score

    if risk_score == 0:
        raise ProfileValidationError("no risk-step answers were provided")

    if not MIN_RISK_SCORE <= risk_score <= MAX_RISK_SCORE:
        raise ProfileValidationError(
            f"computed risk_score {risk_score} outside expected range"
        )
    risk_bucket = bucket_from_score(risk_score)

    # ── Knowledge & experience (step 2)
    knowledge_level = _validate_enum(
        "K_01_LEVEL", _require_str(answers, "K_01_LEVEL"), KNOWLEDGE_LEVELS
    )
    years_investing_raw = _require_str(answers, "K_02_YEARS")
    try:
        years_investing = int(years_investing_raw)
    except ValueError as exc:
        raise ProfileValidationError(
            f"K_02_YEARS={years_investing_raw!r} is not an integer"
        ) from exc
    instruments_traded = _require_list(answers, "K_03_INSTRUMENTS")

    # ── Financial situation (step 3)
    investable_amount_band = _validate_enum(
        "F_01_INVESTABLE",
        _require_str(answers, "F_01_INVESTABLE"),
        INVESTABLE_BANDS,
    )
    income_band = _validate_enum(
        "F_02_INCOME", _require_str(answers, "F_02_INCOME"), INCOME_BANDS
    )
    liquid_net_worth_band = _validate_enum(
        "F_03_NET_WORTH",
        _require_str(answers, "F_03_NET_WORTH"),
        NET_WORTH_BANDS,
    )

    # ── Objectives (step 5)
    horizon_band = _validate_enum(
        "O_01_HORIZON", _require_str(answers, "O_01_HORIZON"), HORIZON_BANDS
    )
    primary_goal = _validate_enum(
        "O_02_PRIMARY_GOAL",
        _require_str(answers, "O_02_PRIMARY_GOAL"),
        PRIMARY_GOALS,
    )
    max_dd_raw = _require_str(answers, "O_03_MAX_DD")
    try:
        max_drawdown_pct = float(max_dd_raw)
    except ValueError as exc:
        raise ProfileValidationError(
            f"O_03_MAX_DD={max_dd_raw!r} is not a number"
        ) from exc
    if not 0 < max_drawdown_pct <= 100:
        raise ProfileValidationError(
            f"O_03_MAX_DD must be in (0, 100], got {max_drawdown_pct}"
        )

    # ── Universe (step 6)
    region_preference = _validate_enum(
        "U_01_REGION", _require_str(answers, "U_01_REGION"), REGION_PREFERENCES
    )
    sector_whitelist = _require_list(answers, "U_02_SECTOR_WHITELIST")
    sector_blacklist = _require_list(answers, "U_03_SECTOR_BLACKLIST")
    leverage_choice = _require_str(answers, "U_04_LEVERAGE")
    if leverage_choice not in {"yes", "no"}:
        raise ProfileValidationError(
            f"U_04_LEVERAGE must be 'yes' or 'no', got {leverage_choice!r}"
        )
    exclude_leverage = leverage_choice == "no"

    # ── Operational (step 7)
    base_currency = _validate_enum(
        "P_01_CURRENCY",
        _require_str(answers, "P_01_CURRENCY"),
        SUPPORTED_BASE_CURRENCIES,
    )
    trading_frequency = _validate_enum(
        "P_02_FREQUENCY",
        _require_str(answers, "P_02_FREQUENCY"),
        TRADING_FREQUENCIES,
    )

    return ScoredProfile(
        risk_score=risk_score,
        risk_bucket=risk_bucket,
        horizon_band=horizon_band,
        primary_goal=primary_goal,
        max_drawdown_pct=max_drawdown_pct,
        knowledge_level=knowledge_level,
        years_investing=years_investing,
        instruments_traded=instruments_traded,
        investable_amount_band=investable_amount_band,
        income_band=income_band,
        liquid_net_worth_band=liquid_net_worth_band,
        sector_whitelist=sector_whitelist,
        sector_blacklist=sector_blacklist,
        region_preference=region_preference,
        exclude_leverage=exclude_leverage,
        base_currency=base_currency,
        trading_frequency=trading_frequency,
    )


# ── Persistence ──────────────────────────────────────────────────────


class ProfileService:
    """Persistence + revision handling.

    `upsert` writes the new profile and an accompanying revision row in
    a single transaction. The caller (API endpoint) controls the commit.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_risk_question_choices(self) -> dict[str, list[dict]]:
        """Read step-4 questions and parse their choices_json."""
        rows = (
            await self.db.execute(
                select(ProfileQuestion).where(ProfileQuestion.step == 4)
            )
        ).scalars().all()
        return {q.code: json.loads(q.choices_json) for q in rows}

    async def get_current(self, user_id: str) -> InvestorProfile | None:
        return (
            await self.db.execute(
                select(InvestorProfile).where(InvestorProfile.user_id == user_id)
            )
        ).scalar_one_or_none()

    async def list_revisions(self, user_id: str) -> list[InvestorProfileRevision]:
        return list(
            (
                await self.db.execute(
                    select(InvestorProfileRevision)
                    .where(InvestorProfileRevision.user_id == user_id)
                    .order_by(InvestorProfileRevision.version.desc())
                )
            )
            .scalars()
            .all()
        )

    async def upsert(
        self,
        user_id: str,
        scored: ScoredProfile,
        raw_answers: dict[str, str | list[str]],
        change_summary: str | None = None,
    ) -> InvestorProfile:
        """Insert or update the current profile, and append a revision row."""
        current = await self.get_current(user_id)
        next_version = (current.version + 1) if current else 1

        if current is None:
            profile = InvestorProfile(
                user_id=user_id,
                version=next_version,
                risk_score=scored.risk_score,
                risk_bucket=scored.risk_bucket,
                horizon_band=scored.horizon_band,
                primary_goal=scored.primary_goal,
                max_drawdown_pct=scored.max_drawdown_pct,
                knowledge_level=scored.knowledge_level,
                years_investing=scored.years_investing,
                instruments_traded_json=json.dumps(scored.instruments_traded),
                investable_amount_band=scored.investable_amount_band,
                income_band=scored.income_band,
                liquid_net_worth_band=scored.liquid_net_worth_band,
                sector_whitelist_json=json.dumps(scored.sector_whitelist),
                sector_blacklist_json=json.dumps(scored.sector_blacklist),
                region_preference=scored.region_preference,
                exclude_leverage=scored.exclude_leverage,
                base_currency=scored.base_currency,
                trading_frequency=scored.trading_frequency,
                raw_answers_json=json.dumps(raw_answers, sort_keys=True),
            )
            self.db.add(profile)
        else:
            current.version = next_version
            current.risk_score = scored.risk_score
            current.risk_bucket = scored.risk_bucket
            current.horizon_band = scored.horizon_band
            current.primary_goal = scored.primary_goal
            current.max_drawdown_pct = scored.max_drawdown_pct
            current.knowledge_level = scored.knowledge_level
            current.years_investing = scored.years_investing
            current.instruments_traded_json = json.dumps(scored.instruments_traded)
            current.investable_amount_band = scored.investable_amount_band
            current.income_band = scored.income_band
            current.liquid_net_worth_band = scored.liquid_net_worth_band
            current.sector_whitelist_json = json.dumps(scored.sector_whitelist)
            current.sector_blacklist_json = json.dumps(scored.sector_blacklist)
            current.region_preference = scored.region_preference
            current.exclude_leverage = scored.exclude_leverage
            current.base_currency = scored.base_currency
            current.trading_frequency = scored.trading_frequency
            current.raw_answers_json = json.dumps(raw_answers, sort_keys=True)
            profile = current

        # Flush so the new/updated profile has an id available for the revision.
        await self.db.flush()

        revision = InvestorProfileRevision(
            profile_id=profile.id,
            user_id=user_id,
            version=next_version,
            snapshot_json=json.dumps(
                {
                    "scored": scored.__dict__,
                    "raw_answers": raw_answers,
                },
                sort_keys=True,
            ),
            change_summary=change_summary,
        )
        self.db.add(revision)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
