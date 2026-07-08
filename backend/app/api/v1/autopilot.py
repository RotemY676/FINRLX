"""PROGRAM LEAP S2 — Autopilot dossier endpoint.

GET /api/v1/autopilot/dossier?ticker=NVDA

Returns the full 360-degree research dossier as JSON (schema E.4).
Mirrors /analysis/single-ticker conventions: strict server-side ticker
validation (D40), thread-offloaded pipeline, clean error mapping.
Dossiers are research analysis, not recommendations (D30).
"""
from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.autopilot import HISTORY_DAYS_DEFAULT, build_dossier
from app.services.autopilot_store import (
    COMPARISON_MAX_TICKERS,
    build_comparison,
    persist_dossier,
)
from app.services.desk_elevation import elevate
from app.services.desk_methods import method_block
from app.services.desk_status import RateLimiter, compute_desk_status

logger = logging.getLogger(__name__)
router = APIRouter()

# Desk W1 (SPEC-02 API-4): in-process limiter, 20/min per client (SO-1).
_status_limiter = RateLimiter(limit=20, window_s=60.0)


@router.get(
    "/autopilot/dossier",
    summary="360-degree automatic research dossier for one ticker",
    description=(
        "Zero-config pipeline: ingest prices, enrich with news+sentiment, "
        "compute the technical vocabulary, run the automatic model "
        "tournament (walk-forward validated, overfitting-penalized), and "
        "return the assembled dossier with per-stage timings, evidence, "
        "and disclaimers."
    ),
)
async def autopilot_dossier(
    ticker: str = Query(..., min_length=1, max_length=10,
                        description="Stock ticker symbol (e.g. NVDA, BRK.B)"),
    db: AsyncSession = Depends(get_db),
):
    t0 = time.time()
    try:
        dossier = await asyncio.to_thread(
            build_dossier, ticker, history_days=HISTORY_DAYS_DEFAULT
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # noqa: BLE001 — boundary; clean 500
        logger.exception("autopilot dossier failed for %s", ticker)
        raise HTTPException(status_code=500, detail=f"Autopilot failed: {e}")
    try:
        await persist_dossier(db, dossier)
        await db.commit()
    except Exception:  # noqa: BLE001 — persistence must never fail the read path
        logger.exception("dossier persistence failed for %s (serving anyway)", ticker)
        await db.rollback()

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info("autopilot dossier %s: %d ms (cache=%s)",
                dossier["ticker"], elapsed_ms, dossier.get("served_from_cache"))
    return {"meta": {"duration_ms": elapsed_ms}, "data": dossier}


@router.get(
    "/autopilot/compare",
    summary="Side-by-side comparison of 2-4 tickers on shared dossier dimensions",
    description=(
        "Serves each ticker's dossier (persisted when current, freshly built "
        "otherwise) and assembles the shared comparison dimensions plus "
        "measured divergence highlights. Research analysis, not advice."
    ),
)
async def autopilot_compare(
    tickers: str = Query(..., description="Comma-separated tickers, 2-4, e.g. NVDA,AMD"),
    db: AsyncSession = Depends(get_db),
):
    raw = [t for t in (p.strip() for p in tickers.split(",")) if t]
    if not 2 <= len(raw) <= COMPARISON_MAX_TICKERS:
        raise HTTPException(
            status_code=400,
            detail=f"Provide 2-{COMPARISON_MAX_TICKERS} comma-separated tickers.",
        )
    try:
        result = await build_comparison(db, raw)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"data": result}


# LEAP A4 (D42) — section endpoints: the desk streams each section
# independently; slices come from the (persisted-or-built) dossier.
_SECTION_MAP = {
    "header": lambda d: {"ticker": d["ticker"], "summary": d["summary"],
                          "freshness": d["freshness"], "generated_at": d["generated_at"],
                          "config_version": d["config_version"],
                          "disclaimers": d["disclaimers"]},
    "chart": lambda d: {"price_series": d.get("price_series", []),
                         "regime_bands": d["sections"]["desk"].get("regime_bands", []),
                         "event_markers": d["sections"]["desk"].get("event_markers", [])},
    "signals": lambda d: {"signal_matrix": d["sections"]["desk"].get("signal_matrix", []),
                           "technical": d["sections"]["technical"]},
    "tournament": lambda d: {**d["sections"]["model_insight"],
                              "split_windows": d["sections"]["desk"].get("split_windows", [])},
    "rl": lambda d: d["sections"]["model_insight"].get("rl", {}),
    "news_social": lambda d: d["sections"]["news_sentiment"],
    "fundamentals": lambda d: d["sections"]["fundamentals"],
    "filings": lambda d: d["sections"]["filings"],
    "insider": lambda d: d["sections"]["insider"],
    "risk": lambda d: {"regime_bands": d["sections"]["desk"].get("regime_bands", []),
                        "signal_matrix": [r for r in d["sections"]["desk"].get("signal_matrix", [])
                                          if "volatility" in r["key"] or "drawdown" in r["key"]
                                          or "turbulence" in r["key"]]},
}


