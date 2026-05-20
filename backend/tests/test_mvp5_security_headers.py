"""Phase MVP-5 — Security headers middleware tests.

Each header is asserted on a representative response. The middleware is
applied globally, so we sanity-check on /health (public) and /api/v1/flags
(also public) to confirm both unauthenticated and lightly-authenticated
paths carry the headers.
"""
from __future__ import annotations

import pytest

EXPECTED_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
}


@pytest.mark.asyncio
async def test_security_headers_present_on_root(client):
    r = await client.get("/health")
    assert r.status_code == 200
    for header, value in EXPECTED_HEADERS.items():
        assert r.headers.get(header) == value, f"{header} missing or wrong"


@pytest.mark.asyncio
async def test_security_headers_present_on_api_v1_flags(client):
    r = await client.get("/api/v1/flags")
    assert r.status_code == 200
    for header in EXPECTED_HEADERS:
        assert header in r.headers


@pytest.mark.asyncio
async def test_x_frame_options_blocks_framing(client):
    r = await client.get("/api/v1/flags")
    assert r.headers["X-Frame-Options"] == "DENY"


@pytest.mark.asyncio
async def test_hsts_signals_year_long_inclusion(client):
    r = await client.get("/health")
    hsts = r.headers.get("Strict-Transport-Security", "")
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
