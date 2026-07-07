"""Desk W1 gates — SPEC-02 API-4/6/7 + DEC-7 flag.

Fixture-only (SPEC-04 R3-Q1): no live providers. Each test maps to a
SPEC-01 acceptance row or a SPEC-02 MUST; names say which.
"""
from __future__ import annotations

import pytest

from app.services.desk_elevation import (
    CAPTION,
    FEATURE_PRIORITY,
    elevate,
)
from app.services.desk_methods import method_block
from app.services.desk_status import (
    SECTION_IDS,
    RateLimiter,
    compute_desk_status,
)

# ── fixtures (SPEC-04 §2) ───────────────────────────────────────────────────


def _row(key, percentile, value=1.0):
    return {"key": key, "name": key, "value": value, "percentile": percentile}


def _dossier_full():
    """FX-FULL — all six engines healthy."""
    return {
        "ticker": "UMC",
        "generated_at": "2026-07-07T07:41:00Z",
        "config_version": "test-cv",
        "freshness": {"latest_bar": "2026-07-04", "bars": 740,
                      "news_source_available": True},
        "summary": {"regime": "uptrend", "stance": "constructive"},
        "price_series": [{"date": "2026-07-04", "close": 25.83}],
        "sections": {
            "technical": {"available": True,
                          "regime": {"label": "uptrend"}},
            "news_sentiment": {
                "available": True,
                "counts": {"news_count_7d": 9},
                "social": {"available": True, "scored": True,
                           "source": "finnhub_social"},
                "divergence": {"status": "computed", "sign_disagreement": False},
            },
            "fundamentals": {"available": True},
            "filings": {"available": True},
            "insider": {"available": True},
            "model_insight": {
                "winner": "regime_filtered_momentum",
                "scoreboard": [],
                "rl": {"status": "completed"},
            },
            "desk": {
                "signal_matrix": [
                    _row("return_5d", 0.67), _row("return_20d", 0.55),
                    _row("volatility_20d", 0.91), _row("drawdown_20d", 0.30),
                    _row("rsi_14", None),
                ],
                "regime_bands": [{"label": "uptrend"}],
            },
        },
    }


def _mutate(d, path, value):
    node = d
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value
    return d


# ── API-4: state machine per engine (US-2.1 AC-3/4; SPEC-02 enum) ──────────


def test_status_full_dossier_all_live_and_shape():
    body = compute_desk_status(_dossier_full(), alerts_unseen=2)
    assert set(s["id"] for s in body["sections"]) == set(SECTION_IDS)
    assert [s["id"] for s in body["sections"]] == SECTION_IDS  # stable order
    for s in body["sections"]:
        assert s["state"] == "live", s
        assert "reason" not in s  # live carries no reason
    assert body["alerts_unseen"] == 2
    assert len(body["fingerprint"]) == 12
    sector = next(s for s in body["sections"] if s["id"] == "sector")
    assert sector["scope"] == "benchmark_only"  # W1 wording (US-3.6)


def test_status_fingerprint_stable_for_same_dossier():
    a = compute_desk_status(_dossier_full())["fingerprint"]
    b = compute_desk_status(_dossier_full())["fingerprint"]
    assert a == b
    changed = compute_desk_status(
        _mutate(_dossier_full(), ["generated_at"], "2026-07-08T00:00:00Z")
    )["fingerprint"]
    assert changed != a


def test_status_e7_gated_tournament_degraded():
    """FX-E7 — DEC-5/US-2.1 AC-4: honest gating, exact detail_code."""
    d = _mutate(_dossier_full(),
                ["sections", "model_insight", "rl", "status"],
                "queued_for_research_run")
    s = {x["id"]: x for x in compute_desk_status(d)["sections"]}
    assert s["tournament"]["state"] == "degraded"
    assert s["tournament"]["detail_code"] == "E7_GATED"
    assert "E7" in s["tournament"]["reason"]


def test_status_e8_fallback_social_degraded():
    """FX-E8 — mentions-only fallback => degraded E8_GATED (US-3.4 AC-1)."""
    d = _mutate(_dossier_full(),
                ["sections", "news_sentiment", "social"],
                {"available": True, "label": "mentions only, unscored"})
    s = {x["id"]: x for x in compute_desk_status(d)["sections"]}
    assert s["social"]["state"] == "degraded"
    assert s["social"]["detail_code"] == "E8_GATED"

    d2 = _mutate(_dossier_full(),
                 ["sections", "news_sentiment", "social"],
                 {"available": False, "reason": "premium_flag_off"})
    s2 = {x["id"]: x for x in compute_desk_status(d2)["sections"]}
    assert s2["social"]["detail_code"] == "E8_GATED"


def test_status_thin_news_coverage():
    """FX-THIN — ≤3 items/7d => THIN_COVERAGE with rendered count."""
    d = _mutate(_dossier_full(),
                ["sections", "news_sentiment", "counts"],
                {"news_count_7d": 3})
    s = {x["id"]: x for x in compute_desk_status(d)["sections"]}
    assert s["news"]["state"] == "degraded"
    assert s["news"]["detail_code"] == "THIN_COVERAGE"
    assert "3" in s["news"]["reason"]


def test_status_partial_signal_nulls():
    """FX-NULLS — ≥3 null values => PARTIAL_DATA (dash-wall ancestry)."""
    d = _dossier_full()
    for r in d["sections"]["desk"]["signal_matrix"][:3]:
        r["value"] = None
    s = {x["id"]: x for x in compute_desk_status(d)["sections"]}
    assert s["technical"]["state"] == "degraded"
    assert s["technical"]["detail_code"] == "PARTIAL_DATA"