# NOTE: /status MUST be declared before the generic /{section} route.
# Starlette matches routes in definition order, so /desk/{ticker}/{section}
# would otherwise shadow /desk/{ticker}/status — capturing section="status"
# and returning a 404 "unknown section" (this shipped the first Desk-v2 crash).
@router.get(
    "/autopilot/desk/{ticker}/status",
    summary="Desk W1 (SPEC-02 API-4) — the six engine-dial states + alerts",
    description=(
        "Dial truth has ONE source: this endpoint. Derived from the "
        "PERSISTED dossier only — a status poll never triggers a pipeline "
        "build. Closed state enum (live|degraded|unavailable) with "
        "detail_code; SPEC-02 R3-T1. Rate-limited 20/min per client (SO-1)."
    ),
)
async def autopilot_desk_status(
    ticker: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client = (request.client.host if request.client else "unknown")
    allowed, retry_after = _status_limiter.check(client)
    if not allowed:
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            content={"error": {"code": "RATE_LIMITED",
                               "message": "status polls are limited to 20/min",
                               "retry_after_s": retry_after}},
        )
    from app.services.autopilot import validate_ticker
    from app.services.autopilot_store import load_persisted

    try:
        sym = validate_ticker(ticker)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "TICKER_INVALID", "message": str(e)}},
        )
    dossier = await load_persisted(db, sym)
    if dossier is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NO_DOSSIER",
                               "message": "no persisted dossier for this "
                                          "ticker — start research first"}},
        )
    alerts = await _open_ticker_alerts(db, dossier["ticker"])
    body = compute_desk_status(dossier, alerts_unseen=len(alerts))
    etag = f'W/"{body["fingerprint"]}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return JSONResponse(content={"data": body}, headers={"ETag": etag})


@router.get(
    "/autopilot/desk/{ticker}/{section}",
    summary="One Analyst Desk section (D42 streaming contract)",
)
async def autopilot_desk_section(
    ticker: str,
    section: str,
    db: AsyncSession = Depends(get_db),
):
    from app.services.autopilot_store import get_or_build_dossier

    if section not in _SECTION_MAP:
        raise HTTPException(status_code=404,
                            detail=f"Unknown section; valid: {sorted(_SECTION_MAP)}")
    try:
        dossier = await get_or_build_dossier(db, ticker)
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        await db.rollback()
        raise HTTPException(status_code=502, detail=str(e))
    try:
        payload = _SECTION_MAP[section](dossier)
    except KeyError:
        payload = {"available": False, "reason": "section_missing_in_dossier"}
    # Desk W1 (SPEC-02 API-6, additive): Forensic-drawer method block.
    _method = method_block(section, dossier)
    if _method is not None:
        payload["method"] = _method
    # Desk W1 (SPEC-02 API-7): elevation block on the signals payload —
    # ranks unusualness only, with its full method disclosed inline (QS-2).
    if section == "signals":
        _regime = ((dossier.get("summary") or {}).get("regime")
                   or ((dossier.get("sections") or {}).get("technical") or {})
                   .get("regime", {}).get("label", "neutral"))
        payload["elevation"] = elevate(payload.get("signal_matrix") or [],
                                       str(_regime))
    if section == "header":
        # LEAP A6: surface S8 material-change alerts for this ticker so the
        # desk can show them live; evidence-linked, read-only.
        payload["alerts"] = await _open_ticker_alerts(db, dossier["ticker"])
    return {"data": {"ticker": dossier["ticker"], "section": section,
                     "generated_at": dossier["generated_at"], "payload": payload}}


async def _open_ticker_alerts(db: AsyncSession, ticker: str) -> list[dict]:
    from sqlalchemy import select

    from app.models.ops import Incident
    from app.services.autopilot_refresh import INCIDENT_TITLE_PREFIX

    rows = (
        await db.execute(
            select(Incident)
            .where(
                Incident.title == f"{INCIDENT_TITLE_PREFIX}{ticker}",
                Incident.status != "resolved",
            )
            .order_by(Incident.created_at.desc())
            .limit(3)
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "severity": r.severity,
            "description": r.description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
