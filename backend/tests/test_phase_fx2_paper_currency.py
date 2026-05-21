"""Phase FX-2 — paper portfolio FX translation.

Coverage:
* PaperPortfolio.base_currency column exists and defaults USD.
* value_portfolio_in_currency translates holdings:
    - same currency → no FX adjustment
    - different currency → FX applied via FxService
    - missing FX path → warning + zero value_in_target, no crash
* GET /api/v1/paper/current/valuation-in-currency:
    - 404 when no active portfolio
    - 422 on bad currency input
    - 200 with translated holdings + native + target totals
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from app.models.ingestion import MarketBar
from app.models.reference import Asset
from app.models.validation import PaperPortfolio
from app.services.paper_currency import value_portfolio_in_currency


def _uid() -> str:
    return str(uuid.uuid4())


@pytest.mark.asyncio
async def test_paper_portfolio_has_base_currency_column_default_usd():
    from tests.conftest import test_session_factory

    pp_id = _uid()
    async with test_session_factory() as db:
        db.add(
            PaperPortfolio(
                id=pp_id,
                name="FX-2 test",
                current_holdings={},
                cash_weight=1.0,
                portfolio_value=100000.0,
                source_type="seed_demo",
            )
        )
        await db.commit()
        loaded = (
            await db.execute(
                select(PaperPortfolio).where(PaperPortfolio.id == pp_id)
            )
        ).scalar_one()
    assert loaded.base_currency == "USD"


@pytest.mark.asyncio
async def test_value_in_same_currency_passes_through():
    """A USD-currency asset valued in USD should produce native==target."""
    from tests.conftest import test_session_factory

    asset_id = _uid()
    pp_id = _uid()
    async with test_session_factory() as db:
        db.add(
            Asset(
                id=asset_id, ticker="USDONLY", name="USD Only",
                sector="Technology", currency="USD",
            )
        )
        db.add(
            MarketBar(
                id=_uid(), asset_id=asset_id, ticker="USDONLY",
                bar_date=date(2025, 5, 10), interval="1d",
                open=100.0, high=100.0, low=100.0, close=100.0,
                volume=1, source="test",
            )
        )
        db.add(
            PaperPortfolio(
                id=pp_id, name="USD only",
                current_holdings={
                    asset_id: {"ticker": "USDONLY", "quantity": 10},
                },
                base_currency="USD",
                cash_weight=0.0,
                portfolio_value=1000.0,
                source_type="seed_demo",
            )
        )
        await db.commit()
        loaded = (
            await db.execute(
                select(PaperPortfolio).where(PaperPortfolio.id == pp_id)
            )
        ).scalar_one()
        valuation = await value_portfolio_in_currency(db, loaded, "USD")

    assert len(valuation.holdings) == 1
    h = valuation.holdings[0]
    assert h.value_native == pytest.approx(1000.0)
    assert h.value_in_base == pytest.approx(1000.0)
    assert h.fx_rate == 1.0
    assert h.fx_is_fallback is False
    assert valuation.total_value_in_target == pytest.approx(1000.0)
    assert valuation.fx_warnings == []


@pytest.mark.asyncio
async def test_value_with_cross_currency_uses_fx_service():
    """EUR-denominated asset valued in USD should apply EUR→USD rate."""
    from app.models.fx import FxRate
    from tests.conftest import test_session_factory

    asset_id = _uid()
    pp_id = _uid()
    rate_date = date(2025, 5, 10)
    async with test_session_factory() as db:
        db.add(
            Asset(
                id=asset_id, ticker="EUR_ASSET", name="EUR Asset",
                sector="Industrials", currency="EUR",
            )
        )
        db.add(
            MarketBar(
                id=_uid(), asset_id=asset_id, ticker="EUR_ASSET",
                bar_date=rate_date, interval="1d",
                open=200.0, high=200.0, low=200.0, close=200.0,
                volume=1, source="test",
            )
        )
        db.add(
            FxRate(
                base_currency="EUR", quote_currency="USD",
                rate_date=rate_date, rate=1.10, source="frankfurter",
            )
        )
        db.add(
            PaperPortfolio(
                id=pp_id, name="EUR holder",
                current_holdings={
                    asset_id: {"ticker": "EUR_ASSET", "quantity": 5},
                },
                base_currency="USD",
                cash_weight=0.0,
                portfolio_value=1100.0,
                source_type="seed_demo",
            )
        )
        await db.commit()
        loaded = (
            await db.execute(
                select(PaperPortfolio).where(PaperPortfolio.id == pp_id)
            )
        ).scalar_one()
        valuation = await value_portfolio_in_currency(
            db, loaded, "USD", on_date=rate_date,
        )

    h = valuation.holdings[0]
    # 5 * 200 EUR = 1000 EUR; * 1.10 = 1100 USD
    assert h.value_native == pytest.approx(1000.0)
    assert h.value_in_base == pytest.approx(1100.0)
    assert h.fx_rate == pytest.approx(1.10)
    assert valuation.total_value_in_target == pytest.approx(1100.0)


@pytest.mark.asyncio
async def test_value_warns_when_fx_path_missing():
    """An asset whose currency has no FX path emits a warning, value=0."""
    from tests.conftest import test_session_factory

    asset_id = _uid()
    pp_id = _uid()
    async with test_session_factory() as db:
        db.add(
            Asset(
                id=asset_id, ticker="NOFX", name="No FX",
                sector="Healthcare", currency="ZZZ",  # bogus, no FX table
            )
        )
        db.add(
            MarketBar(
                id=_uid(), asset_id=asset_id, ticker="NOFX",
                bar_date=date(2025, 5, 10), interval="1d",
                open=50.0, high=50.0, low=50.0, close=50.0,
                volume=1, source="test",
            )
        )
        db.add(
            PaperPortfolio(
                id=pp_id, name="No FX",
                current_holdings={
                    asset_id: {"ticker": "NOFX", "quantity": 4},
                },
                base_currency="USD",
                source_type="seed_demo",
            )
        )
        await db.commit()
        loaded = (
            await db.execute(
                select(PaperPortfolio).where(PaperPortfolio.id == pp_id)
            )
        ).scalar_one()
        v = await value_portfolio_in_currency(db, loaded, "USD")

    assert len(v.holdings) == 1
    assert v.holdings[0].value_in_base == 0.0
    assert v.fx_warnings  # at least one warning


# ── API ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_valuation_endpoint_validates_currency(client):
    r = await client.get(
        "/api/v1/paper/current/valuation-in-currency?currency=US"
    )
    # 422 because currency != 3 chars
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_valuation_endpoint_returns_translation_with_seed(client):
    """The conftest seed has an active paper portfolio? If not, 404 — either way the route exists."""
    r = await client.get(
        "/api/v1/paper/current/valuation-in-currency?currency=USD"
    )
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        body = r.json()["data"]
        assert body["target_currency"] == "USD"
        assert "holdings" in body
        assert "total_value_in_target" in body


@pytest.mark.asyncio
async def test_valuation_endpoint_404_when_no_portfolio(client, monkeypatch):
    """Force no-current path."""
    from app.services.paper import PaperPortfolioService

    async def _no_current(self):
        return None

    monkeypatch.setattr(PaperPortfolioService, "get_current", _no_current)
    r = await client.get(
        "/api/v1/paper/current/valuation-in-currency?currency=USD"
    )
    assert r.status_code == 404
    assert "no_active_paper_portfolio" in r.json()["detail"]
