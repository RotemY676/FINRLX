"""Phase 17.1 — Monthly LLM token budget tracker.

Reads + writes to `llm_token_usage` to enforce the operator-set
`MAX_MONTHLY_LLM_TOKENS` cap. Bucket key is (year, month) only —
totals are summed across providers because the cap is a wallet
not a per-vendor quota.

Pricing table is best-effort. Anthropic publishes per-million prices;
we record an estimate at write time. If the price table is stale, the
budget logic still works (token totals are the cap; cost is a
display-only field).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document_analysis import LLMTokenUsage

# Per-million-token prices in USD. Conservative defaults; update when
# Anthropic / OpenAI revise their boards.
_PRICE_PER_M_INPUT_USD: dict[str, float] = {
    "anthropic": 3.0,    # Claude Sonnet 4.6 input price (placeholder)
    "openai": 0.15,      # GPT-4o-mini input price (placeholder)
    "gemini": 0.075,     # Gemini 1.5 Flash paid-tier input price. Free
                         # tier is $0, but we estimate against paid so
                         # the operator-visible dollar figure is the
                         # worst case if free quota is exceeded.
    "local": 0.0,        # Self-hosted Ollama
    "stub": 0.0,
}
_PRICE_PER_M_OUTPUT_USD: dict[str, float] = {
    "anthropic": 15.0,
    "openai": 0.60,
    "gemini": 0.30,      # Gemini 1.5 Flash paid-tier output price.
    "local": 0.0,
    "stub": 0.0,
}


@dataclass
class BudgetStatus:
    """Snapshot returned to the FE budget-status endpoint."""

    year: int
    month: int
    cap_tokens: int
    used_tokens: int
    remaining_tokens: int
    cost_estimate_usd: float
    per_provider: dict[str, dict[str, float]]
    over_budget: bool


def estimate_cost_usd(provider: str, input_tokens: int, output_tokens: int) -> float:
    """Rough cost estimate. Returns 0.0 for unknown providers — cost
    is display-only; the budget cap enforces by tokens, not dollars."""
    in_rate = _PRICE_PER_M_INPUT_USD.get(provider, 0.0)
    out_rate = _PRICE_PER_M_OUTPUT_USD.get(provider, 0.0)
    return (input_tokens / 1_000_000.0) * in_rate + (output_tokens / 1_000_000.0) * out_rate


def _current_bucket() -> tuple[int, int]:
    now = datetime.now(UTC)
    return now.year, now.month


async def get_status(db: AsyncSession) -> BudgetStatus:
    """Sum the current month's usage across all providers and compare
    against the cap. The FE uses this to render a "you've used N of M
    tokens this month" indicator."""
    year, month = _current_bucket()
    result = await db.execute(
        select(LLMTokenUsage).where(
            LLMTokenUsage.year == year,
            LLMTokenUsage.month == month,
        )
    )
    rows = list(result.scalars().all())

    used_tokens = sum(r.input_tokens_total + r.output_tokens_total for r in rows)
    cost_total = sum(r.cost_estimate_usd_total for r in rows)

    per_provider: dict[str, dict[str, float]] = {}
    for r in rows:
        per_provider[r.provider] = {
            "input_tokens": float(r.input_tokens_total),
            "output_tokens": float(r.output_tokens_total),
            "cost_estimate_usd": r.cost_estimate_usd_total,
        }

    cap = settings.max_monthly_llm_tokens
    return BudgetStatus(
        year=year,
        month=month,
        cap_tokens=cap,
        used_tokens=used_tokens,
        remaining_tokens=max(0, cap - used_tokens),
        cost_estimate_usd=cost_total,
        per_provider=per_provider,
        over_budget=used_tokens >= cap,
    )


async def can_spend(db: AsyncSession, additional_tokens: int) -> tuple[bool, BudgetStatus]:
    """Pre-call check. Returns (allowed, status) where `allowed` is
    False if the projected (current_used + additional) exceeds the
    cap. The caller (analyze endpoint) translates a False here into a
    503 response with a budget-exceeded detail.

    `additional_tokens` should be the conservative estimate of the
    upcoming call (extracted_text_tokens_estimate + prompt_tokens +
    a small headroom for the system prompt and the response).
    """
    status = await get_status(db)
    if status.used_tokens + additional_tokens > status.cap_tokens:
        return False, status
    return True, status


async def record_usage(
    db: AsyncSession,
    *,
    provider: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Accumulate usage for (current_year, current_month, provider).
    Upserts the row; the caller commits the surrounding transaction so
    this is atomic with the DocumentAnalysis write."""
    year, month = _current_bucket()
    cost = estimate_cost_usd(provider, input_tokens, output_tokens)

    existing = await db.execute(
        select(LLMTokenUsage).where(
            LLMTokenUsage.year == year,
            LLMTokenUsage.month == month,
            LLMTokenUsage.provider == provider,
        )
    )
    row = existing.scalar_one_or_none()
    now = datetime.now(UTC)
    if row is None:
        db.add(
            LLMTokenUsage(
                year=year,
                month=month,
                provider=provider,
                input_tokens_total=input_tokens,
                output_tokens_total=output_tokens,
                cost_estimate_usd_total=cost,
                last_updated_at=now,
            )
        )
    else:
        row.input_tokens_total += input_tokens
        row.output_tokens_total += output_tokens
        row.cost_estimate_usd_total += cost
        row.last_updated_at = now


def estimate_prompt_tokens(prompts: Iterable[str]) -> int:
    """Approximate token count for a set of prompt strings. Same 4-
    chars-per-token heuristic used in extraction.estimate_tokens."""
    total_chars = sum(len(p) for p in prompts if p)
    return max(1, total_chars // 4)
