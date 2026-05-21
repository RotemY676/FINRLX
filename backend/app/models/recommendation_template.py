"""Phase TPL-1 — pre-made recommendation templates.

A template is a saved InvestorProfile skeleton (risk bucket, horizon,
sector tilt, currency, cadence) plus a few presentation fields (name,
description, badge). Users can:

* preview the template at `/templates`
* "Apply" it — which routes them to the wizard's edit page pre-filled
  with the template's settings (TPL-3 work).

Seed templates are loaded once via ``scripts.seed_recommendation_templates``.
Users (in a later admin sub-phase) can author their own templates with
``is_seed=False``.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, gen_uuid

# Re-exported for cross-module use (avoid string typos)
TEMPLATE_KEYS = (
    "capital_preservation",
    "balanced_growth",
    "long_term_growth",
    "tech_growth",
    "income_focus",
)


class RecommendationTemplate(Base, TimestampMixin):
    """Pre-made (or user-authored) recommendation template."""

    __tablename__ = "recommendation_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    badge: Mapped[str] = mapped_column(String(40), nullable=False)

    # Profile-skeleton fields (mirror InvestorProfile)
    risk_bucket: Mapped[str] = mapped_column(String(40), nullable=False)
    horizon_band: Mapped[str] = mapped_column(String(20), nullable=False)
    primary_goal: Mapped[str] = mapped_column(String(40), nullable=False)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)
    sector_whitelist_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="[]"
    )
    sector_blacklist_json: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="[]"
    )
    exclude_leverage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    trading_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )
    region_preference: Mapped[str] = mapped_column(
        String(10), nullable=False, default="global"
    )

    is_seed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36))

    # For the templates list UI: a short label like "60/40" or "95/5".
    allocation_summary: Mapped[str | None] = mapped_column(String(40))

    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
