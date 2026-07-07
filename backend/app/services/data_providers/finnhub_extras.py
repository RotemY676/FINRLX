"""LEAP A1 — Finnhub alternative-data adapters (decision D43).

Three documented Finnhub endpoints the desk renders as CONTEXT (never as
signals, and never influencing stances — regression-tested):

  insider_sentiment(ticker)   /stock/insider-sentiment — monthly MSPR
                              (-100..+100 insider buy/sell pressure)
  filings_tone(ticker)        /stock/filings-sentiment on the latest 10-K/10-Q
                              (Loughran-McDonald word lists)
  similarity_index(ticker)    /stock/similarity-index — YoY cosine similarity
                              of 10-K/10-Q language (disclosure-change signal)

All require FINNHUB_API_KEY (same key the fundamentals provider uses).
Absence of the key, an endpoint error, or a payment-required tier returns
{"available": False, "reason": ...} — the UI names the missing source.

Caveat copy (binding, from the Analyst Desk research report):
MSPR is documented as noisy in practitioner analysis; it renders with the
NOISE_CAVEAT verbatim.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE = "https://finnhub.io/api/v1"
NOISE_CAVEAT = (
    "Insider MSPR is a noisy contextual gauge — insiders transact for many "
    "reasons unrelated to their view of the stock; practitioner analyses find "
    "the raw signal weak. Shown for context, never as a signal."
)


def _key() -> str | None:
    return getattr(settings, "fundamentals_finnhub_api_key", None) or None


def _get(path: str, params: dict[str, Any]) -> tuple[dict | None, str | None]:
    key = _key()
    if not key:
        return None, "no_api_key"
    try:
        resp = httpx.get(
            f"{BASE}{path}", params={**params, "token": key}, timeout=15.0
        )
        if resp.status_code in (401, 402, 403):
            return None, "tier_or_auth"
        if resp.status_code != 200:
            return None, f"http_{resp.status_code}"
        return resp.json(), None
    except Exception as exc:  # noqa: BLE001 — provider boundary
        logger.warning("finnhub %s failed: %s", path, exc)
        return None, "unreachable"


def insider_sentiment(ticker: str) -> dict:
    now = datetime.now(UTC).date()
    frm = (now - timedelta(days=400)).isoformat()
    data, err = _get(
        "/stock/insider-sentiment", {"symbol": ticker, "from": frm, "to": now.isoformat()}
    )
    if err or not data:
        return {"available": False, "reason": err or "empty", "source": "finnhub_insider"}
    rows = data.get("data") or []
    if not rows:
        return {"available": False, "reason": "no_rows", "source": "finnhub_insider"}
    rows = sorted(rows, key=lambda r: (r.get("year", 0), r.get("month", 0)))[-12:]
    series = [
        {"year": r.get("year"), "month": r.get("month"),
         "mspr": r.get("mspr"), "net_change": r.get("change")}
        for r in rows
    ]
    return {
        "available": True,
        "source": "finnhub_insider",
        "latest_mspr": series[-1]["mspr"],
        "series_12m": series,
        "caveat": NOISE_CAVEAT,
    }


def filings_tone(ticker: str) -> dict:
    filings, err = _get("/stock/filings", {"symbol": ticker})
    if err or not filings:
        return {"available": False, "reason": err or "empty", "source": "finnhub_filings"}
    reports = [f for f in filings if f.get("form") in ("10-K", "10-Q")]
    if not reports:
        return {"available": False, "reason": "no_10k_10q", "source": "finnhub_filings"}
    latest = sorted(reports, key=lambda f: str(f.get("filedDate", "")))[-1]
    access = latest.get("accessNumber")
    tone, err2 = _get("/stock/filings-sentiment", {"accessNumber": access})
    if err2 or not tone:
        return {"available": False, "reason": err2 or "empty", "source": "finnhub_filings"}
    s = tone.get("sentiment") or {}
    return {
        "available": True,
        "source": "finnhub_filings",
        "form": latest.get("form"),
        "filed_date": latest.get("filedDate"),
        "access_number": access,
        "tone": {
            "negative": s.get("negative"),
            "positive": s.get("positive"),
            "uncertainty": s.get("uncertainty"),
            "litigious": s.get("litigious"),
            "polarity": s.get("polarity"),
        },
        "method": "Loughran-McDonald word lists (Finnhub filings NLP)",
    }


def similarity_index(ticker: str) -> dict:
    data, err = _get("/stock/similarity-index", {"symbol": ticker, "freq": "annual"})
    if err or not data:
        return {"available": False, "reason": err or "empty", "source": "finnhub_similarity"}
    rows = data.get("similarity") or []
    if not rows:
        return {"available": False, "reason": "no_rows", "source": "finnhub_similarity"}
    latest = sorted(rows, key=lambda r: str(r.get("filedDate", "")))[-1]
    return {
        "available": True,
        "source": "finnhub_similarity",
        "form": latest.get("form"),
        "filed_date": latest.get("filedDate"),
        # cosine similarity of full 10-K vs prior year (1.0 = unchanged text)
        "cosine_all": latest.get("cosineAll") or latest.get("cosine"),
        "read": (
            "Lower similarity vs last year means the company changed its "
            "disclosure language materially — a documented "
            "change-in-disclosure research signal, not a directional call."
        ),
    }
