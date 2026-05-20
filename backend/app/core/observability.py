"""Observability scaffolding (Phase MVP-7).

Initializes the Sentry SDK if a DSN is configured. When `settings.sentry_dsn`
is empty (local dev, CI, any deploy that didn't set the env var), this is a
no-op — `sentry_sdk.init` is never called, no network traffic, no module
side effects.

Two reasons to keep this as a one-shot function called at startup rather
than at import time:

1. Tests import `app.main` to spin up an ASGITransport — we don't want them
   accidentally pinging Sentry even with a DSN set.
2. The DSN can be rotated by restarting the process; we read settings fresh
   inside the function rather than at module load.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

_log = logging.getLogger(__name__)


def init_sentry() -> bool:
    """Initialize Sentry if configured. Returns True if init ran, False if skipped.

    Safe to call multiple times — sentry_sdk.init is itself idempotent for
    the same DSN.
    """
    if not settings.sentry_dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        _log.warning("sentry_sdk not installed; SENTRY_DSN set but no SDK available")
        return False

    integrations: list[Any] = [
        StarletteIntegration(transaction_style="endpoint"),
        FastApiIntegration(transaction_style="endpoint"),
    ]

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=integrations,
        # Personally-identifiable data is opt-in. The default is to scrub.
        send_default_pii=False,
    )
    _log.info("Sentry initialized for environment=%s", settings.sentry_environment)
    return True


__all__ = ["init_sentry"]
