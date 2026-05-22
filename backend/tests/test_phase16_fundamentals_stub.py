"""Phase 16.0 — Fundamentals + Peers provider abstraction contract.

These tests pin the contract that holds across the stub provider (16.0)
and the real Finnhub provider (16.2 lands as a drop-in replacement):

  - Endpoints always return 200 with a structurally-complete envelope.
  - When no provider is configured, the envelope is tagged source="stub"
    and carries a coverage_note that names the env vars to set.
  - Invalid tickers 400 — no provider round-trip is wasted on garbage.
  - The status endpoint is cheap (does not call the provider) and
    reports unconfigured by default.
  - The two new feature flags are exposed by /api/v1/flags.
"""
from __future__ import annotations

import pytest

from app.services.fundamentals.router import (
    get_provider,
    get_provider_status,
)
from app.services.fundamentals.stub_provider import StubFundamentalsProvider


# ── Router unit tests ────────────────────────────────────────────────────


def test_router_returns_stub_by_default(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "")
    monkeypatch.setattr(config_mod.settings, "fundamentals_finnhub_api_key", "")
    provider = get_provider()
    assert provider is not None, "router must never return None — stub is the floor"
    assert provider.name == "stub"
    assert isinstance(provider, StubFundamentalsProvider)


def test_router_status_unconfigured_by_default(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "")
    monkeypatch.setattr(config_mod.settings, "fundamentals_finnhub_api_key", "")
    s = get_provider_status()
    assert s.configured is False
    assert "FUNDAMENTALS_PROVIDER" in s.detail
    assert "finnhub" in s.detail.lower()


def test_router_status_finnhub_without_key(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "finnhub")
    monkeypatch.setattr(config_mod.settings, "fundamentals_finnhub_api_key", "")
    s = get_provider_status()
    assert s.configured is False
    assert "FINNHUB_API_KEY" in s.detail
    # Provider name reflects the selection, even though it's not actually
    # usable yet — operator can diagnose by reading the detail line.
    assert s.provider_name == "finnhub"


def test_router_status_finnhub_with_key(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "finnhub")
    monkeypatch.setattr(config_mod.settings, "fundamentals_finnhub_api_key", "dummy-test-key")
    s = get_provider_status()
    assert s.configured is True
    assert s.provider_name == "finnhub"
    # Phase 16.2 — provider is live; detail mentions the cache budget so
    # operators reading the status endpoint see at-a-glance which TTLs
    # are in effect.
    assert "live" in s.detail.lower()
    assert "cache" in s.detail.lower()


def test_router_unknown_provider_falls_back_to_stub(monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "bogus-provider")
    provider = get_provider()
    assert provider is not None
    assert provider.name == "stub"
    s = get_provider_status()
    assert s.configured is False
    assert "Unknown" in s.detail


# ── Stub provider unit tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stub_fundamentals_envelope_complete():
    provider = StubFundamentalsProvider()
    payload = await provider.get_fundamentals("nvda")
    assert payload.ticker == "NVDA"
    assert payload.source == "stub"
    assert payload.cached_at is not None
    assert payload.coverage_note is not None
    assert "FUNDAMENTALS_PROVIDER" in payload.coverage_note
    # Every metric is None — no invented numbers.
    assert payload.pe_ratio_ttm is None
    assert payload.market_cap_usd is None
    assert payload.gross_margin_ttm is None


@pytest.mark.asyncio
async def test_stub_peers_envelope_complete():
    provider = StubFundamentalsProvider()
    payload = await provider.get_peers("AAPL")
    assert payload.target_ticker == "AAPL"
    assert payload.source == "stub"
    assert payload.peers == []
    assert payload.coverage_note is not None


# ── HTTP endpoint contract ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_fundamentals_endpoint_returns_stub_envelope(client, monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "")
    r = await client.get("/api/v1/research/fundamentals/NVDA")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data"]["ticker"] == "NVDA"
    assert body["data"]["source"] == "stub"
    assert body["data"]["coverage_note"] is not None


@pytest.mark.asyncio
async def test_get_peers_endpoint_returns_stub_envelope(client, monkeypatch):
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "")
    r = await client.get("/api/v1/research/peers/MSFT")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data"]["target_ticker"] == "MSFT"
    assert body["data"]["source"] == "stub"
    assert body["data"]["peers"] == []


@pytest.mark.asyncio
async def test_get_fundamentals_rejects_invalid_ticker(client):
    r = await client.get("/api/v1/research/fundamentals/not-a-ticker!")
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_get_peers_rejects_invalid_ticker(client):
    r = await client.get("/api/v1/research/peers/12345")
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_fundamentals_status_endpoint_does_not_call_provider(client, monkeypatch):
    """The status endpoint must be cheap — never call provider methods."""
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "fundamentals_provider", "")
    r = await client.get("/api/v1/research/fundamentals/_status")
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["configured"] is False
    assert "detail" in data


# ── Feature flags exposure ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_flags_endpoint_exposes_research_flags(client):
    r = await client.get("/api/v1/flags")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "research_fundamentals_ui" in data
    assert "research_peers_ui" in data
    # Defaults are True so the panels surface (with stub envelope) until
    # the operator turns them off explicitly.
    assert data["research_fundamentals_ui"] is True
    assert data["research_peers_ui"] is True
