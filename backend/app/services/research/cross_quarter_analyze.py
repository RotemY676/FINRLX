"""Phase 18.6 — Cross-quarter LLM analysis.

Builds a prompt covering ALL recent sec_auto filings for a ticker
and asks the configured LLM chain to synthesize:

  1. Headline-metric trajectory across quarters
  2. Latest-quarter delta + management commentary
  3. Risk-factor changes vs the prior period
  4. "What to watch" — one paragraph for the user

This is the synthesis layer on top of 18.4's per-filing ingest. It
reads from `research_documents` (sec_auto rows for the ticker) and
writes a single TickerInsights row.

Token budgeting:
  - Each filing's extracted_text is truncated to _MAX_CHARS_PER_FILING
    (80K chars ~ 20K tokens). 6 filings × 20K = 120K input tokens,
    well within Gemini 2.5 Flash's 1M context window and the existing
    monthly token budget.
  - The output is capped to 4K tokens (a structured but
    summary-length response).

If the chain falls back from Gemini (free) to Anthropic (paid), the
budget tracker records both attempts — the failed Gemini call uses
zero tokens since it errors before generation.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import ResearchDocument
from app.models.ticker_insights import TickerInsights
from app.services.documents import budget as budget_svc
from app.services.llm import LLMMessage, get_provider_chain
from app.services.llm.provider import StubProviderError
from app.services.llm.router import get_provider_status

logger = logging.getLogger(__name__)


# Per-filing input cap. Keeps total prompt size predictable across
# tickers with very long filings (some 10-Ks are 300K+ chars). At
# ~4 chars/token, 80K chars ≈ 20K input tokens — 6 filings fit
# comfortably inside Gemini's 1M context and the monthly budget.
_MAX_CHARS_PER_FILING = 80_000
# Raised from 4096 → 8192 after Phase 18.6.1 because production runs
# truncated at ~160 output tokens before completing the four sections.
# The model finished a markdown table HEADER then stopped (likely a
# self-judged "complete" signal). With 8192 there's no realistic risk
# of running out for a structured response.
_MAX_OUTPUT_TOKENS = 8192


SYSTEM_PROMPT = (
    "You are FINRLX Analyst, a research specialist for the FINRLX "
    "decision-intelligence platform. You are reading the most recent "
    "quarterly filings for a single ticker and synthesizing what "
    "matters across them.\n\n"
    "Rules you must follow:\n"
    "- Answer ONLY from the filing text the user provided. Do not "
    "draw on memorised facts about the company.\n"
    "- Cite the accession number you used (e.g. '0001045810-26-000012') "
    "when you reference a specific filing.\n"
    "- Be precise with numbers — quote them exactly as they appear in "
    "the filings.\n"
    "- FINRLX is decision-support, not investment advice. Refuse trade "
    "instructions ('should I buy?', 'sell now?') and market-direction "
    "predictions.\n\n"
    "Your output MUST have two parts, in this exact order:\n\n"
    "PART 1 — A fenced JSON code block with the structured metrics. "
    "The frontend renders this as a chart, so the schema is strict. "
    "Use this exact shape, with no extra fields:\n"
    "```json\n"
    "{\n"
    '  "metrics": [\n'
    "    {\n"
    '      "name": "Revenue",\n'
    '      "unit": "USD millions",\n'
    '      "quarters": [\n'
    '        {"period_end": "2025-01-26", "label": "Q4 FY25", "value": 39331},\n'
    '        {"period_end": "2025-04-27", "label": "Q1 FY26", "value": 44062}\n'
    "      ]\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "```\n"
    "Rules for the JSON:\n"
    "- Include 2–4 metrics. Prefer Revenue, Gross margin %, Operating "
    "margin %, Free cash flow (in this priority order) when present.\n"
    "- One entry per filing in `quarters`, in chronological order "
    "(oldest first). Skip filings where the metric isn't reported.\n"
    "- `value` MUST be a number, not a string. For percentages use the "
    "raw percent (e.g. 75.4 not 0.754).\n"
    "- `unit` is a short label the chart axis can show (e.g. \"USD "
    "millions\", \"%\", \"USD billions\").\n"
    "- `label` is a 6-12 character human label for the X-axis tick "
    "(e.g. \"Q1 FY27\", not a long date).\n"
    "- Do NOT add commentary inside the JSON block. The frontend parses "
    "it programmatically.\n\n"
    "PART 2 — A markdown narrative with THREE sections (do not repeat "
    "the trajectory — the chart shows it). Each section is short:\n\n"
    "## Latest-quarter delta\n"
    "2–4 sentences: what changed in the most recent quarter vs the "
    "prior period? What did management call out in the MD&A narrative? "
    "Cite the accession number you read it from.\n\n"
    "## Risk-factor changes\n"
    "Bullet list of new, modified, or removed risk factors vs the prior "
    "period. Material changes only. If nothing material changed, say "
    "so in one line.\n\n"
    "## What to watch\n"
    "One paragraph (3–5 sentences) on the headline thing the user "
    "should monitor next quarter, anchored in what the filings actually "
    "said (don't invent forecasts)."
)


# Fenced-JSON extractor. The LLM is instructed to emit ```json … ```
# but we tolerate the bare ``` variant too. Compiled once.
_JSON_FENCE_RE = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    flags=re.DOTALL | re.IGNORECASE,
)


def _parse_metrics_block(text: str) -> dict | None:
    """Extract the JSON metrics block from the LLM response.

    Returns the parsed dict, or None if no valid block is found. The
    caller falls back to "narrative-only" mode in that case — we still
    persist the row and render the markdown; the chart just doesn't
    appear. We never persist invalid JSON.
    """
    match = _JSON_FENCE_RE.search(text)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except (ValueError, TypeError) as e:
        logger.warning("metrics JSON block did not parse: %s", e)
        return None
    if not isinstance(payload, dict) or "metrics" not in payload:
        logger.warning("metrics block missing 'metrics' key")
        return None
    metrics = payload.get("metrics")
    if not isinstance(metrics, list):
        return None
    # Light schema sanity. We don't reject the whole thing on a single
    # bad metric — drop the bad ones and keep the rest.
    cleaned: list[dict] = []
    for m in metrics:
        if not isinstance(m, dict):
            continue
        name = m.get("name")
        quarters = m.get("quarters")
        if not isinstance(name, str) or not isinstance(quarters, list):
            continue
        clean_quarters: list[dict] = []
        for q in quarters:
            if not isinstance(q, dict):
                continue
            value = q.get("value")
            if not isinstance(value, (int, float)):
                continue
            clean_quarters.append({
                "period_end": q.get("period_end") or "",
                "label": q.get("label") or "",
                "value": float(value),
            })
        if clean_quarters:
            cleaned.append({
                "name": name,
                "unit": m.get("unit") or "",
                "quarters": clean_quarters,
            })
    return {"metrics": cleaned} if cleaned else None


def _strip_metrics_block(text: str) -> str:
    """Remove the fenced JSON metrics block from the text so the
    frontend doesn't render it twice (once as a chart, once as raw
    JSON in the narrative)."""
    return _JSON_FENCE_RE.sub("", text, count=1).strip()


class InsufficientFilingsError(RuntimeError):
    """Raised when generation is requested for a ticker that has no
    sec_auto documents ready. The endpoint translates this to 409 so
    the FE can chain auto-ingest → insights, or the user can upload
    PDFs manually instead."""


@dataclass
class InsightsGenerationResult:
    """Returned by `generate_insights` so the caller can persist the
    row + record usage atomically with its own transaction policy."""
    insights: TickerInsights
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


async def generate_insights(
    db: AsyncSession,
    *,
    ticker: str,
    triggered_by_email: str,
) -> InsightsGenerationResult:
    """Run cross-quarter analysis for `ticker` and persist a
    TickerInsights row.

    Raises:
      - InsufficientFilingsError: ticker has no sec_auto documents
        with extracted_text ready (caller → 409 + hint to ingest).
      - StubProviderError: every LLM provider in the chain failed
        (caller → 503).
      - BudgetExceededError: projected token spend exceeds
        MAX_MONTHLY_LLM_TOKENS (caller → 503 with budget detail).
    """
    symbol = ticker.strip().upper()

    # Load sec_auto documents for this ticker, ordered by report
    # period (oldest first so the LLM sees the trajectory chronologically).
    stmt = (
        select(ResearchDocument)
        .where(
            ResearchDocument.ticker == symbol,
            ResearchDocument.source == "sec_auto",
            ResearchDocument.extraction_status == "ready",
        )
        .order_by(ResearchDocument.sec_period_of_report.asc())
    )
    res = await db.execute(stmt)
    docs = list(res.scalars().all())

    if not docs:
        raise InsufficientFilingsError(
            f"No sec_auto documents ready for {symbol}. "
            "Run POST /research/{ticker}/auto-ingest first, or upload "
            "PDFs manually."
        )

    # Build the user prompt: chronological filing dump with explicit
    # headers so the LLM can cite by accession + period.
    filing_chunks: list[str] = []
    for d in docs:
        text = (d.extracted_text or "")[:_MAX_CHARS_PER_FILING]
        truncation_note = ""
        if d.extracted_text and len(d.extracted_text) > _MAX_CHARS_PER_FILING:
            truncation_note = (
                f"\n[NOTE: filing truncated to {_MAX_CHARS_PER_FILING:,} chars "
                "to fit the context window; the cut content is later sections "
                "of the same filing.]"
            )
        filing_chunks.append(
            f"## Filing: {d.sec_form or 'unknown'} for period "
            f"{d.sec_period_of_report.isoformat() if d.sec_period_of_report else 'unknown'} "
            f"(accession: {d.sec_accession_no})\n\n"
            f"{text}{truncation_note}"
        )
    accessions = [d.sec_accession_no for d in docs if d.sec_accession_no]
    user_content = (
        f"Ticker: {symbol}\n"
        f"Filings provided (oldest first): {len(docs)}\n\n"
        + "\n\n---\n\n".join(filing_chunks)
        + "\n\n---\n\n"
        + "Produce the four-section analysis described in the system message."
    )

    # Budget pre-flight using the chars-per-token heuristic. The
    # cross-quarter prompt is large, so budget exhaustion is a real
    # risk — surface it BEFORE any provider call.
    projected_input = budget_svc.estimate_prompt_tokens(
        [SYSTEM_PROMPT, user_content]
    )
    projected_total = projected_input + _MAX_OUTPUT_TOKENS
    allowed, status = await budget_svc.can_spend(db, projected_total)
    if not allowed:
        from app.services.documents.analyze import BudgetExceededError
        raise BudgetExceededError(status, projected_total)

    chain = get_provider_chain()
    if not chain:
        status_obj = get_provider_status()
        raise StubProviderError(
            f"LLM provider not configured. {status_obj.detail}"
        )

    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_content),
    ]

    # Walk the chain — same pattern as analyze.py. Record every
    # provider's failure so the operator sees the full story if all
    # providers fail.
    errors: list[tuple[str, str]] = []
    response = None
    for provider in chain:
        try:
            response = await provider.chat(messages, max_tokens=_MAX_OUTPUT_TOKENS)
            break
        except StubProviderError as e:
            logger.warning(
                "insights provider %s failed (%s); trying next in chain",
                provider.name, e,
            )
            errors.append((provider.name, str(e)))

    if response is None:
        breakdown = "; ".join(f"{name}: {msg}" for name, msg in errors)
        raise StubProviderError(
            f"All {len(errors)} configured LLM providers failed for insights. {breakdown}"
        )

    # Record the successful call's token usage. This is the same path
    # the per-document analyze endpoint uses; insights consume from
    # the same monthly budget bucket.
    if response.input_tokens is not None and response.output_tokens is not None:
        await budget_svc.record_usage(
            db,
            provider=response.provider,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )
        cost = budget_svc.estimate_cost_usd(
            response.provider, response.input_tokens, response.output_tokens
        )
    else:
        cost = None

    # Phase 18.6.1: extract the structured metrics block so the FE
    # can render a chart, then strip it from the markdown so it isn't
    # re-rendered as raw JSON below the chart. If parsing fails the
    # row still saves — chart just doesn't appear.
    parsed_metrics = _parse_metrics_block(response.text)
    narrative_text = _strip_metrics_block(response.text) if parsed_metrics else response.text

    row = TickerInsights(
        ticker=symbol,
        summary_text=narrative_text,
        metrics=parsed_metrics,
        quarters_covered=accessions,
        provider=response.provider,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        cost_estimate_usd=cost,
        generated_by_email=triggered_by_email,
    )
    db.add(row)
    await db.commit()

    return InsightsGenerationResult(
        insights=row,
        provider=response.provider,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )


async def get_latest_insights(
    db: AsyncSession, *, ticker: str
) -> TickerInsights | None:
    """Return the most recent TickerInsights row for `ticker`, or None
    if none exist yet."""
    symbol = ticker.strip().upper()
    stmt = (
        select(TickerInsights)
        .where(TickerInsights.ticker == symbol)
        .order_by(TickerInsights.generated_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
