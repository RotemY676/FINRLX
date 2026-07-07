"""Desk W1 — API-4 dial aggregator (SPEC-02 \u00A72).

Derives the six engine-dial states from a PERSISTED dossier. This module is
pure over the dossier dict so the state machine is fixture-testable; the
endpoint in api/v1/autopilot.py adds alerts and transport concerns.

Contract (closed enums \u2014 clients switch exhaustively; SPEC-02 R3-T1):
  state:        live | degraded | unavailable
  detail_code:  E7_GATED | E8_GATED | THIN_COVERAGE | SOURCE_DOWN
                | STALE_BEYOND_POLICY | PARTIAL_DATA
Every non-live state carries a renderable ``reason`` and a ``detail_code``.

Dial truth has ONE source (design tenet 3): the frontend MUST NOT infer
dial states from section-fetch outcomes.
"""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

SECTION_IDS = ["technical", "tournament", "news", "social", "fundamentals", "sector"]

THIN_NEWS_7D = 3          # \u2264 this many 7d items => THIN_COVERAGE
PARTIAL_NULLS = 3         # \u2265 this many null matrix values => PARTIAL_DATA
MENTIONS_LABEL = "mentions only, unscored"  # D43 fallback label (verbatim)


def _fingerprint(dossier: dict) -> str:
    basis = "|".join(str(dossier.get(k)) for k in ("ticker", "generated_at", "config_version")) \
            + "|" + str((dossier.get("freshness") or {}).get("latest_bar"))
    return hashlib.sha1(basis.encode()).hexdigest()[:12]


def _dial(section_id: str, state: str, *, reason: str | None = None,
          detail_code: str | None = None, **extra) -> dict:
    d: dict = {"id": section_id, "state": state}
    if state != "live":
        d["reason"] = reason or "unavailable"
        d["detail_code"] = detail_code or "SOURCE_DOWN"
    d.update(extra)
    return d


def _technical(dossier: dict) -> dict:
    desk = (dossier.get("sections") or {}).get("desk") or {}
    matrix = desk.get("signal_matrix") or []
    if not matrix:
        return _dial("technical", "unavailable",
                     reason="signal matrix missing from dossier",
                     detail_code="SOURCE_DOWN")
    nulls = sum(1 for r in matrix if r.get("value") is None)
    if nulls >= PARTIAL_NULLS:
        return _dial("technical", "degraded",
                     reason=f"{nulls} signals unpopulated \u2014 data-depth limitation",
                     detail_code="PARTIAL_DATA")
    fresh = dossier.get("freshness") or {}
    return _dial("technical", "live", freshness_bar=fresh.get("latest_bar"))


def _tournament(dossier: dict) -> dict:
    mi = (dossier.get("sections") or {}).get("model_insight") or {}
    rl = mi.get("rl") or {}
    if rl.get("status") == "queued_for_research_run":
        return _dial("tournament", "degraded",
                     reason="RL leg queued (E7)", detail_code="E7_GATED")
    if rl.get("status") == "insufficient_history":
        return _dial("tournament", "degraded",
                     reason="insufficient history for RL candidates",
                     detail_code="PARTIAL_DATA")
    if not mi.get("winner") and not mi.get("selected"):
        return _dial("tournament", "unavailable",
                     reason="tournament results missing",
                     detail_code="SOURCE_DOWN")
    return _dial("tournament", "live")


def _news(dossier: dict) -> dict:
    ns = (dossier.get("sections") or {}).get("news_sentiment") or {}
    if not ns.get("available"):
        return _dial("news", "unavailable",
                     reason=ns.get("note") or "news source unavailable",
                     detail_code="SOURCE_DOWN")
    counts = ns.get("counts") or {}
    n7 = counts.get("news_count_7d", counts.get("count_7d"))
    if isinstance(n7, int) and n7 <= THIN_NEWS_7D:
        return _dial("news", "degraded",
                     reason=f"7-day news count: {n7} \u2014 thin coverage",
                     detail_code="THIN_COVERAGE")
    return _dial("news", "live")


def _social(dossier: dict) -> dict:
    ns = (dossier.get("sections") or {}).get("news_sentiment") or {}
    lane = ns.get("social") or {}
    if lane.get("available") is False:
        reason = str(lane.get("reason") or "")
        if "premium" in reason:
            return _dial("social", "degraded",
                         reason="scored lane needs Finnhub tier (E8)",
                         detail_code="E8_GATED")
        return _dial("social", "unavailable",
                     reason=lane.get("reason") or "social lane unavailable",
                     detail_code="SOURCE_DOWN")
    if lane.get("label") == MENTIONS_LABEL or lane.get("scored") is False:
        return _dial("social", "degraded",
                     reason="mentions-only fallback (E8)",
                     detail_code="E8_GATED")
    return _dial("social", "live")


def _fundamentals(dossier: dict) -> dict:
    fu = (dossier.get("sections") or {}).get("fundamentals") or {}
    if not fu.get("available"):
        return _dial("fundamentals", "unavailable",
                     reason=fu.get("reason") or "fundamentals source unavailable",
                     detail_code="SOURCE_DOWN")
    return _dial("fundamentals", "live")


def _sector(dossier: dict) -> dict:
    # W1: benchmark-only scope by design; the panel copy states this plainly.
    has_series = bool(dossier.get("price_series"))
    if not has_series:
        return _dial("sector", "unavailable",
                     reason="price series unavailable",
                     detail_code="SOURCE_DOWN")
    return _dial("sector", "live", scope="benchmark_only")


def compute_desk_status(dossier: dict, alerts_unseen: int = 0) -> dict:
    """API-4 body from a persisted dossier (never triggers a build)."""
    sections = [
        _technical(dossier), _tournament(dossier), _news(dossier),
        _social(dossier), _fundamentals(dossier), _sector(dossier),
    ]
    return {
        "fingerprint": _fingerprint(dossier),
        "sections": sections,
        "alerts_unseen": int(alerts_unseen),
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


class RateLimiter:
    """Sliding-window limiter for API-4 (SPEC-02: 20/min per client).

    In-process by design for W1 (single Railway instance); the clock is
    injectable for deterministic tests.
    """

    def __init__(self, limit: int = 20, window_s: float = 60.0, clock=time.monotonic):
        self.limit, self.window_s, self._clock = limit, window_s, clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, int]:
        """(allowed, retry_after_s). Records the hit when allowed."""
        now = self._clock()
        q = self._hits[key]
        while q and now - q[0] > self.window_s:
            q.popleft()
        if len(q) >= self.limit:
            return False, max(1, int(self.window_s - (now - q[0])) + 1)
        q.append(now)
        return True, 0
