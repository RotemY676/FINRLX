"""Operation Credibility K1 — production data-health diagnostic.

GET /api/v1/ops/data-health?tickers=UMC,NVDA

For each ticker (max 5), probes every price source LIVE and reports what the
dossier pipeline would actually see: per-source bar depth and latest date,
which source fetch_history serves, and the feature population rate. This is
the tool that turns "the signals are all dashes" from a screenshot into a
named root cause, in production, in one request.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.api.deps import make_meta
from app.schemas.common import ApiResponse

router = APIRouter(tags=["ops"])

DEFAULT_QA_TICKERS = "UMC,NVDA,AAPL"
PROBE_DAYS = 420


def _probe_ticker(sym: str) -> dict:
    import app.services.single_ticker_analysis as sta

    end = date.today()
    start = end - timedelta(days=PROBE_DAYS)
    out: dict = {"ticker": sym, "sources": {}}

    for name, fn in (
        ("yfinance", lambda: sta._fetch_history_yfinance(sym, start, end)),
        ("stooq", lambda: sta._bars_from_stooq(sym, start, end)),
    ):
        try:
            bars = fn()
            out["sources"][name] = {
                "ok": bool(bars.closes),
                "bars": len(bars.closes),
                "latest": bars.dates[-1].isoformat() if bars.dates else None,
            }
        except Exception as exc:  # noqa: BLE001 — diagnostic must never crash
            out["sources"][name] = {"ok": False, "error": str(exc)[:160]}

    try:
        served = sta.fetch_history(sym, PROBE_DAYS)
        feats = sta.compute_features(served.closes, served.volumes, [], False)
        populated = sum(1 for v in feats.values() if v[0] is not None)
        out["served"] = {
            "bars": len(served.closes),
            "latest": served.dates[-1].isoformat() if served.dates else None,
            "features_populated": f"{populated}/{len(feats)}",
            "dash_wall": populated == 0,
        }
    except Exception as exc:  # noqa: BLE001
        out["served"] = {"error": str(exc)[:160]}
    return out


@router.get("/ops/data-health")
def data_health(tickers: str = Query(DEFAULT_QA_TICKERS)):
    syms = [t.strip().upper() for t in tickers.split(",") if t.strip()][:5]
    return ApiResponse(
        meta=make_meta(),
        data={"probes": [_probe_ticker(s) for s in syms]},
    )
