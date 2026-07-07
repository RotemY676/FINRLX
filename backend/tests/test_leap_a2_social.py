"""LEAP A2 — social lane + divergence tests (D43/D44 gates)."""
from __future__ import annotations

from unittest import mock

from app.services.data_providers import social_sentiment as ss


def test_scored_lane_gated_by_premium_flag(monkeypatch):
    from app.core.config import settings

    with mock.patch.object(settings, "finnhub_premium", False):
        out = ss.fetch_social_scored("NVDA")
    assert out == {"available": False, "reason": "premium_flag_off", "source": "finnhub_social"}


def test_mentions_fallback_is_labeled(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {"results": [{"ticker": "NVDA", "rank": 3, "mentions": 512, "upvotes": 2048}]}
    monkeypatch.setattr(ss.httpx, "get", lambda *a, **k: R())
    with mock.patch.object(ss, "_premium_enabled", return_value=False):
        lane = ss.build_social_lane("NVDA")
    assert lane["scored"] is False
    assert lane["label"] == "mentions only, unscored"
    assert lane["trending"] is True and lane["mentions_24h"] == 512
    assert lane["scored_lane_status"] == "premium_flag_off"


def test_mentions_fallback_not_trending_is_honest(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {"results": [{"ticker": "GME", "rank": 1, "mentions": 9}]}
    monkeypatch.setattr(ss.httpx, "get", lambda *a, **k: R())
    lane = ss.fetch_social_mentions("ZZZQ")
    assert lane["available"] is True and lane["trending"] is False
    assert "Not among the top trending" in lane["read"]


def test_scored_lane_aggregation(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {
                "reddit": [
                    {"mention": 10, "positiveMention": 6, "negativeMention": 2, "score": 0.4},
                    {"mention": 20, "positiveMention": 5, "negativeMention": 9, "score": -0.2},
                ],
                "twitter": [],
            }
    monkeypatch.setattr(ss.httpx, "get", lambda *a, **k: R())
    with mock.patch.object(ss, "_premium_enabled", return_value=True), mock.patch.object(
        ss, "_finnhub_key", return_value="k"
    ):
        out = ss.fetch_social_scored("NVDA")
    assert out["available"] and out["scored"]
    assert out["reddit"] == {"mentions_7d": 30, "positive_7d": 11, "negative_7d": 11, "avg_score": 0.1}
    assert out["twitter"] is None


def test_divergence_matrix():
    scored = {"available": True, "scored": True,
              "reddit": {"avg_score": -0.3}, "twitter": {"avg_score": -0.1}}
    d = ss.compute_divergence(0.4, scored)
    assert d["status"] == "diverged" and d["social_avg"] == -0.2
    assert "opposite directions" in d["read"]

    aligned = ss.compute_divergence(0.3, {"available": True, "scored": True,
                                          "reddit": {"avg_score": 0.2}, "twitter": None})
    assert aligned["status"] == "aligned"

    na = ss.compute_divergence(0.3, {"available": True, "scored": False})
    assert na["status"] == "not_applicable" and "mentions-only" in na["reason"]

    assert ss.compute_divergence(None, scored)["status"] == "not_applicable"


def test_dossier_news_section_gains_social_and_divergence(monkeypatch):
    from datetime import date, timedelta
    from app.services import autopilot
    from app.services.single_ticker_analysis import Bars

    dates, closes = [], []
    d, px, i = date(2024, 6, 3), 100.0, 0
    while len(dates) < 420:
        if d.weekday() < 5:
            px *= 1.0 + (0.004 if (i // 20) % 2 == 0 else -0.002)
            dates.append(d); closes.append(round(px, 4)); i += 1
        d += timedelta(days=1)
    bars = Bars(dates=dates, closes=closes, volumes=[1_000_000] * 420,
                highs=[c * 1.01 for c in closes], lows=[c * 0.99 for c in closes])
    monkeypatch.setattr(autopilot, "fetch_history", lambda s, days: bars)
    monkeypatch.setattr(autopilot, "fetch_news", lambda s, limit=20: ([], False))
    import app.services.data_providers.social_sentiment as lane_mod
    monkeypatch.setattr(lane_mod, "build_social_lane",
                        lambda t: {"available": True, "scored": False,
                                   "source": "apewisdom", "label": "mentions only, unscored",
                                   "trending": False, "read": "Not among the top trending tickers on tracked forums right now."})
    autopilot._dossier_cache.clear()
    dossier = autopilot.build_dossier("A2T")
    news = dossier["sections"]["news_sentiment"]
    assert news["social"]["label"] == "mentions only, unscored"
    assert news["divergence"]["status"] == "not_applicable"


# ── FinGPT lane (D44) ───────────────────────────────────────────────────────


def test_fingpt_lane_absent_is_normal(tmp_path, monkeypatch):
    from app.services import fingpt_lane as fl
    monkeypatch.setattr(fl, "ARTIFACT_DIR", tmp_path)
    items = [{"date": "2026-07-01", "title": "X news", "compound": 0.3}]
    status = fl.attach_llm_scores("XTIC", items)
    assert status["status"] == "research_worker_unavailable"
    assert "sentiment_llm" not in items[0]


def test_fingpt_lane_attaches_dual_scores_and_agreement(tmp_path, monkeypatch):
    import json
    from app.services import fingpt_lane as fl
    monkeypatch.setattr(fl, "ARTIFACT_DIR", tmp_path)
    items = [
        {"date": "2026-07-01", "title": "Good quarter", "compound": 0.5},
        {"date": "2026-07-02", "title": "Lawsuit filed", "compound": -0.4},
        {"date": "2026-07-03", "title": "Unscored item", "compound": 0.1},
    ]
    artifact = {
        "ticker": "XTIC", "model": "FinGPT/test-lora", "generated_at": "2026-07-06T00:00:00Z",
        "items": {
            fl.item_key("2026-07-01", "Good quarter"): {"score": 0.8, "label": "positive"},
            fl.item_key("2026-07-02", "Lawsuit filed"): {"score": 0.2, "label": "neutral"},
        },
    }
    (tmp_path / "XTIC.json").write_text(json.dumps(artifact))
    status = fl.attach_llm_scores("XTIC", items)
    assert status["status"] == "ok" and status["items_scored"] == 2
    assert items[0]["sentiment_llm"] == 0.8 and items[0]["agreement"] is True
    assert items[1]["agreement"] is False  # lexicon negative, LLM positive
    assert "sentiment_llm" not in items[2]
    assert status["agreement_rate"] == 0.5
    assert "never influence stances" in status["note"]
