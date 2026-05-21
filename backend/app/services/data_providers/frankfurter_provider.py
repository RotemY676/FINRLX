"""Phase FX-1 — Frankfurter API adapter.

Frankfurter (https://frankfurter.dev) is a free, open-source FX rate
proxy backed by ECB reference rates. No API key, no quota — only
abuse-prevention throttling.

We use the v2 API (`https://api.frankfurter.dev/v2/`):
* ``GET /v2/rates?base=USD&quotes=EUR,ILS,GBP`` → latest available
* ``GET /v2/rates?date=YYYY-MM-DD&base=USD&quotes=EUR,ILS,GBP`` → historical

Adapter returns a dict of ``{quote_currency: rate}`` for the requested
date (or latest if date omitted). Network errors propagate as
``FrankfurterError`` so the caller can decide whether to fall back to
the cached row or warn the user.
"""
from __future__ import annotations

from datetime import date as DateType
from typing import Any

import httpx

FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2"
SUPPORTED_BASE_QUOTES = ("USD", "EUR", "ILS", "GBP")
DEFAULT_TIMEOUT_S = 10.0


class FrankfurterError(RuntimeError):
    """Raised on any Frankfurter fetch failure."""


async def fetch_rates(
    base: str,
    quotes: list[str] | tuple[str, ...],
    rate_date: DateType | None = None,
    *,
    client: httpx.AsyncClient | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict[str, float]:
    """Fetch FX rates for ``base`` against ``quotes``.

    * ``rate_date=None`` ⇒ latest available rate (typically previous
      business day, since the ECB publishes once per day).
    * ``rate_date=`` a past date ⇒ historical rate for that date.

    Returns ``{quote_currency: rate}`` where ``1 base = rate quote``.

    Raises ``FrankfurterError`` on any HTTP / parse failure.
    """
    if base not in SUPPORTED_BASE_QUOTES:
        raise FrankfurterError(f"unsupported base currency {base!r}")
    valid_quotes = [q for q in quotes if q in SUPPORTED_BASE_QUOTES and q != base]
    if not valid_quotes:
        return {}

    params: dict[str, Any] = {"base": base, "quotes": ",".join(valid_quotes)}
    if rate_date is not None:
        params["date"] = rate_date.isoformat()

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=timeout_s)

    try:
        try:
            resp = await client.get(f"{FRANKFURTER_BASE_URL}/rates", params=params)
        except httpx.HTTPError as exc:
            raise FrankfurterError(f"frankfurter request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise FrankfurterError(
                f"frankfurter HTTP {resp.status_code}: {resp.text[:200]}"
            )
        try:
            body = resp.json()
        except ValueError as exc:
            raise FrankfurterError(f"frankfurter returned non-JSON: {exc}") from exc

        rates = body.get("rates")
        if not isinstance(rates, dict):
            raise FrankfurterError(
                f"frankfurter payload missing 'rates' dict: {body!r}"
            )
        return {k: float(v) for k, v in rates.items()}
    finally:
        if own_client and client is not None:
            await client.aclose()
