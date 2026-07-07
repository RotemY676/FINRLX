"""LEAP A2 (D44) — FinGPT dual-score lane: artifact contract + attachment.

The FinGPT scorer runs on the E7 research worker (torch); this module is the
backend half: it loads worker-produced sentiment artifacts and attaches a
second score to each news item so the desk renders BOTH lanes side by side
with an agreement metric. FinGPT scores NEVER influence stances in Track A —
display + A/B logging only (regression-tested).

Artifact contract (schema E.7), one JSON per ticker at
  research/artifacts/fingpt_sentiment/{TICKER}.json:
{
  "ticker": "NVDA",
  "model": "FinGPT/fingpt-sentiment_llama2-13b_lora",
  "generated_at": "...Z",
  "items": { "<sha1-12 of 'date|title'>": {"score": -1.0..1.0, "label": "..."} }
}

Absence of the artifact (worker not deployed / ticker not yet scored) is the
normal state and reports status `research_worker_unavailable`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import pathlib

logger = logging.getLogger(__name__)

ARTIFACT_DIR = pathlib.Path(__file__).resolve().parents[3] / "research" / "artifacts" / "fingpt_sentiment"


def item_key(date_str: str, title: str) -> str:
    return hashlib.sha1(f"{date_str}|{title}".encode("utf-8")).hexdigest()[:12]


def load_artifact(ticker: str) -> dict | None:
    path = ARTIFACT_DIR / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data.get("items"), dict):
            return None
        return data
    except Exception as exc:  # noqa: BLE001 — artifact boundary
        logger.warning("fingpt artifact unreadable for %s: %s", ticker, exc)
        return None


def attach_llm_scores(ticker: str, items: list[dict]) -> dict:
    """Mutates news items in place (adds sentiment_llm / llm_label /
    agreement) and returns the lane status block."""
    artifact = load_artifact(ticker)
    if artifact is None:
        return {"status": "research_worker_unavailable",
                "note": "FinGPT lane appears when the research worker (E7) publishes "
                        "sentiment artifacts; the lexicon lane is unaffected."}
    scored, agreements = 0, []
    for item in items:
        entry = artifact["items"].get(item_key(item.get("date", ""), item.get("title", "")))
        if not entry or not isinstance(entry.get("score"), (int, float)):
            continue
        llm = float(entry["score"])
        item["sentiment_llm"] = round(llm, 3)
        item["llm_label"] = entry.get("label")
        lex = item.get("compound")
        if isinstance(lex, (int, float)):
            agree = (llm >= 0) == (lex >= 0)
            item["agreement"] = agree
            agreements.append(agree)
        scored += 1
    return {
        "status": "ok" if scored else "no_matching_items",
        "model": artifact.get("model"),
        "generated_at": artifact.get("generated_at"),
        "items_scored": scored,
        "agreement_rate": round(sum(agreements) / len(agreements), 3) if agreements else None,
        "note": "A/B display lane — FinGPT scores never influence stances (D44).",
    }
