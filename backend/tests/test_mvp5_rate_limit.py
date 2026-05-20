"""Rate limiter tests.

The limiter is disabled globally in conftest so the rest of the suite is
hermetic. These tests temporarily re-enable it, then turn it back off in a
`finally` so they don't pollute later tests. The auth cap is read from
`settings.rate_limit_auth` so the tests stay correct if the cap is retuned.
"""
import pytest

from app.core.config import settings
from app.core.rate_limit import limiter


def _auth_cap() -> int:
    """Parse the leading integer from a slowapi limit string like '10/minute'."""
    return int(settings.rate_limit_auth.split("/", 1)[0])


async def _flood_login(client, count: int) -> list[int]:
    statuses: list[int] = []
    for _ in range(count):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "x"},
        )
        statuses.append(r.status_code)
    return statuses


@pytest.mark.asyncio
async def test_auth_login_rate_limited_after_burst(client):
    cap = _auth_cap()
    limiter.enabled = True
    limiter.reset()
    try:
        in_cap = await _flood_login(client, cap)
        # Under the cap we expect the auth-failure path, never a 429.
        assert all(s in (401, 422) for s in in_cap), (
            f"saw a 429 inside the cap of {cap}: {in_cap}"
        )

        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "x"},
        )
        assert r.status_code == 429, (
            f"expected 429 after {cap}/minute cap; got {r.status_code}"
        )
    finally:
        limiter.enabled = False
        limiter.reset()


@pytest.mark.asyncio
async def test_disabled_limiter_does_not_block(client):
    assert limiter.enabled is False
    statuses = await _flood_login(client, _auth_cap() * 2)
    assert all(s in (401, 422) for s in statuses)


@pytest.mark.asyncio
async def test_rate_limit_response_carries_retry_after(client):
    limiter.enabled = True
    limiter.reset()
    try:
        await _flood_login(client, _auth_cap())
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "x"},
        )
        assert r.status_code == 429
        # slowapi sets Retry-After when headers_enabled=True; operators rely on
        # it for backoff hints.
        assert "retry-after" in {k.lower() for k in r.headers}
    finally:
        limiter.enabled = False
        limiter.reset()
