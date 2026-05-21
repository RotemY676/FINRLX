"""Google OAuth 2.0 service — sign-in with Gmail.

Authorization-code flow with state CSRF protection. We deliberately do
NOT depend on `google-auth` here; everything is plain HTTP via httpx +
manual ID-token verification through Google's JWKS endpoint. Reasons:

* keeps the dep tree small (httpx is already vendored)
* makes the verification path easy to audit
* avoids the `google-auth` library's transitive `cryptography` pin churn

Public entry points:

  * ``build_authorization_url(state)``    — returns the URL to redirect
    the browser to.
  * ``exchange_code_for_id_token(code)``  — POST /token, returns the
    raw id_token JWT string.
  * ``verify_id_token(id_token)``         — verifies signature against
    Google's JWKS + audience/issuer/expiry; returns the claims dict.

The actual login state (state cookie, callback flow) lives in
``app/api/v1/auth.py`` so the service stays pure HTTP.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUER_ALLOWLIST = (
    "https://accounts.google.com",
    "accounts.google.com",
)
GOOGLE_SCOPES = "openid email profile"


class GoogleOAuthDisabled(RuntimeError):
    """Raised when no client_id is configured."""


class GoogleOAuthError(RuntimeError):
    """Raised on any OAuth handshake failure."""


@dataclass(frozen=True)
class GoogleIdClaims:
    sub: str                # Google account id (stable)
    email: str
    email_verified: bool
    name: str | None
    picture: str | None
    raw: dict[str, Any]


def _require_configured() -> None:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise GoogleOAuthDisabled(
            "Google OAuth is not configured (GOOGLE_OAUTH_CLIENT_ID / SECRET missing)."
        )


def build_authorization_url(state: str) -> str:
    """Return the Google authorization URL for the browser to navigate to."""
    _require_configured()
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "online",     # we don't need a long-lived refresh token from Google
        "prompt": "select_account",  # show account picker every time
        "state": state,
    }
    return GOOGLE_AUTH_URL + "?" + "&".join(
        f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items()
    )


async def exchange_code_for_id_token(
    code: str, *, client: httpx.AsyncClient | None = None
) -> str:
    """Exchange an authorization code for Google's id_token JWT."""
    _require_configured()
    payload = {
        "code": code,
        "client_id": settings.google_oauth_client_id,
        "client_secret": settings.google_oauth_client_secret,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "grant_type": "authorization_code",
    }
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=15.0)
    try:
        try:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
        except httpx.HTTPError as exc:
            raise GoogleOAuthError(f"token exchange failed: {exc}") from exc
        if resp.status_code >= 400:
            raise GoogleOAuthError(
                f"token exchange HTTP {resp.status_code}: {resp.text[:300]}"
            )
        body = resp.json()
        id_token = body.get("id_token")
        if not isinstance(id_token, str):
            raise GoogleOAuthError(
                f"token response missing id_token: {json.dumps(body)[:200]}"
            )
        return id_token
    finally:
        if own_client and client is not None:
            await client.aclose()


# JWKS verifier with the in-process cache pyjwt provides (no extra dep).
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(GOOGLE_JWKS_URL)
    return _jwks_client


def verify_id_token(id_token: str) -> GoogleIdClaims:
    """Verify the id_token's signature + iss + aud + exp; return claims.

    Raises GoogleOAuthError on any verification failure.
    """
    _require_configured()
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(id_token).key
    except Exception as exc:  # noqa: BLE001
        raise GoogleOAuthError(f"could not fetch JWKS key: {exc}") from exc

    try:
        decoded = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.google_oauth_client_id,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise GoogleOAuthError(f"id_token verification failed: {exc}") from exc

    iss = decoded.get("iss")
    if iss not in GOOGLE_ISSUER_ALLOWLIST:
        raise GoogleOAuthError(f"id_token issuer not Google: {iss!r}")

    email = decoded.get("email")
    if not email:
        raise GoogleOAuthError("id_token has no 'email' claim")
    if decoded.get("email_verified") is not True:
        raise GoogleOAuthError(
            f"Google reports email {email!r} is not verified — refusing login"
        )

    sub = decoded.get("sub")
    if not isinstance(sub, str):
        raise GoogleOAuthError("id_token missing 'sub' (account id)")

    return GoogleIdClaims(
        sub=sub,
        email=email,
        email_verified=True,
        name=decoded.get("name"),
        picture=decoded.get("picture"),
        raw=decoded,
    )
