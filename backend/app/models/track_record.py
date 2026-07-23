"""Prospective stance observations (phase 7).

The market survey found this the one asset that cannot be bought back later:
a forward-scored record accumulates only in wall-clock time, so capture starts
now even though the reporting surface is thin at n=0.

What this is NOT: a backtest. Every row is written when a stance was actually
served, at the price that was actually current, and scored later against the
price that actually occurred. Nothing is reconstructed after the fact — which
is precisely what makes it evidence a backtest can never be.
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid


class StanceObservation(Base):
    """One stance, recorded when served and scored once its horizon matures."""

    __tablename__ = "stance_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # What was claimed, at the moment it was claimed.
    stance: Mapped[str] = mapped_column(String(24), nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    avg_confidence: Mapped[float | None] = mapped_column(Float)
    uncertainty_tier: Mapped[str | None] = mapped_column(String(16))
    config_version: Mapped[str | None] = mapped_column(String(64))

    # The market as it stood when the claim was made.
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    observed_bar_date: Mapped[date] = mapped_column(Date, nullable=False)
    observed_close: Mapped[float] = mapped_column(Float, nullable=False)

    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, default=21)

    # Filled in only once the horizon has actually elapsed. NULL means
    # "not yet knowable" — never zero, which would read as a flat outcome.
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome_bar_date: Mapped[date | None] = mapped_column(Date)
    outcome_close: Mapped[float | None] = mapped_column(Float)
    realized_return: Mapped[float | None] = mapped_column(Float)
