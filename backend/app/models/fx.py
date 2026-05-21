"""Phase FX-1 — foreign-exchange rate cache.

One row per ``(base, quote, rate_date, source)``. We always store rates
as ``1 base = N quote`` to make conversions explicit and avoid sign
confusion.

Source field tracks the provider (currently "frankfurter") so a future
provider switch can be done without renaming columns.
"""
from datetime import date as DateType
from datetime import datetime

from sqlalchemy import Date, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import gen_uuid


class FxRate(Base):
    __tablename__ = "fx_rates"
    __table_args__ = (
        UniqueConstraint(
            "base_currency", "quote_currency", "rate_date", "source",
            name="uq_fx_rates_base_quote_date_source",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    rate_date: Mapped[DateType] = mapped_column(Date, nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="frankfurter")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