def test_status_source_down_states():
    d = _mutate(_dossier_full(), ["sections", "news_sentiment", "available"], False)
    d = _mutate(d, ["sections", "fundamentals"], {"available": False,
                                                  "reason": "finnhub 502"})
    d = _mutate(d, ["sections", "desk", "signal_matrix"], [])
    d = _mutate(d, ["price_series"], [])
    s = {x["id"]: x for x in compute_desk_status(d)["sections"]}
    for sec in ("news", "fundamentals", "technical", "sector"):
        assert s[sec]["state"] == "unavailable"
        assert s[sec]["detail_code"] == "SOURCE_DOWN"
        assert s[sec]["reason"]  # every non-live state names its reason


def test_status_states_are_closed_enum():
    """SPEC-02 R3-T1: no state outside the closed enum can be produced."""
    variants = [
        _dossier_full(),
        _mutate(_dossier_full(), ["sections", "model_insight", "rl", "status"],
                "queued_for_research_run"),
        _mutate(_dossier_full(), ["sections", "news_sentiment", "available"], False),
    ]
    for d in variants:
        for s in compute_desk_status(d)["sections"]:
            assert s["state"] in {"live", "degraded", "unavailable"}
            if s["state"] != "live":
                assert s["detail_code"] in {
                    "E7_GATED", "E8_GATED", "THIN_COVERAGE", "SOURCE_DOWN",
                    "STALE_BEYOND_POLICY", "PARTIAL_DATA",
                }


# ── API-4 rate limiter (SPEC-02 R3-T2) ──────────────────────────────────────


def test_rate_limiter_20_per_minute_with_retry_after():
    t = {"now": 0.0}
    rl = RateLimiter(limit=20, window_s=60.0, clock=lambda: t["now"])
    for _ in range(20):
        ok, _ra = rl.check("1.2.3.4")
        assert ok
    ok, retry = rl.check("1.2.3.4")
    assert not ok and 1 <= retry <= 61
    ok2, _ = rl.check("5.6.7.8")     # per-client isolation
    assert ok2
    t["now"] = 61.0                   # window slides
    ok3, _ = rl.check("1.2.3.4")
    assert ok3


# ── API-7 elevation (QS-2 fixtures: eligibility/tie/regime/all-ineligible) ──


def test_elevation_top3_regime_weight_and_caption():
    rows = [
        _row("return_5d", 0.90),        # u=80, momentum, uptrend ⇒ ×1.15 = 92
        _row("volatility_20d", 0.91),   # u=82, risk, no boost      = 82
        _row("drawdown_20d", 0.14),     # u=72, risk                = 72
        _row("return_20d", 0.60),       # u=20 ×1.15                = 23
        _row("rsi_14", 0.50),           # u=0
    ]
    out = elevate(rows, "uptrend")
    assert out["elevated"] == ["return_5d", "volatility_20d", "drawdown_20d"]
    assert out["caption"] == CAPTION
    assert "not a prediction" in out["caption"]        # RSK-5 wording
    assert out["method"]["tie_break"] == FEATURE_PRIORITY  # disclosed verbatim


def test_elevation_eligibility_none_percentile_never_elevated():
    rows = [_row("return_5d", None), _row("volatility_20d", 0.51)]
    out = elevate(rows, "risk-off")
    assert out["elevated"] == ["volatility_20d"]
    assert "return_5d" not in out["elevated"]


def test_elevation_tie_break_is_priority_order():
    rows = [_row("return_20d", 0.90), _row("return_5d", 0.90)]  # equal scores
    out = elevate(rows, "neutral")  # no boost for either
    assert out["elevated"][0] == "return_5d"  # earlier in FEATURE_PRIORITY


def test_elevation_all_ineligible_yields_honest_note():
    out = elevate([_row("return_5d", None), _row("rsi_14", None)], "uptrend")
    assert out["elevated"] == []
    assert out["note"] and "history" in out["note"]


def test_elevation_regime_weight_flips_ranking_in_risk_off():
    rows = [_row("return_5d", 0.88),       # u=76, momentum
            _row("drawdown_20d", 0.85)]    # u=70, risk ⇒ ×1.15 = 80.5
    out = elevate(rows, "risk-off")
    assert out["elevated"][0] == "drawdown_20d"


# ── API-6 method blocks (US-4.1 anatomy) ────────────────────────────────────


@pytest.mark.parametrize("section", ["signals", "tournament", "news_social",
                                     "fundamentals", "filings", "insider",
                                     "chart", "header", "risk"])
def test_method_block_anatomy_for_all_drawer_sections(section):
    m = method_block(section, _dossier_full())
    assert m is not None, section
    for key in ("summary", "factors", "detail_md", "sources"):
        assert key in m, (section, key)
    assert len(m["summary"].split(".")[0]) > 20      # plain sentence
    assert all("name" in f and "role" in f for f in m["factors"])
    assert m["sources"] and all("name" in s for s in m["sources"])


def test_method_tournament_names_e7_when_gated():
    d = _mutate(_dossier_full(),
                ["sections", "model_insight", "rl", "status"],
                "queued_for_research_run")
    m = method_block("tournament", d)
    assert "E7" in m["detail_md"]
    assert "never simulates" in m["detail_md"]


def test_method_unknown_section_returns_none():
    assert method_block("rl", _dossier_full()) is None  # no drawer for raw rl


# ── DEC-7 flag ──────────────────────────────────────────────────────────────


def test_desk_v2_flag_exists_and_defaults_off():
    from app.core.config import settings
    assert settings.feature_desk_v2 is False


def test_desk_v2_exposed_in_flags_payload():
    import inspect

    from app.api.v1 import flags as flags_mod
    src = inspect.getsource(flags_mod)
    assert '"desk_v2"' in src
