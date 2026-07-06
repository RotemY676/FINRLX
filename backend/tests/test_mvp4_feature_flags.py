"""Phase MVP-4 — Feature-flag endpoint tests.

The /api/v1/flags endpoint is read by the frontend at boot to decide
which navigation surfaces to expose. Defaults are ON (so test envs
work); production sets FEATURE_RESEARCH_LANE=false etc. via env.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_flags_endpoint_returns_default_payload_shape(client):
    r = await client.get("/api/v1/flags")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "meta" in body
    assert "data" in body
    data = body["data"]
    # MVP-4 flags + product-track surface flags must be present
    assert set(data.keys()) == {
        "research_lane", "paper_trading", "backtests", "replay",
        "universe_ui",       # A1
        "ops_ui",            # A2
        "policy_ui",         # A3
        "integrations_ui",   # A4
        "risk_ui",           # B1
        "news_ui",           # B2
        "operator_console",  # O-0
        "research_fundamentals_ui",  # Phase 16
        "research_peers_ui",         # Phase 16
    }
    # Defaults are ON for the test environment
    for k in data:
        assert isinstance(data[k], bool), f"{k} must be bool, got {type(data[k])}"


@pytest.mark.asyncio
async def test_flags_endpoint_reflects_settings_override(client, monkeypatch):
    """When a setting is overridden, the endpoint reflects the new value."""
    from app.core import config as config_mod
    monkeypatch.setattr(config_mod.settings, "feature_research_lane", False)
    r = await client.get("/api/v1/flags")
    assert r.json()["data"]["research_lane"] is False
    monkeypatch.setattr(config_mod.settings, "feature_research_lane", True)
    r2 = await client.get("/api/v1/flags")
    assert r2.json()["data"]["research_lane"] is True


@pytest.mark.asyncio
async def test_flags_endpoint_is_public_no_auth_required(client):
    """The /flags endpoint is read at app boot before auth — must be public."""
    r = await client.get("/api/v1/flags")
    assert r.status_code == 200
