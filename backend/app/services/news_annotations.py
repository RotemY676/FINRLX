"""Program LEAP S9 — sourced "why this matters" news annotations
(decision D16, contract Appendix E.2).

Every annotation is bound to exactly one source news item and survives a
strict validator before anything reaches a user:

  contract per item:
    {item_id, annotation (<=2 sentences), source_binding {item_id,
     published_at}, model, generated_at, freshness_stamp}

  validator rejects:
    - missing/mismatched source_binding (id or published_at)
    - more than MAX_SENTENCES sentences
    - advice-language (imperative/assurance verbs: buy, sell, should, must,
      guaranteed, will outperform, ...)
    - any ticker-like symbol not present in the source item's own text
    - empty/whitespace annotations

  canary (D16): the feature turns on for a batch only after CANARY_SIZE
  consecutive validated annotations; a single rejection fails the canary and
  the batch ships unannotated (flag stays effectively off for the run).

Flag: settings.insights_annotations (default OFF). Without a configured LLM
provider the annotator reports status "provider_unconfigured" and touches
nothing — the existing empty-state pattern renders in the UI.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import settings
from app.services.llm.provider import StubProviderError
from app.services.llm.router import get_provider
from app.services.llm.types import LLMMessage

logger = logging.getLogger(__name__)

MAX_SENTENCES = 2
CANARY_SIZE = 20

# Advice / assurance language that must never appear (D16 + safe-language rules).
_ADVICE_PATTERNS = re.compile(
    r"\b(buy|sell|short|go long|should|must|need to|guaranteed?|assure[ds]?|"
    r"can't lose|cannot lose|will (outperform|beat|rise|fall|double|soar|crash)|"
    r"sure thing|no[- ]brainer|act now)\b",
    re.IGNORECASE,
)
_TICKER_LIKE = re.compile(r"\b[A-Z]{2,6}(?:\.[A-Z])?\b")
# Common English words that match the ticker pattern but aren't symbols.
_TICKER_STOPWORDS = {
    "A", "AI", "CEO", "CFO", "CTO", "EPS", "ETF", "EU", "FDA", "FED", "GDP",
    "IPO", "NEWS", "NYSE", "PE", "Q", "SEC", "THE", "US", "USA", "USD", "VS",
}

__all__ = [
    "AnnotationRejection",
    "validate_annotation",
    "run_canary",
    "annotate_items",
    "MAX_SENTENCES",
    "CANARY_SIZE",
]


@dataclass(frozen=True)
class AnnotationRejection:
    item_id: str
    reason: str


def _sentence_count(text: str) -> int:
    parts = [p for p in re.split(r"[.!?]+(?:\s|$)", text.strip()) if p.strip()]
    return len(parts)


def _foreign_tickers(annotation: str, source_text: str) -> list[str]:
    source_upper = source_text.upper()
    found = []
    for sym in set(_TICKER_LIKE.findall(annotation)):
        if sym in _TICKER_STOPWORDS:
            continue
        if sym not in source_upper:
            found.append(sym)
    return sorted(found)


def validate_annotation(candidate: dict, source_item: dict) -> AnnotationRejection | None:
    """None = valid; otherwise the exact reason (tested adversarially)."""
    item_id = str(source_item.get("item_id", ""))
    text = (candidate.get("annotation") or "").strip()
    binding = candidate.get("source_binding") or {}
    if not text:
        return AnnotationRejection(item_id, "empty_annotation")
    if str(binding.get("item_id", "")) != item_id or not binding.get("published_at"):
        return AnnotationRejection(item_id, "missing_or_mismatched_source_binding")
    if str(binding.get("published_at")) != str(source_item.get("published_at")):
        return AnnotationRejection(item_id, "published_at_mismatch")
    if _sentence_count(text) > MAX_SENTENCES:
        return AnnotationRejection(item_id, "too_many_sentences")
    if _ADVICE_PATTERNS.search(text):
        return AnnotationRejection(item_id, "advice_language")
    src_text = f"{source_item.get('title', '')} {source_item.get('summary', '')}"
    foreign = _foreign_tickers(text, src_text)
    if foreign:
        return AnnotationRejection(item_id, f"unbound_tickers:{','.join(foreign)}")
    return None


def run_canary(candidates: list[dict], sources: dict[str, dict]) -> tuple[bool, list[AnnotationRejection]]:
    """A batch earns display only if its first CANARY_SIZE (or all, when
    fewer) candidates validate with zero rejections."""
    rejections: list[AnnotationRejection] = []
    for cand in candidates[:CANARY_SIZE]:
        src = sources.get(str((cand.get("source_binding") or {}).get("item_id", "")))
        if src is None:
            rejections.append(AnnotationRejection(str(cand.get("item_id", "?")), "unknown_source"))
            continue
        rej = validate_annotation(cand, src)
        if rej:
            rejections.append(rej)
    return (len(rejections) == 0, rejections)


_PROMPT = (
    "You annotate financial news for a research tool. For the item below, "
    "write WHY IT MATTERS for someone researching {ticker}: at most two "
    "sentences, factual, no advice, no predictions, no imperatives. "
    "Respond with the annotation text only.\n\nTitle: {title}\nSummary: {summary}"
)


async def _generate_one(provider, ticker: str, item: dict) -> dict:
    resp = await provider.chat(
        [LLMMessage(role="user", content=_PROMPT.format(
            ticker=ticker, title=item.get("title", ""), summary=item.get("summary", "")))],
        max_tokens=160,
        temperature=0.2,
    )
    return {
        "item_id": str(item["item_id"]),
        "annotation": (resp.content or "").strip(),
        "source_binding": {
            "item_id": str(item["item_id"]),
            "published_at": str(item.get("published_at")),
        },
        "model": f"{provider.name}:{provider.model}",
        "generated_at": datetime.now(UTC).isoformat(),
        "freshness_stamp": str(item.get("published_at")),
    }


async def annotate_items(ticker: str, items: list[dict]) -> dict:
    """Flag-gated, provider-gated, canary-gated annotation of news items.

    Returns {status, annotations, rejections}; on any gate failing, the
    annotations list is empty and status says exactly why — the UI keeps its
    existing unannotated rendering (GS8.2-style flag-off regression).
    """
    if not settings.insights_annotations:
        return {"status": "flag_off", "annotations": [], "rejections": []}
    provider = get_provider()
    if provider is None:
        return {"status": "provider_unconfigured", "annotations": [], "rejections": []}
    candidates: list[dict] = []
    sources: dict[str, dict] = {}
    for item in items:
        if "item_id" not in item:
            continue
        sources[str(item["item_id"])] = item
        try:
            candidates.append(await _generate_one(provider, ticker, item))
        except StubProviderError:
            return {"status": "provider_unconfigured", "annotations": [], "rejections": []}
        except Exception as exc:  # noqa: BLE001 — annotation must never break the pipeline
            logger.warning("annotation generation failed for %s: %s", item.get("item_id"), exc)
            return {"status": "generation_error", "annotations": [], "rejections": []}
    ok, rejections = run_canary(candidates, sources)
    if not ok:
        logger.warning(
            "annotation canary failed for %s: %s",
            ticker,
            [f"{r.item_id}:{r.reason}" for r in rejections[:5]],
        )
        return {
            "status": "canary_failed",
            "annotations": [],
            "rejections": [r.__dict__ for r in rejections],
        }
    return {"status": "ok", "annotations": candidates, "rejections": []}
