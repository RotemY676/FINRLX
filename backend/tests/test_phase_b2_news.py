"""Phase B2 — News service tests.

Avoids hitting live RSS feeds. Patches `feedparser.parse` to return
deterministic entries so VADER scoring can be asserted against known
inputs and the cache TTL behavior can be verified.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import news as news_mod
from app.services.news import NewsService, _label, _score_one


def test_label_buckets():
    assert _label(0.50) == "positive"
    assert _label(0.05) == "positive"
    assert _label(0.04) == "neutral"
    assert _label(-0.04) == "neutral"
    assert _label(-0.05) == "negative"
    assert _label(-0.99) == "negative"


def test_score_one_polarity():
    pos, lp = _score_one("Markets surge on strong earnings beat and bright outlook")
    neg, ln = _score_one("Stocks plunge as recession fears mount and losses deepen")
    neu, lneu = _score_one("Company files quarterly statement on schedule")
    assert lp == "positive" and pos > 0
    assert ln == "negative" and neg < 0
    assert lneu == "neutral" or abs(neu) < 0.2


def test_score_empty_text_returns_neutral():
    score, label = _score_one("")
    assert score == 0.0
    assert label == "neutral"


@pytest.mark.asyncio
async def test_get_headlines_aggregates_dedupes_and_scores(monkeypatch):
    """Two feeds with one overlapping title — the merged result keeps only one copy
    and every returned NewsItem carries a VADER score + label."""
    fake_feeds = {
        "https://finance.yahoo.com/news/rssindex": SimpleNamespace(entries=[
            {"title": "Markets rally on upbeat data", "summary": "Big gains across sectors",
             "link": "https://a/1", "published": "Tue, 21 May 2026 09:00:00 GMT"},
            {"title": "Volatility eases", "summary": "VIX falls",
             "link": "https://a/2", "published": "Tue, 21 May 2026 08:00:00 GMT"},
        ]),
        "https://feeds.content.dowjones.io/public/rss/mw_topstories": SimpleNamespace(entries=[
            # Duplicate title casing-different — dedupe should fold it.
            {"title": "MARKETS RALLY ON UPBEAT DATA", "summary": "Same story", "link": "https://b/1", "published": None},
            {"title": "Tech sells off on rate worries", "summary": "Decline accelerates",
             "link": "https://b/2", "published": None},
        ]),
        "https://feeds.content.dowjones.io/public/rss/mw_marketpulse": SimpleNamespace(entries=[]),
    }

    def fake_parse(url):
        return fake_feeds.get(url, SimpleNamespace(entries=[]))

    monkeypatch.setattr(news_mod, "feedparser", SimpleNamespace(parse=fake_parse))
    # Reset the module-level cache so this test starts fresh.
    monkeypatch.setattr(news_mod, "_CACHE", news_mod._Cache())

    svc = NewsService()
    items = await svc.get_headlines(force_refresh=True)

    titles_lower = [i.title.lower() for i in items]
    # Dedup: only one "markets rally" survived
    assert sum(1 for t in titles_lower if "markets rally" in t) == 1
    # All three unique titles present
    assert any("markets rally" in t for t in titles_lower)
    assert any("volatility" in t for t in titles_lower)
    assert any("tech sells off" in t for t in titles_lower)
    # Every item carries a VADER score in [-1, 1] and a non-empty label
    for it in items:
        assert -1.0 <= it.sentiment_compound <= 1.0
        assert it.sentiment_label in {"positive", "neutral", "negative"}

    summary = svc.get_summary(items)
    assert summary["total"] == len(items)
    assert summary["positive"] + summary["neutral"] + summary["negative"] == summary["total"]


@pytest.mark.asyncio
async def test_get_headlines_cache_honors_ttl(monkeypatch):
    """Within TTL the cache returns the same payload without re-fetching."""
    call_count = {"n": 0}
    base_entries = [{"title": "Static headline", "summary": "", "link": "", "published": None}]
    fake_feed = SimpleNamespace(entries=base_entries)

    def fake_parse(_url):
        call_count["n"] += 1
        return fake_feed

    monkeypatch.setattr(news_mod, "feedparser", SimpleNamespace(parse=fake_parse))
    monkeypatch.setattr(news_mod, "_CACHE", news_mod._Cache())

    svc = NewsService()
    first = await svc.get_headlines(force_refresh=True)
    first_calls = call_count["n"]
    # Second call without refresh should hit cache, not re-parse.
    second = await svc.get_headlines(force_refresh=False)
    assert call_count["n"] == first_calls, "cache should suppress re-fetch within TTL"
    assert [i.title for i in first] == [i.title for i in second]
