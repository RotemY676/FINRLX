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

import logging
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
_MAX_OUTPUT_TOKENS = 4096


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
    "Your output must have four sections, in this order:\n"
    "**Headline metric trajectory** — identify 2–4 key metrics "
    "(revenue, gross margin, operating margin, free cash flow, etc.) "
    "and show their values per quarter in chronological order. Use a "
    "small table or bullet list.\n\n"
    "**Latest-quarter delta** — what changed in the most recent quarter "
    "vs the prior period? What did management call out in the MD&A "
    "narrative? Quote management's language briefly when relevant.\n\n"
    "**Risk-factor changes** — any new, modified, or removed risk "
    "factors vs the prior period? Be concise; only list material changes.\n\n"
    "**What to watch** — one paragraph (3–5 sentences) on the headline "
    "thing the user should monitor next quarter."
)


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

    row = TickerInsights(
        ticker=symbol,
        summary_text=response.text,
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
