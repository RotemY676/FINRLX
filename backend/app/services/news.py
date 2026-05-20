"""Phase B2 — News intelligence (free-tier RSS + VADER sentiment).

Aggregates headlines from public RSS feeds (Yahoo Finance, MarketWatch)
and scores each with VADER (rule-based, no API key needed). Cached in
memory for ~5 minutes so we don't hammer the upstream feeds on every
page view.

No DB tables: news is ephemeral and re-fetched. If we later want
historical news or per-user feeds, that's a separate phase with a DB
migration.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Free public RSS sources — no auth, no rate-limit headers required.
RSS_SOURCES: list[tuple[str, str]] = [
    ("Yahoo Finance — Top",   "https://finance.yahoo.com/news/rssindex"),
    ("MarketWatch — Top",     "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("MarketWatch — Markets", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"),
]

CACHE_TTL_SECONDS = 300  # 5 min — balances freshness vs upstream politeness


@dataclass
class NewsItem:
    """One headline with its computed sentiment + provenance."""
    source: str
    title: str
    link: str
    summary: str
    published: str | None
    sentiment_compound: float  # VADER compound score [-1, 1]
    sentiment_label: str       # "positive" | "neutral" | "negative"

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published": self.published,
            "sentiment_compound": round(self.sentiment_compound, 4),
            "sentiment_label": self.sentiment_label,
        }


@dataclass
class _Cache:
    items: list[NewsItem] = field(default_factory=list)
    fetched_at: float = 0.0


_CACHE = _Cache()
_ANALYZER = SentimentIntensityAnalyzer()


def _label(score: float) -> str:
    # VADER's recommended cutoffs.
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"


def _score_one(text: str) -> tuple[float, str]:
    if not text.strip():
        return 0.0, "neutral"
    compound = _ANALYZER.polarity_scores(text)["compound"]
    return compound, _label(compound)


def _fetch_one_feed(source_name: str, url: str) -> list[NewsItem]:
    """Synchronous fetch — feedparser is sync, we call via run_in_executor."""
    try:
        parsed = feedparser.parse(url)
    except Exception:
        return []
    out: list[NewsItem] = []
    for entry in parsed.entries[:25]:  # cap per feed
        title = entry.get("title", "").strip()
        if not title:
            continue
        summary = entry.get("summary", "").strip()
        # Score against title + summary so short titles get richer signal.
        score, label = _score_one(f"{title}. {summary}")
        out.append(NewsItem(
            source=source_name,
            title=title,
            link=entry.get("link", ""),
            summary=summary[:240],
            published=entry.get("published") or entry.get("updated"),
            sentiment_compound=score,
            sentiment_label=label,
        ))
    return out


class NewsService:
    """Public surface — async wrapper around the cache + executor."""

    async def get_headlines(self, force_refresh: bool = False) -> list[NewsItem]:
        now = time.time()
        if not force_refresh and _CACHE.items and (now - _CACHE.fetched_at) < CACHE_TTL_SECONDS:
            return _CACHE.items
        loop = asyncio.get_running_loop()
        # Fetch feeds in parallel via threadpool — feedparser is blocking I/O.
        tasks = [
            loop.run_in_executor(None, _fetch_one_feed, name, url)
            for name, url in RSS_SOURCES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        merged: list[NewsItem] = []
        for r in results:
            if isinstance(r, list):
                merged.extend(r)
        # De-dupe by title (RSS often republishes via multiple sources).
        seen: set[str] = set()
        deduped: list[NewsItem] = []
        for item in merged:
            key = item.title.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        _CACHE.items = deduped
        _CACHE.fetched_at = now
        return deduped

    def get_summary(self, items: list[NewsItem]) -> dict:
        n = len(items)
        if n == 0:
            return {"total": 0, "positive": 0, "neutral": 0, "negative": 0, "mean_compound": 0.0}
        pos = sum(1 for i in items if i.sentiment_label == "positive")
        neg = sum(1 for i in items if i.sentiment_label == "negative")
        neu = n - pos - neg
        mean = sum(i.sentiment_compound for i in items) / n
        return {
            "total": n,
            "positive": pos,
            "neutral": neu,
            "negative": neg,
            "mean_compound": round(mean, 4),
        }
