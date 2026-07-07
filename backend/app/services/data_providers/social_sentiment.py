"""LEAP A2 — social-sentiment lane (decision D43/D44).

Order of truth:
  1. Finnhub `/stock/social-sentiment` (Reddit+Twitter, SCORED) — only when
     the operator sets FINNHUB_PREMIUM=1 (third-party comparisons report the
     endpoint is not unlocked on the free tier; we never promise it blind).
  2. ApeWisdom (keyless) — MENTIONS ONLY, no sentiment scores. Rendered with
     the explicit label "mentions only, unscored" (D43).
  3. Honest absence.

Divergence (D44): when BOTH media sentiment (our news lane) and a SCORED
social lane exist, `divergence` compares their signs/magnitudes — a measured
flag, never editorial. With a mentions-only fallback, divergence is
`not_applicable` and says why.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"
APEWISDOM_URL = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/1"
MENTIONS_LABEL = "mentions only, unscored"


def _finnhub_key() -> str | None:
    return getattr(settings, "fundamentals_finnhub_api_key", None) or None


def _premium_enabled() -> bool:
    return bool(getattr(settings, "finnhub_premium", False)) and bool(_finnhub_key())


def fetch_social_scored(ticker: str) -> dict:
    """Finnhub scored lane (premium-gated)."""
    if not _premium_enabled():
        return {"available": False, "reason": "premium_flag_off", "source": "finnhub_social"}
    now = datetime.now(UTC).date()
    try:
        resp = httpx.get(
            f"{FINNHUB_BASE}/stock/social-sentiment",
            params={
                "symbol": ticker,
                "from": (now - timedelta(days=7)).isoformat(),
                "to": now.isoformat(),
                "token": _finnhub_key(),
            },
            timeout=15.0,
        )
        if resp.status_code in (401, 402, 403):
            return {"available": False, "reason": "tier_or_auth", "source": "finnhub_social"}
        if resp.status_code != 200:
            return {"available": False, "reason": f"http_{resp.status_code}", "source": "finnhub_social"}
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 — provider boundary
        logger.warning("finnhub social failed: %s", exc)
        return {"available": False, "reason": "unreachable", "source": "finnhub_social"}

    def _lane(rows: list[dict]) -> dict | None:
        if not rows:
            return None
        mentions = sum(int(r.get("mention", 0)) for r in rows)
        pos = sum(int(r.get("positiveMention", 0)) for r in rows)
        neg = sum(int(r.get("negativeMention", 0)) for r in rows)
        scores = [float(r["score"]) for r in rows if isinstance(r.get("score"), int | float)]
        return {
            "mentions_7d": mentions,
            "positive_7d": pos,
            "negative_7d": neg,
            "avg_score": round(sum(scores) / len(scores), 4) if scores else None,
        }

    reddit = _lane(data.get("reddit") or [])
    twitter = _lane(data.get("twitter") or [])
    if reddit is None and twitter is None:
        return {"available": False, "reason": "no_rows", "source": "finnhub_social"}
    return {
        "available": True,
        "scored": True,
        "source": "finnhub_social",
        "reddit": reddit,
        "twitter": twitter,
    }


def fetch_social_mentions(ticker: str) -> dict:
    """ApeWisdom keyless fallback — buzz only, honestly labeled."""
    try:
        resp = httpx.get(APEWISDOM_URL, timeout=15.0)
        if resp.status_code != 200:
            return {"available": False, "reason": f"http_{resp.status_code}", "source": "apewisdom"}
        rows = (resp.json() or {}).get("results") or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("apewisdom failed: %s", exc)
        return {"available": False, "reason": "unreachable", "source": "apewisdom"}
    hit = next((r for r in rows if str(r.get("ticker", "")).upper() == ticker.upper()), None)
    if hit is None:
        return {
            "available": True,
            "scored": False,
            "source": "apewisdom",
            "label": MENTIONS_LABEL,
            "trending": False,
            "read": "Not among the top trending tickers on tracked forums right now.",
        }
    return {
        "available": True,
        "scored": False,
        "source": "apewisdom",
        "label": MENTIONS_LABEL,
        "trending": True,
        "rank": hit.get("rank"),
        "mentions_24h": hit.get("mentions"),
        "upvotes_24h": hit.get("upvotes"),
        "mentions_change_24h": hit.get("rank_24h_ago"),
    }


def build_social_lane(ticker: str) -> dict:
    scored = fetch_social_scored(ticker)
    if scored.get("available"):
        return scored
    fallback = fetch_social_mentions(ticker)
    fallback["scored_lane_status"] = scored.get("reason")
    return fallback


def compute_divergence(media_avg: float | None, social: dict) -> dict:
    """Measured media-vs-social disagreement (D44)."""
    if not social.get("available") or not social.get("scored"):
        return {
            "status": "not_applicable",
            "reason": "social lane is mentions-only or unavailable — divergence "
                      "requires two scored lanes",
        }
    scores = [
        lane["avg_score"]
        for lane in (social.get("reddit"), social.get("twitter"))
        if lane and lane.get("avg_score") is not None
    ]
    if media_avg is None or not scores:
        return {"status": "not_applicable", "reason": "missing a scored side"}
    social_avg = sum(scores) / len(scores)
    diverged = (media_avg > 0.05 and social_avg < -0.05) or (
        media_avg < -0.05 and social_avg > 0.05
    )
    return {
        "status": "diverged" if diverged else "aligned",
        "media_avg": round(media_avg, 4),
        "social_avg": round(social_avg, 4),
        "read": (
            "Media tone and social-forum tone point in opposite directions"
            if diverged
            else "Media and social lanes broadly agree"
        ),
    }
