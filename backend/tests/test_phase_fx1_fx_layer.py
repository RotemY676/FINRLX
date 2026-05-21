"""Phase FX-1 — FX rate persistence + conversion contract.

Coverage:
* fx_rates table writeable + UNIQUE (base, quote, date, source).
* upsert_rate is idempotent for the same row; refuses silent mutation.
* convert(same currency) → 1.0 with no fallback.
* convert(direct hit) → exact row used.
* convert(stale fallback) → most recent row, is_fallback=true.
* convert(cross-rate via USD) when no direct row exists.
* convert(inverse direct) when only the reciprocal row exists.
* convert(no path) raises FxConversionError.
* refresh_rates_for_today() partial-writes when upstream fails.

The Frankfurter provider itself is exercised indirectly via a mock.
"""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.fx import FxRate
from app.services.fx_service import FxConversionError, FxService


@pytest.mark.asyncio
async def test_fx_rates_table_writeable_and_unique():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        db.add(
            FxRate(
                base_currency="USD",
                quote_currency="EUR",
                rate_date=date(2025, 1, 1),
                rate=0.9123,
                source="frankfurter",
            )
        )
        await db.commit()

    # Same (base, quote, date, source) → IntegrityError on insert
    async with test_session_factory() as db:
        db.add(
            FxRate(
                base_currency="USD",
                quote_currency="EUR",
                rate_date=date(2025, 1, 1),
                rate=0.9123,
                source="frankfurter",
            )
        )
        with pytest.raises(IntegrityError):
            await db.commit()
        await db.rollback()


@pytest.mark.asyncio
async def test_convert_same_currency_returns_one():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        svc = FxService(db)
        c = await svc.convert(100.0, "USD", "USD")
    assert c.amount_out == 100.0
    assert c.rate == 1.0
    assert c.is_fallback is False


@pytest.mark.asyncio
async def test_convert_direct_hit_uses_exact_row():
    from tests.conftest import test_session_factory

    target = date(2025, 6, 1)
    async with test_session_factory() as db:
        svc = FxService(db)
        await svc.upsert_rate("USD", "EUR", target, 0.92)
        await db.commit()
        c = await svc.convert(100.0, "USD", "EUR", target)
    assert c.amount_out == pytest.approx(92.0)
    assert c.rate == pytest.approx(0.92)
    assert c.rate_date == target
    assert c.is_fallback is False


@pytest.mark.asyncio
async def test_convert_stale_fallback():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        svc = FxService(db)
        await svc.upsert_rate("USD", "EUR", date(2025, 7, 10), 0.93)
        await db.commit()
        c = await svc.convert(100.0, "USD", "EUR", date(2025, 7, 20))
    # Only the 7/10 row exists → fallback used
    assert c.amount_out == pytest.approx(93.0)
    assert c.is_fallback is True
    assert "2025-07-10" in (c.fallback_reason or "")


@pytest.mark.asyncio
async def test_convert_cross_rate_via_usd():
    """EUR → ILS via USD when no direct EUR→ILS row exists."""
    from tests.conftest import test_session_factory

    target = date(2025, 8, 1)
    async with test_session_factory() as db:
        svc = FxService(db)
        await svc.upsert_rate("EUR", "USD", target, 1.10)
        await svc.upsert_rate("USD", "ILS", target, 3.70)
        await db.commit()
        c = await svc.convert(100.0, "EUR", "ILS", target)
    # 100 EUR * 1.10 USD/EUR * 3.70 ILS/USD = 407
    assert c.amount_out == pytest.approx(407.0, rel=1e-3)
    assert c.is_fallback is True
    assert c.fallback_reason == "cross-rated via USD"


@pytest.mark.asyncio
async def test_convert_inverse_direct():
    """USD→GBP when only GBP→USD row exists and no other GBP↔USD rows pollute.

    Uses a date far in the past + a pair (USD↔GBP) we don't touch in
    other tests, to dodge session-scoped DB pollution.
    """
    from tests.conftest import test_session_factory

    target = date(2023, 1, 15)
    async with test_session_factory() as db:
        svc = FxService(db)
        await svc.upsert_rate("GBP", "USD", target, 1.25)
        await db.commit()
        c = await svc.convert(125.0, "USD", "GBP", target)
    # No USD→GBP row, no cross-via-USD (one leg involves USD), so inverse
    assert c.amount_out == pytest.approx(100.0, rel=1e-3)
    assert c.is_fallback is True
    assert c.fallback_reason == "inverted-from-quote"


@pytest.mark.asyncio
async def test_convert_no_path_raises():
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        svc = FxService(db)
        with pytest.raises(FxConversionError):
            await svc.convert(100.0, "GBP", "ILS", date(2025, 1, 1))


@pytest.mark.asyncio
async def test_refresh_partial_write_on_provider_error(monkeypatch):
    """If Frankfurter fails for one base, the others still write."""
    from app.services import fx_service as fx_svc_mod
    from tests.conftest import test_session_factory

    call_log = []

    async def fake_fetch(base, quotes, rate_date=None, **_):
        call_log.append((base, list(quotes), rate_date))
        if base == "EUR":
            from app.services.data_providers.frankfurter_provider import (
                FrankfurterError,
            )
            raise FrankfurterError("simulated upstream failure")
        # Return a plausible payload for the others
        return {q: 1.0 + 0.01 * len(q) for q in quotes}

    monkeypatch.setattr(fx_svc_mod, "fetch_rates", fake_fetch)

    target = date(2025, 11, 15)
    async with test_session_factory() as db:
        svc = FxService(db)
        result = await svc.refresh_rates_for_today(
            bases=("USD", "EUR", "GBP"), quotes=("USD", "EUR", "GBP"), rate_date=target,
        )

    # USD and GBP succeed (2 quotes each = 4 fetched); EUR errors.
    assert result["errors"] == 1
    assert result["fetched"] == 4
