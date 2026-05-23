"""Phase 20.2 — Universe membership add/remove with soft-delete provenance.

POST   /universes/{id}/assets         body: {"ticker": "AAPL"}
DELETE /universes/{id}/assets/{asset_id}

Soft-delete semantics:
  - first remove sets removed_at = now()
  - the row stays so backtests / replays of past recommendations can
    still resolve the (universe, asset) tuple
  - re-adding clears removed_at instead of attempting to INSERT a
    duplicate (which would violate the composite PK)

All operations are scoped to a freshly-created test universe so the
session-scoped DB seed is left intact.
"""
import pytest


async def _new_universe(client, name: str) -> str:
    r = await client.post("/api/v1/universes", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["data"]["universe_id"]


async def _asset_id_for_ticker(client, ticker: str) -> str:
    """The seeded DB has AAPL + MSFT. Resolve their ids by reading the
    default universe (which contains both)."""
    r = await client.get("/api/v1/universes/default")
    assert r.status_code == 200
    for a in r.json()["data"]["assets"]:
        if a["ticker"].upper() == ticker.upper():
            return a["asset_id"]
    raise AssertionError(f"Ticker {ticker} not in seeded default universe")


def test_migration_added_removed_at_column():
    """The UniverseMembership model carries the column the Alembic migration
    added — guards against schema drift if someone hand-edits the model."""
    from app.models.reference import UniverseMembership
    assert "removed_at" in UniverseMembership.__table__.columns
    col = UniverseMembership.__table__.columns["removed_at"]
    assert col.nullable is True


@pytest.mark.asyncio
async def test_add_asset_succeeds_and_appears_in_detail(client):
    uid = await _new_universe(client, "Mem20.2 Empty Alpha")
    r = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert "AAPL" in data["tickers"]
    assert data["asset_count"] == 1


@pytest.mark.asyncio
async def test_add_asset_is_case_insensitive(client):
    uid = await _new_universe(client, "Mem20.2 Lower Case")
    r = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "aapl"})
    assert r.status_code == 200
    assert "AAPL" in r.json()["data"]["tickers"]


@pytest.mark.asyncio
async def test_add_asset_unknown_ticker_returns_409(client):
    uid = await _new_universe(client, "Mem20.2 Unknown")
    r = await client.post(
        f"/api/v1/universes/{uid}/assets",
        json={"ticker": "ZZZZZZ"},
    )
    assert r.status_code == 409
    assert "not found" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_duplicate_active_returns_409(client):
    uid = await _new_universe(client, "Mem20.2 Dup")
    r1 = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    assert r1.status_code == 200
    r2 = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    assert r2.status_code == 409
    assert "already a current member" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_asset_soft_deletes(client):
    uid = await _new_universe(client, "Mem20.2 Remove")
    add = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    aapl_id = next(a["asset_id"] for a in add.json()["data"]["assets"])
    r = await client.delete(f"/api/v1/universes/{uid}/assets/{aapl_id}")
    assert r.status_code == 200
    # AAPL no longer appears in "current" detail.
    detail = await client.get(f"/api/v1/universes/{uid}")
    assert "AAPL" not in detail.json()["data"]["tickers"]
    assert detail.json()["data"]["asset_count"] == 0


@pytest.mark.asyncio
async def test_remove_then_add_clears_removed_at(client):
    """Re-add must clear removed_at on the existing row rather than INSERT
    a duplicate (would violate the composite PK)."""
    uid = await _new_universe(client, "Mem20.2 Readd")
    add1 = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    aapl_id = next(a["asset_id"] for a in add1.json()["data"]["assets"])
    rm = await client.delete(f"/api/v1/universes/{uid}/assets/{aapl_id}")
    assert rm.status_code == 200
    add2 = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    assert add2.status_code == 200
    assert "AAPL" in add2.json()["data"]["tickers"]
    # And we did NOT silently double-add — count is still 1.
    assert add2.json()["data"]["asset_count"] == 1


@pytest.mark.asyncio
async def test_remove_already_removed_returns_409(client):
    uid = await _new_universe(client, "Mem20.2 DoubleRemove")
    add = await client.post(f"/api/v1/universes/{uid}/assets", json={"ticker": "AAPL"})
    aapl_id = next(a["asset_id"] for a in add.json()["data"]["assets"])
    await client.delete(f"/api/v1/universes/{uid}/assets/{aapl_id}")
    r = await client.delete(f"/api/v1/universes/{uid}/assets/{aapl_id}")
    assert r.status_code == 409
    assert "already removed" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_non_member_returns_409(client):
    """Try to remove an asset that's not actually in the universe."""
    uid = await _new_universe(client, "Mem20.2 NotMember")
    # Use a known asset id from the seeded default universe.
    aapl_id = await _asset_id_for_ticker(client, "AAPL")
    r = await client.delete(f"/api/v1/universes/{uid}/assets/{aapl_id}")
    assert r.status_code == 409
    assert "not a member" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_to_unknown_universe_returns_404(client):
    r = await client.post(
        "/api/v1/universes/00000000-0000-0000-0000-000000000000/assets",
        json={"ticker": "AAPL"},
    )
    assert r.status_code == 404
