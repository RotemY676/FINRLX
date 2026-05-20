"""Auth service: password hashing, JWT issue/verify, refresh rotation.

Pure functions where possible. DB interactions are done by the router via
AsyncSession; this module owns the crypto + token semantics only.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

_DEV_DEFAULT_JWT_SECRET = "dev-only-not-for-production-jwt-secret-rotate-me-please"

# Precomputed valid bcrypt hash used by verify_password during login for non-existent
# users — keeps timing roughly constant whether the user exists or not.
_TIMING_DUMMY_HASH = bcrypt.hashpw(b"timing-dummy-not-a-real-password", bcrypt.gensalt(rounds=4)).decode("utf-8")


def guard_jwt_secret() -> None:
    """Refuse to start with the default JWT secret in production-shaped envs.

    Heuristic: if not debug AND database is not SQLite, we are in prod-shape.
    """
    if (
        not settings.debug
        and not settings.database_url.startswith("sqlite")
        and settings.jwt_secret == _DEV_DEFAULT_JWT_SECRET
    ):
        raise RuntimeError(
            "JWT_SECRET is at its development default but the runtime "
            "looks like production (non-debug, non-sqlite). Set JWT_SECRET "
            "to a strong random value (>= 32 bytes of entropy) via env var."
        )


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_access_token(*, user_id: str, role: str) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate. Raises jwt.PyJWTError on any failure."""
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub", "typ"]},
    )
    if payload.get("typ") != "access":
        raise jwt.InvalidTokenError("Token type is not 'access'")
    return payload


def generate_refresh_token_pair() -> tuple[str, str]:
    """Return (plaintext, hash). Plaintext is sent to the client once; only hash is stored."""
    plaintext = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    return plaintext, hashed


def hash_refresh_token(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def refresh_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)


def timing_safe_dummy_hash() -> str:
    """Returns a valid bcrypt hash to use in verify_password when user is missing.

    Reason: `bcrypt.checkpw` returns immediately on a malformed-format hash, so a
    fake string like "$2b$12$" + "x"*53 produces a timing oracle. A real
    precomputed bcrypt hash forces the cost to be paid.
    """
    return _TIMING_DUMMY_HASH
