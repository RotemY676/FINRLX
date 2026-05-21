"""Phase W-1 — investor profile entities.

Three tables back the investor-profile wizard:

* `investor_profiles` — one current row per user (the active profile).
* `investor_profile_revisions` — append-only history of every change, so
  any Recommendation can reference the exact profile version that drove it.
* `profile_questions` — canonical catalog of wizard questions (text,
  choices, scoring map). Seeded once; not user-editable.

Methodology rationale (sources: Grable & Lytton 1999; ESMA MiFID II 2022
suitability guidelines; Morningstar/FinaMetrica risk→growth mapping):

* Risk score is an 8-item subset of the Grable-Lytton scale, each item
  scored 1-4, yielding raw 8-32. The 8 items were chosen for highest
  discriminating power per the 2014 retrospective.
* Three MiFID II dimensions (knowledge, financial situation, objectives)
  are stored as banded enums to avoid storing precise PII.
* Sector/region preferences feed Universe filters at recommendation time.
* `base_currency` drives the FX layer (Phase FX).

All JSON columns are stored as TEXT for SQLite + Postgres compat (same
pattern as `saved_views.filters_json`).
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid

RISK_BUCKETS = (
    "conservative",
    "moderate_conservative",
    "moderate",
    "moderate_aggressive",
    "aggressive",
)
HORIZON_BANDS = ("lt_1y", "1y_3y", "3y_5y", "5y_10y", "gt_10y")
PRIMARY_GOALS = ("preservation", "income", "growth", "aggressive_growth")
TRADING_FREQUENCIES = ("monthly", "weekly", "daily")
REGION_PREFERENCES = ("us", "eu", "global")
SUPPORTED_BASE_CURRENCIES = ("USD", "EUR", "ILS", "GBP")
KNOWLEDGE_LEVELS = ("novice", "intermediate", "advanced", "expert")
INVESTABLE_BANDS = ("lt_10k", "10k_50k", "50k_250k", "250k_1m", "gt_1m")
INCOME_BANDS = ("lt_50k", "50k_150k", "150k_500k", "gt_500k")
NET_WORTH_BANDS = ("lt_100k", "100k_500k", "500k_2m", "gt_2m")

PROFILE_DIMENSIONS = (
    "knowledge",
    "financial",
    "risk",
    "objectives",
    "universe",
    "operational",
)


class InvestorProfile(Base, TimestampMixin):
    """Current investor profile — one row per user.

    Insert-or-update semantics: writing a new profile bumps `version` and
    writes a fresh `InvestorProfileRevision`. The current row is always
    the latest snapshot.
    """

    __tablename__ = "investor_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Risk dimension
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_bucket: Mapped[str] = mapped_column(String(40), nullable=False)

    # Objectives
    horizon_band: Mapped[str] = mapped_column(String(20), nullable=False)
    primary_goal: Mapped[str] = mapped_column(String(40), nullable=False)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)

    # Knowledge & experience (MiFID II §1)
    knowledge_level: Mapped[str] = mapped_column(String(20), nullable=False)
    years_investing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    instruments_traded_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="[]"
    )

    # Financial situation (MiFID II §2) — bands only, no precise amounts
    investable_amount_band: Mapped[str] = mapped_column(String(20), nullable=False)
    income_band: Mapped[str] = mapped_column(String(20), nullable=False)
    liquid_net_worth_band: Mapped[str] = mapped_column(String(20), nullable=False)

    # Universe & sector preferences
    sector_whitelist_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="[]"
    )
    sector_blacklist_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="[]"
    )
    region_preference: Mapped[str] = mapped_column(
        String(10), nullable=False, default="global"
    )
    exclude_leverage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Operational
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    trading_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )

    # Full raw answers for audit / replay
    raw_answers_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="{}"
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InvestorProfileRevision(Base):
    """Append-only history of profile changes.

    Every InvestorProfile write produces a revision row. Recommendations
    reference (user_id, profile_version) so replay can reconstruct the
    exact suitability frame that drove a given recommendation.
    """

    __tablename__ = "investor_profile_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    profile_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ProfileQuestion(Base):
    """Canonical catalog of wizard questions.

    Seeded by `scripts/seed_profile_questions.py`. The frontend reads this
    list at runtime so question text + choices live in one place.
    """

    __tablename__ = "profile_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    order_in_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dimension: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    helper_text: Mapped[str | None] = mapped_column(Text)
    # choices_json: list of {value, label, score?} objects
    choices_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
