"""Phase FX-1 — FX rate persistence + conversion.

Bridges the Frankfurter adapter and the ``fx_rates`` table. Conversions
follow a defined fallback chain so the caller never gets a confusing
``None``:

  1. exact (base, quote, date) hit → use it
  2. latest (base, quote) row ≤ date in cache → use it (stale flag set
     in caller-side via fx_age_days helper if needed)
  3. cross-rate via USD: convert base→USD then USD→quote
  4. same currency → 1.0
  5. raise ``FxConversionError`` if every option fails

``refresh_rates_for_today()`` is the once-per-day job that fetches
all configured (base, quote) pairs and writes new rows. We never
overwrite a historical row — each (date, base, quote) row is immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from datetime import date as DateType

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import gen_uuid
from app.models.fx import FxRate
from app.services.data_providers.frankfurter_provider import (
    SUPPORTED_BASE_QUOTES,
    FrankfurterError,
    fetch_rates,
)

# All pairwise (base, quote) we fetch on the daily refresh — small set
# because we cross-rate the rest via USD.
DEFAULT_BASE_CURRENCIES = ("USD", "EUR", "ILS", "GBP")


class FxConversionError(RuntimeError):
    """Raised when no rate can be resolved through any fallback."""


@dataclass(frozen=True)
class FxConversion:
    amount_in: float
    amount_out: float
    from_currency: str
    to_currency: str
    rate: float
    rate_date: DateType
    is_fallback: bool
    fallback_reason: str | None


class FxService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Persistence ──────────────────────────────────────────────────

    async def upsert_rate(
        self,
        base: str,
        quote: str,
        rate_date: DateType,
        rate: float,
        source: str = "frankfurter",
    ) -> FxRate:
        existing = (
            await self.db.execute(
                select(FxRate)
                .where(FxRate.base_currency == base)
                .where(FxRate.quote_currency == quote)
                .where(FxRate.rate_date == rate_date)
                .where(FxRate.source == source)
            )
        ).scalar_one_or_none()
        if existing is not None:
            # Historical rows are immutable. We tolerate idempotent re-fetch
            # of today's row (same value) but never silently change history.
            if abs(existing.rate - rate) > 1e-9:
                # Refresh of today's value (ECB publishes once; if a
                # refresh sees a different value it's because the date
                # has rolled over and we should write a new row for the
                # new date, not mutate). Skip the mutation.
                return existing
            return existing

        row = FxRate(
            id=gen_uuid(),
            base_currency=base,
            quote_currency=quote,
            rate_date=rate_date,
            rate=rate,
            source=source,
        )
        self.db.add(row)
        return row

    async def _latest_rate_row(
        self, base: str, quote: str, on_or_before: DateType
    ) -> FxRate | None:
        return (
            await self.db.execute(
                select(FxRate)
                .where(FxRate.base_currency == base)
                .where(FxRate.quote_currency == quote)
                .where(FxRate.rate_date <= on_or_before)
                .order_by(FxRate.rate_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    # ── Conversion ───────────────────────────────────────────────────

    async def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        on_date: DateType | None = None,
    ) -> FxConversion:
        """Convert ``amount`` from ``from_currency`` to ``to_currency``.

        ``on_date`` defaults to today (UTC).
        """
        if from_currency == to_currency:
            return FxConversion(
                amount_in=amount,
                amount_out=amount,
                from_currency=from_currency,
                to_currency=to_currency,
                rate=1.0,
                rate_date=on_date or datetime.now(UTC).date(),
                is_fallback=False,
                fallback_reason=None,
            )

        if on_date is None:
            on_date = datetime.now(UTC).date()

        # 1) Direct
        direct = await self._latest_rate_row(from_currency, to_currency, on_date)
        if direct is not None:
            is_fallback = direct.rate_date != on_date
            return FxConversion(
                amount_in=amount,
                amount_out=amount * direct.rate,
                from_currency=from_currency,
                to_currency=to_currency,
                rate=direct.rate,
                rate_date=direct.rate_date,
                is_fallback=is_fallback,
                fallback_reason=(
                    f"using {direct.rate_date.isoformat()} (no row for {on_date.isoformat()})"
                    if is_fallback
                    else None
                ),
            )

        # 2) Cross-rate via USD
        if from_currency != "USD" and to_currency != "USD":
            leg1 = await self._latest_rate_row(from_currency, "USD", on_date)
            leg2 = await self._latest_rate_row("USD", to_currency, on_date)
            if leg1 is not None and leg2 is not None:
                rate = leg1.rate * leg2.rate
                used_date = min(leg1.rate_date, leg2.rate_date)
                return FxConversion(
                    amount_in=amount,
                    amount_out=amount * rate,
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    rate_date=used_date,
                    is_fallback=True,
                    fallback_reason="cross-rated via USD",
                )

        # 3) Try inverse direct: 1/quote→base
        inverse = await self._latest_rate_row(to_currency, from_currency, on_date)
        if inverse is not None and inverse.rate > 0:
            implied = 1.0 / inverse.rate
            return FxConversion(
                amount_in=amount,
                amount_out=amount * implied,
                from_currency=from_currency,
                to_currency=to_currency,
                rate=implied,
                rate_date=inverse.rate_date,
                is_fallback=True,
                fallback_reason="inverted-from-quote",
            )

        raise FxConversionError(
            f"no path to convert {from_currency} -> {to_currency} on {on_date.isoformat()}"
        )

    # ── Daily refresh ────────────────────────────────────────────────

    async def refresh_rates_for_today(
        self,
        bases: tuple[str, ...] = DEFAULT_BASE_CURRENCIES,
        quotes: tuple[str, ...] = DEFAULT_BASE_CURRENCIES,
        *,
        rate_date: DateType | None = None,
    ) -> dict[str, int]:
        """Fetch every (base, quote) pair from Frankfurter and write rows.

        Returns counts: ``{"fetched": N, "errors": M}``. Per-base errors
        don't abort the whole refresh — we partial-write what we can.
        """
        target_date = rate_date or datetime.now(UTC).date()
        fetched = 0
        errors = 0

        for base in bases:
            if base not in SUPPORTED_BASE_QUOTES:
                errors += 1
                continue
            wanted = [q for q in quotes if q != base and q in SUPPORTED_BASE_QUOTES]
            try:
                rates = await fetch_rates(base, wanted, target_date)
            except FrankfurterError:
                errors += 1
                continue
            for q, r in rates.items():
                await self.upsert_rate(base, q, target_date, r)
                fetched += 1

        await self.db.commit()
        return {"fetched": fetched, "errors": errors}
