"""LEAP S2/S6 — dossier persistence + multi-ticker comparison assembly.

Async layer over the synchronous autopilot pipeline:

  persist_dossier(db, dossier)        upsert latest-per-ticker (D34)
  load_persisted(db, ticker)          latest stored payload or None
  get_or_build_dossier(db, ticker)    warm order: in-process cache ->
                                      persisted row (same latest bar +
                                      config version) -> full pipeline build
                                      (thread-offloaded), then persist
  build_comparison(db, tickers)       <=4 tickers (D32) side-by-side on the
                                      shared dossier dimensions, with
                                      computed divergence highlights (S6) —
                                      differences are measured, never
                                      editorialized.

Isolation (D30/GS4.4): this module reads/writes autopilot_dossiers only —
never recommendations/publication tables; the regression test asserts it.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.autopilot import AutopilotDossier
from app.services.autopilot import CONFIG_VERSION, build_dossier, validate_ticker

logger = logging.getLogger(__name__)

COMPARISON_MAX_TICKERS = 4

__all__ = [
    "COMPARISON_MAX_TICKERS",
    "persist_dossier",
    "load_persisted",
    "get_or_build_dossier",
    "build_comparison",
]


async def persist_dossier(db: AsyncSession, dossier: dict) -> AutopilotDossier:
    ticker = dossier["ticker"]
    row = (
        await db.execute(
            select(AutopilotDossier).where(AutopilotDossier.ticker == ticker)
        )
    ).scalar_one_or_none()
    payload = json.dumps(dossier, default=str)
    if row is None:
        row = AutopilotDossier(
            ticker=ticker,
            latest_bar_date=(dossier.get("freshness") or {}).get("latest_bar", ""),
            config_version=dossier.get("config_version", CONFIG_VERSION),
            generated_at=datetime.now(UTC),
            payload_json=payload,
        )
        db.add(row)
    else:
        row.latest_bar_date = (dossier.get("freshness") or {}).get("latest_bar", "")
        row.config_version = dossier.get("config_version", CONFIG_VERSION)
        row.generated_at = datetime.now(UTC)
        row.payload_json = payload
    await db.flush()
    await _capture_stance_observation(db, dossier)
    return row


async def _capture_stance_observation(db: AsyncSession, dossier: dict) -> None:
    """Record the served stance for forward scoring (phase 7).

    A forward-scored track record is the one asset that cannot be bought back
    later — it accrues only in wall-clock time — so capture runs from the first
    dossier, long before the reporting surface is useful.

    Deliberately best-effort: a failure here must never break the read path.
    A missing observation costs one data point; a 500 on the dossier costs the
    user their research.
    """
    from app.services.track_record import record_stance

    try:
        summary = dossier.get("summary") or {}
        freshness = dossier.get("freshness") or {}
        latest_bar = freshness.get("latest_bar")
        close = summary.get("latest_close")
        stance = summary.get("stance")
        score = summary.get("composite_score")
        # Every field must be genuinely present — a synthesised observation
        # would poison the only honest record the product has.
        if not (latest_bar and stance and isinstance(close, int | float)
                and isinstance(score, int | float)):
            return
        await record_stance(
            db,
            ticker=dossier["ticker"],
            stance=stance,
            composite_score=float(score),
            observed_bar_date=date.fromisoformat(latest_bar),
            observed_close=float(close),
            avg_confidence=summary.get("avg_confidence"),
            uncertainty_tier=(summary.get("uncertainty") or {}).get("tier"),
            config_version=dossier.get("config_version"),
        )
    except Exception:  # noqa: BLE001 — capture must never break serving
        logger.warning("stance observation capture failed for %s",
                       dossier.get("ticker"), exc_info=True)


async def load_persisted(db: AsyncSession, ticker: str) -> dict | None:
    row = (
        await db.execute(
            select(AutopilotDossier).where(AutopilotDossier.ticker == ticker)
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    payload = json.loads(row.payload_json)
    payload["served_from_persistence"] = True
    return payload


async def get_or_build_dossier(db: AsyncSession, raw_ticker: str) -> dict:
    """Warm path: persisted row when it matches the current config version;
    otherwise a full (thread-offloaded) pipeline build, persisted after."""
    ticker = validate_ticker(raw_ticker)
    persisted = await load_persisted(db, ticker)
    if persisted is not None and persisted.get("config_version") == CONFIG_VERSION:
        return persisted
    dossier = await asyncio.to_thread(build_dossier, ticker)
    await _attach_annotations(dossier)
    await persist_dossier(db, dossier)
    return dossier


def _news_item_id(item: dict) -> str:
    raw = f"{item.get('date','')}|{item.get('title','')}"
    return "n-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


async def _attach_annotations(dossier: dict) -> None:
    """LEAP S9 (D16): flag/provider/canary-gated 'why this matters' notes on
    the dossier News card. Additive and failure-proof: any non-ok status
    leaves the dossier exactly as built, with the status recorded."""
    from app.services.news_annotations import annotate_items

    news = (dossier.get("sections") or {}).get("news_sentiment") or {}
    items = news.get("items_7d") or []
    enriched = [
        {
            "item_id": _news_item_id(i),
            "published_at": i.get("date"),
            "title": i.get("title", ""),
            "summary": i.get("title", ""),
        }
        for i in items
    ]
    try:
        result = await annotate_items(dossier["ticker"], enriched)
    except Exception:  # noqa: BLE001 — annotations must never break dossiers
        news["annotations_status"] = "generation_error"
        return
    news["annotations_status"] = result["status"]
    if result["status"] == "ok" and result["annotations"]:
        by_id = {a["source_binding"]["item_id"]: a for a in result["annotations"]}
        for i in items:
            ann = by_id.get(_news_item_id(i))
            if ann:
                i["why_this_matters"] = ann["annotation"]
                i["annotation_meta"] = {
                    "model": ann["model"],
                    "generated_at": ann["generated_at"],
                    "freshness_stamp": ann["freshness_stamp"],
                }


# ── comparison (S6) ─────────────────────────────────────────────────────────


def _dim(dossier: dict) -> dict:
    """The shared comparison dimensions extracted from one dossier."""
    sections = dossier.get("sections", {})
    tourn = sections.get("model_insight", {}) or {}
    winner = tourn.get("winner") or {}
    summary = dossier.get("summary", {}) or {}
    news = sections.get("news_sentiment", {}) or {}
    return {
        "ticker": dossier["ticker"],
        "latest_bar_date": (dossier.get("freshness") or {}).get("latest_bar"),
        "stance": summary.get("stance"),
        "regime": summary.get("regime"),
        "composite_score": summary.get("composite_score"),
        "news_counts_7d": news.get("counts"),
        "news_available": news.get("available"),
        "selected_model": winner.get("name"),
        "selected_model_key": winner.get("key"),
        "selected_model_kind": winner.get("kind"),
        "selected_model_score": winner.get("score"),
        "validation_sharpe": winner.get("val_sharpe"),
        "freshness": dossier.get("freshness"),
        "served_from_cache": bool(
            dossier.get("served_from_cache") or dossier.get("served_from_persistence")
        ),
    }


def _divergence_highlights(columns: list[dict]) -> list[dict]:
    """Measured disagreements across tickers — facts, not editorial."""
    highlights: list[dict] = []
    stances = {c["ticker"]: c["stance"] for c in columns if c.get("stance")}
    if len(set(stances.values())) > 1:
        highlights.append({"dimension": "stance", "values": stances})
    regimes = {c["ticker"]: c["regime"] for c in columns if c["regime"]}
    if len(set(regimes.values())) > 1:
        highlights.append({"dimension": "regime", "values": regimes})
    models = {c["ticker"]: c["selected_model"] for c in columns if c["selected_model"]}
    if len(set(models.values())) > 1:
        highlights.append({"dimension": "selected_model", "values": models})
    sharpes = {
        c["ticker"]: c["validation_sharpe"]
        for c in columns
        if isinstance(c.get("validation_sharpe"), int | float)
    }
    if len(sharpes) >= 2 and (max(sharpes.values()) - min(sharpes.values())) > 0.5:
        highlights.append({"dimension": "validation_sharpe_spread", "values": sharpes})
    return highlights


async def build_comparison(db: AsyncSession, raw_tickers: list[str]) -> dict:
    tickers = [validate_ticker(t) for t in raw_tickers]
    # dedupe, preserve order
    tickers = list(dict.fromkeys(tickers))
    if not 2 <= len(tickers) <= COMPARISON_MAX_TICKERS:
        raise ValueError(
            f"Comparison takes 2-{COMPARISON_MAX_TICKERS} distinct tickers; got {len(tickers)}."
        )
    columns: list[dict] = []
    errors: dict[str, str] = {}
    for t in tickers:
        try:
            columns.append(_dim(await get_or_build_dossier(db, t)))
        except (ValueError, RuntimeError) as exc:
            errors[t] = str(exc)
    return {
        "tickers": tickers,
        "columns": columns,
        "errors": errors,
        "divergence_highlights": _divergence_highlights(columns),
        "disclaimers": [
            "Research analysis, not investment advice.",
            "Comparison dimensions come from each ticker's dossier; see the "
            "per-ticker dossier for full evidence and limitations.",
        ],
        "generated_at": datetime.now(UTC).isoformat(),
    }
