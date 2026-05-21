"""Phase W-2 — investor profile request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ── Question catalog ─────────────────────────────────────────────────


class ProfileQuestionChoice(BaseModel):
    value: str
    label: str
    score: int | None = None


class ProfileQuestionResponse(BaseModel):
    code: str
    step: int
    order_in_step: int
    dimension: str
    text: str
    helper_text: str | None = None
    choices: list[ProfileQuestionChoice]
    is_required: bool
    is_active: bool


class ProfileStepResponse(BaseModel):
    step: int
    label: str
    dimension_hint: str
    questions: list[ProfileQuestionResponse]


# ── Profile read/write ───────────────────────────────────────────────


class InvestorProfileResponse(BaseModel):
    id: str
    user_id: str
    version: int
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
    completed_at: datetime
    created_at: datetime
    updated_at: datetime


class ProfileMeResponse(BaseModel):
    has_profile: bool
    profile: InvestorProfileResponse | None = None


class InvestorProfileSubmit(BaseModel):
    """Wizard submission. ``answers`` is a free-form dict keyed by question code.

    Step-4 (risk) answers must be the chosen choice's ``value`` field as a
    string; the scorer looks up the matching score in ``choices_json``.

    Multi-select questions (e.g. K_03 instruments, U_02 / U_03 sectors)
    submit a list of values; everything else submits a single string.
    """

    answers: dict[str, str | list[str]] = Field(
        default_factory=dict,
        description="Map of question code -> selected value (or list for multi-select)",
    )
    change_summary: str | None = Field(
        default=None, max_length=500, description="Optional note explaining the change"
    )


class ProfileRevisionResponse(BaseModel):
    id: str
    profile_id: str
    user_id: str
    version: int
    change_summary: str | None
    created_at: datetime
