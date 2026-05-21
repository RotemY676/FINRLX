"""Phase TPL-2 — template metrics + read API contract."""
from __future__ import annotations

import secrets

import pytest

from app.models.recommendation_template import RecommendationTemplate
from app.services.template_metrics import (
    DEFENSIVE_EXPECTED_RETURN,
    EQUITY_EXPECTED_RETURN,
    METHODOLOGY_NOTE,
    expected_metrics,
)

# ── Pure helpers ─────────────────────────────────────────────────────


def _make_template(
    key: str,
    bucket: str = "moderate",
    horizon: str = "3y_5y",
    max_dd: float = 15.0,
) -> RecommendationTemplate:
    return RecommendationTemplate(
        key=key,
        name=f"Test {key}",
        description="t",
        badge="t",
        risk_bucket=bucket,
        horizon_band=horizon,
        primary_goal="growth",
        max_drawdown_pct=max_dd,
    )


def test_expected_metrics_low_bucket_low_return():
    t = _make_template("low", bucket="conservative", horizon="1y_3y", max_dd=20.0)
    m = expected_metrics(t)
    # Conservative + 1y_3y = 20/80
    assert m.equity_pct == 20.0
    assert m.defensive_pct == 80.0
    expected_ret = 0.20 * EQUITY_EXPECTED_RETURN + 0.80 * DEFENSIVE_EXPECTED_RETURN
    assert abs(m.expected_annual_return_pct - round(expected_ret * 100, 2)) < 0.01


def test_expected_metrics_high_bucket_high_return():
    t = _make_template("high", bucket="aggressive", horizon="gt_10y", max_dd=50.0)
    m = expected_metrics(t)
    # Aggressive + gt_10y = 95/5
    assert m.equity_pct == 95.0
    assert m.defensive_pct == 5.0
    # Higher equity ⇒ higher return ⇒ higher absolute Sharpe vs low bucket
    low_m = expected_metrics(
        _make_template("low2", bucket="conservative", horizon="1y_3y", max_dd=20.0)
    )
    assert m.expected_annual_return_pct > low_m.expected_annual_return_pct


def test_max_drawdown_caps_at_template_setting():
    """If the methodology dd > template.max_drawdown_pct, we report the cap."""
    # Aggressive: methodology max dd is ~2.5 * vol ≈ 2.5 * 15-16% ≈ 38%+
    # so a template that says max_dd=10 should be capped at 10.
    t = _make_template("cap", bucket="aggressive", horizon="gt_10y", max_dd=10.0)
    m = expected_metrics(t)
    assert m.expected_max_drawdown_pct == 10.0


def test_sharpe_estimate_signed_and_bounded():
    """Equity-heavy portfolios should have positive Sharpe under the chosen RF."""
    t = _make_template("sharpe", bucket="moderate_aggressive", horizon="5y_10y")
    m = expected_metrics(t)
    assert m.sharpe_estimate > 0  # expected return > 4% RF
    assert -2.0 < m.sharpe_estimate < 2.0  # sanity bound


def test_methodology_note_includes_disclaimer():
    t = _make_template("note")
    m = expected_metrics(t)
    assert m.confidence_label == "low"
    assert "Vanguard" in m.methodology_note
    assert "Morningstar" in m.methodology_note


# ── API ──────────────────────────────────────────────────────────────


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _signup(client) -> tuple[str, str]:
    from app.models.auth import EmailAllowlist
    from tests.conftest import test_session_factory

    email = f"tpl2-{secrets.token_hex(4)}@example.com"
    async with test_session_factory() as db:
        db.add(EmailAllowlist(email=email))
        await db.commit()
    r = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-strong-password-12345"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["user"]["id"], body["tokens"]["access_token"]


async def _ensure_templates_seeded() -> None:
    import scripts.seed_recommendation_templates as seed_mod
    from scripts.seed_recommendation_templates import seed
    from tests.conftest import test_session_factory

    original = seed_mod.async_session_factory
    seed_mod.async_session_factory = test_session_factory
    try:
        await seed()
    finally:
        seed_mod.async_session_factory = original


@pytest.mark.asyncio
async def test_get_templates_requires_auth(client):
    await _ensure_templates_seeded()
    r = await client.get("/api/v1/templates")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_templates_returns_seeds_with_metrics(client):
    await _ensure_templates_seeded()
    _, token = await _signup(client)
    r = await client.get("/api/v1/templates", headers=_bearer(token))
    assert r.status_code == 200, r.text
    items = r.json()["data"]
    assert len(items) >= 5
    for t in items:
        assert "metrics" in t
        m = t["metrics"]
        assert m["confidence_label"] == "low"
        assert "methodology_note" in m
        assert m["equity_pct"] + m["defensive_pct"] == 100.0
        assert m["expected_max_drawdown_pct"] <= t["max_drawdown_pct"]


@pytest.mark.asyncio
async def test_get_template_by_key(client):
    await _ensure_templates_seeded()
    _, token = await _signup(client)
    r = await client.get(
        "/api/v1/templates/tech_growth", headers=_bearer(token)
    )
    assert r.status_code == 200, r.text
    t = r.json()["data"]
    assert t["key"] == "tech_growth"
    assert t["risk_bucket"] == "aggressive"
    assert "Technology" in t["sector_whitelist"]


@pytest.mark.asyncio
async def test_get_template_404_for_unknown(client):
    _, token = await _signup(client)
    r = await client.get(
        "/api/v1/templates/does_not_exist", headers=_bearer(token)
    )
    assert r.status_code == 404
