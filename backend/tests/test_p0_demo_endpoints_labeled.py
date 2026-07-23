"""US-P0-06 increment 3 — seeded demo endpoints are explicitly labeled.

`GET /regime`, `GET /scenario/baseline`, and `POST /scenario/simulate` return
seeded/illustrative figures, not live model output. Zero-fiction requires that
such data be explicitly labeled so a consumer can never mistake it for real
evidence. The label is a standardized, machine-parseable `DEMO_DATA:` entry in
`meta.warnings` (the response-envelope warning channel).
"""
from __future__ import annotations

import pytest

from app.api.deps import DEMO_DATA_WARNING


def _is_demo_labeled(meta: dict) -> bool:
    return any(w.startswith("DEMO_DATA:") for w in meta.get("warnings", []))


@pytest.mark.asyncio
async def test_regime_is_no_longer_demo_it_is_computed(client):
    """`/regime` was rebuilt on real bars 2026-07-23 — it must not be demo.

    It previously returned a hardcoded "Risk-on · late-cycle" with an invented
    confidence, invented alternative-regime probabilities, factor sigmas and
    sector tilts. Labelling that as demo was the *mitigation*; computing it is
    the fix. This asserts the fix stands and the label is gone with it, so a
    regression back to seeded data fails here rather than quietly re-earning
    the demo tag.
    """
    r = await client.get("/api/v1/regime")
    # 503 is legitimate: no benchmark history is a refusal, not a guess.
    if r.status_code == 503:
        pytest.skip("benchmark history unavailable in this environment")
    assert r.status_code == 200
    body = r.json()
    assert not _is_demo_labeled(body["meta"]), "regime is computed; it must not be demo-labeled"

    data = body["data"]
    # The label comes from the same rule the dossier uses.
    assert data["regime_label"] in {"uptrend", "downtrend", "neutral", "risk-off"}
    assert data["benchmark"] == "SPY"
    assert data["regime_kind"] and "not a prediction" in data["regime_kind"]
    # What the system cannot model must be empty AND named, not fabricated.
    assert data["regime_confidence"] is None
    assert data["alternatives"] == []
    assert data["signal_posture"] == []
    assert data["sector_tilts"] == []
    assert any("regime_confidence" in u for u in data["unavailable"])


@pytest.mark.asyncio
async def test_scenario_baseline_is_labeled_demo(client):
    r = await client.get("/api/v1/scenario/baseline")
    assert r.status_code == 200
    assert _is_demo_labeled(r.json()["meta"])


@pytest.mark.asyncio
async def test_scenario_simulate_is_labeled_demo_and_keeps_domain_warnings(client):
    """The demo label rides in meta.warnings; domain warnings stay in data."""
    r = await client.post("/api/v1/scenario/simulate", json={
        "horizon_days": 90, "rate_shock_bps": 200, "correlation": 0.5,
        "earnings_revision_weight": 0.5, "momentum_engine_on": False,
        "flow_engine_on": True, "policy_constraints_on": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert _is_demo_labeled(body["meta"])  # envelope carries the demo label
    assert len(body["data"]["warnings"]) >= 2  # domain scenario warnings intact


def test_demo_warning_is_prefixed():
    """The constant must use the machine-parseable DEMO_DATA: prefix."""
    assert DEMO_DATA_WARNING.startswith("DEMO_DATA:")
