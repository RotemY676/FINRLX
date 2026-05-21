"""OAUTH-1 — Google sign-in contract.

We don't actually call Google; the upstream interactions are stubbed via
monkeypatch. The tests assert:

* /auth/google/start returns 503 when the client_id env var is empty
* /auth/google/start sets a state cookie and 302s to Google
* /auth/google/callback rejects when state mismatches (CSRF guard)
* /auth/google/callback rejects when email_verified is false
* /auth/google/callback enforces the allowlist gate
* /auth/google/callback issues tokens for an allowlisted Gmail address
"""
from __future__ import annotations

import secrets
from urllib.parse import parse_qs, urlsplit

import pytest

from app.models.auth import EmailAllowlist
from app.services import google_oauth as goauth


def _gmail() -> str:
    return f"gtest-{secrets.token_hex(4)}@example.com"


def _stub_google(
    monkeypatch,
    *,
    email: str,
    email_verified: bool = True,
    client_id: str = "test-client-id.apps.googleusercontent.com",
    client_secret: str = "test-client-secret",
) -> None:
    """Configure settings + stub the exchange + verify funcs."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "google_oauth_client_id", client_id)
    monkeypatch.setattr(settings, "google_oauth_client_secret", client_secret)
    monkeypatch.setattr(
        settings, "google_oauth_redirect_uri",
        "http://localhost:8000/api/v1/auth/google/callback",
    )
    monkeypatch.setattr(
        settings, "google_oauth_post_login_redirect",
        "http://localhost:3000/login/google-finish",
    )

    async def fake_exchange(code, *, client=None):
        return "FAKE.ID.TOKEN"

    def fake_verify(id_token):
        return goauth.GoogleIdClaims(
            sub="google-uid-12345",
            email=email,
            email_verified=email_verified,
            name="Test User",
            picture=None,
            raw={},
        )

    monkeypatch.setattr(goauth, "exchange_code_for_id_token", fake_exchange)
    monkeypatch.setattr(goauth, "verify_id_token", fake_verify)
    # Re-export through the auth module (it imports at module top with noqa).
    import app.api.v1.auth as auth_mod

    monkeypatch.setattr(auth_mod, "exchange_code_for_id_token", fake_exchange)
    monkeypatch.setattr(auth_mod, "verify_id_token", fake_verify)


@pytest.mark.asyncio
async def test_google_start_503_when_unconfigured(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "google_oauth_client_id", "")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "")
    r = await client.get("/api/v1/auth/google/start", follow_redirects=False)
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_google_start_redirects_with_state_cookie(client, monkeypatch):
    _stub_google(monkeypatch, email=_gmail())
    r = await client.get("/api/v1/auth/google/start", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
    set_cookie = r.headers.get("set-cookie", "")
    assert "finrlx_google_state=" in set_cookie


@pytest.mark.asyncio
async def test_google_callback_state_mismatch(client, monkeypatch):
    _stub_google(monkeypatch, email=_gmail())
    r = await client.get(
        "/api/v1/auth/google/callback?code=x&state=does-not-match",
        cookies={"finrlx_google_state": "real-state"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    loc = r.headers["location"]
    # FE finish URL with error=state mismatch in the query
    assert "error=state+mismatch" in loc or "error=state%20mismatch" in loc


@pytest.mark.asyncio
async def test_google_callback_blocks_non_allowlisted(client, monkeypatch):
    email = _gmail()
    _stub_google(monkeypatch, email=email)
    r = await client.get(
        "/api/v1/auth/google/callback?code=x&state=s",
        cookies={"finrlx_google_state": "s"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "not_allowlisted" in r.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_blocks_unverified_email(client, monkeypatch):
    email = _gmail()
    _stub_google(monkeypatch, email=email, email_verified=False)

    # Add to allowlist so allowlist isn't the rejection reason
    from tests.conftest import test_session_factory
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()

    # Override the stub to raise GoogleOAuthError, since unverified email
    # causes verify_id_token to raise (see the service code).
    import app.api.v1.auth as auth_mod

    def raise_unverified(token):
        raise goauth.GoogleOAuthError("not verified")

    monkeypatch.setattr(auth_mod, "verify_id_token", raise_unverified)

    r = await client.get(
        "/api/v1/auth/google/callback?code=x&state=s",
        cookies={"finrlx_google_state": "s"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "verification" in r.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_issues_tokens_for_allowlisted(client, monkeypatch):
    email = _gmail()
    _stub_google(monkeypatch, email=email)

    from tests.conftest import test_session_factory
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()

    r = await client.get(
        "/api/v1/auth/google/callback?code=x&state=s",
        cookies={"finrlx_google_state": "s"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    loc = r.headers["location"]
    # FE finish URL with tokens in the fragment
    assert loc.startswith("http://localhost:3000/login/google-finish#")
    _scheme, _netloc, _path, _query, fragment = urlsplit(loc)
    params = parse_qs(fragment)
    assert "access_token" in params
    assert "refresh_token" in params
    assert params["user_email"][0] == email
