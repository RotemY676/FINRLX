"""US-P0-06 increment 2 — synthetic ingest sources fail closed.

The beta ingests deterministic *synthetic* market data via `ingest.py`
(`_generate_bars`/`_generate_news`) under the source label "local" (and its
alias "local_deterministic"). Those labels must be classified non-real so a
fabricated random-walk price can never back an eligible decision.

The classifier is an allowlist: only real providers ("yfinance", "chain") pass;
every other label — including the beta generator and any unknown/missing
provenance — is synthetic and fails closed. This closes the leak where a
nonempty unknown label silently defaulted to a pass.
"""
from __future__ import annotations

import pytest

from app.services.decision_packet_adapter import (
    _REAL_SOURCE_TOKENS,
    _classify_source,
)


@pytest.mark.parametrize("real", ["yfinance", "chain", "YFinance", " chain "])
def test_real_providers_are_not_synthetic(real):
    is_demo, is_synthetic = _classify_source(real)
    assert is_synthetic is False, f"{real!r} is a real provider, must not be synthetic"
    assert is_demo is False


@pytest.mark.parametrize(
    "label",
    [
        "local",  # the beta random-walk generator (the leak)
        "local_deterministic",  # its documented alias
        "test",  # conftest seed
        "fixture",
        "some_unknown_provider",  # unknown provenance must fail closed
        "",  # missing provenance
        None,
    ],
)
def test_non_real_sources_are_synthetic(label):
    _is_demo, is_synthetic = _classify_source(label)
    assert is_synthetic is True, f"{label!r} is not a real provider; must fail closed"


@pytest.mark.parametrize("label", ["demo", "demo-provider", "sample-data", "placeholder"])
def test_demo_sources_flagged_demo_and_synthetic(label):
    is_demo, is_synthetic = _classify_source(label)
    assert is_demo is True
    assert is_synthetic is True  # demo is also non-real → still fails closed


def test_allowlist_is_the_ingest_real_providers():
    """The real-source allowlist must match ingest.py's live-fetch branches."""
    assert set(_REAL_SOURCE_TOKENS) == {"yfinance", "chain"}
