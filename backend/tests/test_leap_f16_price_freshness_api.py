"""LEAP F1.6 — price-freshness endpoint contract."""
from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import delete

from app.models.ingestion import MarketBar


@pytest.mark.asyncio
async def test_freshness_endpoint_full_and_single(client):
    from tests.conftest import test_session_factory

    async with test_session_factory() as db:
        await db.execute(delete(MarketBar).where(MarketBar.ticker == "F16T"))
        db.add(MarketBar(asset_id="a-f16", ticker="F16T", bar_date=date(2020, 1, 6),
                         interval="1d", open=1, high=1, low=1, close=1, volume=1,
                         source="chain"))
        await db.commit()

    r = await client.get("/api/v1/prices/freshness")
    assert r.status_code == 200
    body = r.json()["data"]
    assert {"fresh", "stale", "degraded"} <= set(body["counts"])
    assert any(t["ticker"] == "F16T" and t["status"] == "degraded" for t in body["tickers"])

    r2 = await client.get("/api/v1/prices/freshness?ticker=f16t")
    assert r2.status_code == 200
    one = r2.json()["data"]
    assert one["status"] == "degraded" and one["latest_bar_date_iso"] == "2020-01-06"

    r3 = await client.get("/api/v1/prices/freshness?ticker=NOBARS9")
    assert r3.status_code == 404

    async with test_session_factory() as db:
        await db.execute(delete(MarketBar).where(MarketBar.ticker == "F16T"))
        await db.commit()
