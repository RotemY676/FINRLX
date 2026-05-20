"""Rate limiting middleware (Phase MVP-5).

A thin wrapper over slowapi that gives every endpoint a per-IP token-bucket
limit. The global default protects against accidental loops; the named
limits (auth, ingest, recommendation_write) tighten the cost on paths an
attacker would target first.

Design notes
------------
- IP is taken from `request.client.host`. Behind Railway / a reverse proxy
  this is the proxy's address unless `X-Forwarded-For` is honored. We trust
  the standard `X-Forwarded-For` header in production; locally it falls
  back to the socket address.
- Storage is in-memory. For MVP we run a single backend instance so this is
  correct; if we shard horizontally we move to Redis (slowapi supports it
  via a different URI).
- Tests set `settings.rate_limit_enabled = False` (see conftest) to keep
  the suite hermetic. The limiter is still attached so endpoint decorators
  parse; it just doesn't enforce.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def _client_key(request: Request) -> str:
    """Identify the caller for rate-limiting.

    Prefer the leftmost X-Forwarded-For entry when present (Railway sets it),
    otherwise fall back to the direct socket address. We never trust a
    forwarded header without a proxy, but Railway terminates TLS and adds
    this header before reaching us.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Leftmost IP is the original client per the de-facto convention.
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_key,
    default_limits=[settings.rate_limit_default],
    enabled=settings.rate_limit_enabled,
    headers_enabled=True,
)


__all__ = ["limiter", "RateLimitExceeded"]
