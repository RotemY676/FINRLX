"""Phase MVP-7 — Sentry initialization no-op contract.

The contract: when `settings.sentry_dsn` is empty, `init_sentry()` does NOT
call `sentry_sdk.init`. This is what lets tests, local dev, and any deploy
without the env var run silently.

We verify by monkey-patching `sentry_sdk.init` and asserting it wasn't
called. We do NOT actually contact Sentry.
"""
from __future__ import annotations

import pytest

from app.core import observability
from app.core.config import settings


def test_init_sentry_is_noop_when_dsn_empty(monkeypatch):
    calls: list[dict] = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(settings, "sentry_dsn", "")
    monkeypatch.setattr("sentry_sdk.init", fake_init)

    result = observability.init_sentry()

    assert result is False
    assert calls == []


def test_init_sentry_calls_sentry_sdk_init_when_dsn_present(monkeypatch):
    calls: list[dict] = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(settings, "sentry_dsn", "https://example@sentry.io/12345")
    monkeypatch.setattr(settings, "sentry_environment", "test")
    monkeypatch.setattr("sentry_sdk.init", fake_init)

    result = observability.init_sentry()

    assert result is True
    assert len(calls) == 1
    init_kwargs = calls[0]
    assert init_kwargs["dsn"] == "https://example@sentry.io/12345"
    assert init_kwargs["environment"] == "test"
    assert init_kwargs["send_default_pii"] is False
