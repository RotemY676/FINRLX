"""Phase 17.1 — Document analysis orchestration.

Glue layer between the analyze endpoint, the LLM provider abstraction
(`app.services.llm`), the token budget tracker, and the
DocumentAnalysis store.

Why this lives in its own module:
  - The endpoint stays thin (validation + persistence).
  - Unit tests can exercise the orchestration without spinning up
    FastAPI.
  - Future RAG path (Option C from the strategy gate) plugs in here
    by adding a retrieval step before `provider.chat()` — endpoint
    contract stays unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.services.documents import budget as budget_svc
from app.services.llm import LLMMessage, get_provider_chain
from app.services.llm.router import get_provider_status
from app.services.llm.provider import StubProviderError

logger = logging.getLogger(__name__)


# Hard cap on the input portion of the prompt we send to the LLM.
# Documents above this length get truncated with a note in the system
# prompt so the call still completes within the provider's context
# window. Tuned for Anthropic Claude (200K context); leaves room for
# the system prompt + response.
_MAX_INPUT_CHARS = 600_000  # ~150K tokens at the 4-chars-per-token heuristic


SYSTEM_PROMPT = (
    "You are FINRLX Analyst, a research specialist for the FINRLX "
    "decision-intelligence platform. The user uploaded a corporate "
    "filing (10-Q, 10-K, transcript, presentation) and is asking a "
    "question about it.\n\n"
    "Rules you must follow:\n"
    "- Answer ONLY from the document text the user provided. Do not "
    "draw on memorised facts about the company.\n"
    "- Cite the section, page, or quoted phrase you used.\n"
    "- When the document does not contain the answer, say so. Do not "
    "guess.\n"
    "- FINRLX is decision-support, not investment advice. Refuse "
    "trade instructions ('should I buy?', 'sell now?') and "
    "market-direction predictions. Decline politely and remind the "
    "user that FINRLX provides research, not advice.\n"
    "- Be precise with numbers — quote them exactly as they appear "
    "in the filing.\n"
)


class BudgetExceededError(RuntimeError):
    """Raised when the projected call would exceed MAX_MONTHLY_LLM_TOKENS."""

    def __init__(self, status: budget_svc.BudgetStatus, projected_tokens: int):
        self.status = status
        self.projected_tokens = projected_tokens
        super().__init__(
            f"monthly LLM token budget would be exceeded: "
            f"{status.used_tokens} used + {projected_tokens} projected > "
            f"{status.cap_tokens} cap"
        )


@dataclass
class AnalysisResult:
    """What the orchestration returns to the endpoint."""

    response_text: str
    provider: str
    model: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]


async def analyze_document(
    db: AsyncSession,
    *,
    document_text: str,
    user_prompt: str,
) -> AnalysisResult:
    """Run an LLM analysis against a document.

    Raises:
      - StubProviderError: when the configured provider is a stub
        (no real API key set). The endpoint should translate to 503
        with a "configure LLM_PROVIDER + key" message.
      - BudgetExceededError: when the projected call would push the
        monthly token total over `MAX_MONTHLY_LLM_TOKENS`. The
        endpoint should translate to 503 with budget detail.
      - ValueError: when document_text or user_prompt is empty.

    On success the caller is responsible for:
      - persisting a DocumentAnalysis row with the returned fields
      - calling `budget.record_usage(...)` with the same provider +
        token counts
      - committing the surrounding transaction so both writes are atomic
    """
    if not user_prompt or not user_prompt.strip():
        raise ValueError("user_prompt is empty")
    if not document_text or not document_text.strip():
        raise ValueError("document_text is empty")

    truncated_doc = document_text[:_MAX_INPUT_CHARS]
    truncation_note = ""
    if len(document_text) > _MAX_INPUT_CHARS:
        truncation_note = (
            "\n\n[NOTE TO MODEL: the document was truncated to the first "
            f"{_MAX_INPUT_CHARS:,} characters to fit the context window. "
            "Tell the user if a truncated section seems load-bearing.]"
        )

    # Budget check FIRST — defensive ordering. If the monthly cap is
    # already exhausted, never look up a provider (free) and never
    # attempt a network call (paid). The endpoint translates this
    # into a 503 with budget detail.
    projected_input_tokens = budget_svc.estimate_prompt_tokens(
        [SYSTEM_PROMPT, truncated_doc, user_prompt, truncation_note]
    )
    # Plus a small headroom for the model's output (call it 2000
    # tokens — fits a paragraph-length summary comfortably).
    projected_total = projected_input_tokens + 2000

    allowed, status = await budget_svc.can_spend(db, projected_total)
    if not allowed:
        raise BudgetExceededError(status, projected_total)

    # Only NOW look up the provider chain. Empty chain → the endpoint
    # 503s with "configure LLM_PROVIDER + key". Phase 17.4 walks the
    # chain in order, falling back on StubProviderError so a free
    # provider (e.g. gemini) can be tried before the paid one
    # (anthropic). The first provider that returns successfully wins.
    chain = get_provider_chain()
    if not chain:
        status_obj = get_provider_status()
        raise StubProviderError(
            f"LLM provider not configured. {status_obj.detail}"
        )

    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=(
                f"Document text (research filing):\n\n"
                f"{truncated_doc}{truncation_note}\n\n"
                f"---\n\n"
                f"My question:\n{user_prompt}"
            ),
        ),
    ]

    last_error: StubProviderError | None = None
    for provider in chain:
        try:
            response = await provider.chat(messages, max_tokens=2048)
        except StubProviderError as e:
            # Log and try the next provider in the chain. The cause is
            # preserved so it surfaces in the final error if all
            # providers fail.
            logger.warning(
                "LLM provider %s failed (%s); trying next in chain",
                provider.name,
                e,
            )
            last_error = e
            continue
        return AnalysisResult(
            response_text=response.text,
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

    # Exhausted the chain. Re-raise the last error so the endpoint
    # surfaces the most recent failure detail (typically the paid
    # provider's reason, since it's last in a free-first chain).
    raise StubProviderError(
        "All configured LLM providers failed. "
        f"Last error: {last_error}"
    )
