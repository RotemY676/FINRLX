"""Anthropic / Claude provider — Phase 17.2 live HTTP via the
`anthropic` SDK.

Activation:
  1. `pip install anthropic` (in requirements.txt as of 17.2).
  2. Set `LLM_ANTHROPIC_API_KEY` env var to the operator's key.
  3. Set `LLM_PROVIDER=anthropic` to route the abstraction here.
  4. Optionally set `LLM_MODEL` — defaults to claude-sonnet-4-6.

Error handling:
  - Auth failures (401): raise `StubProviderError` with a clear
    "invalid or expired key" message. NEVER include the key value.
  - Rate limits (429): raise `StubProviderError` with a "rate-limit
    hit" hint so the analyze endpoint surfaces a 503 rather than
    swallowing the failure silently.
  - Network / timeout / unexpected errors: same — raise
    `StubProviderError` so the endpoint layer translates uniformly.

Token counting: Anthropic's response carries exact `usage.input_tokens`
and `usage.output_tokens` — those are the source of truth the budget
tracker accumulates in `llm_token_usage`. The 4-chars-per-token
estimate in `extraction.py` is only a pre-call projection.

System messages: the FINRLX prompt builder passes a single system
message at index 0 of the messages list. Anthropic's Messages API
takes `system` as a top-level kwarg, NOT as a message — so we
extract it before serialising the rest.
"""
from __future__ import annotations

from app.services.llm.provider import LLMProvider, StubProviderError
from app.services.llm.types import LLMMessage, LLMResponse


# Default model. Operators can override via the LLM_MODEL env var. The
# 4.x lineup has the largest context window (200K) at the time of
# Phase 17.2, which fits typical 10-Q / 10-K filings comfortably.
_DEFAULT_MODEL = "claude-sonnet-4-5"


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self.api_key = api_key
        self.model = model or _DEFAULT_MODEL

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        # Lazy import so the rest of the app doesn't pay the SDK's
        # cold-start cost when no provider is configured.
        try:
            from anthropic import AsyncAnthropic
            from anthropic import (
                APIConnectionError,
                APIStatusError,
                APITimeoutError,
                AuthenticationError,
                RateLimitError,
            )
        except ImportError as e:
            raise StubProviderError(
                "anthropic SDK is not installed. Add `anthropic` to "
                "backend/requirements.txt and reinstall."
            ) from e

        if not self.api_key:
            raise StubProviderError(
                "LLM_ANTHROPIC_API_KEY is empty. Set it in the backend "
                "environment to activate the Anthropic provider."
            )

        # Split out the system message (Anthropic API takes it as a
        # top-level kwarg, not as a list element). Collapse multiple
        # system messages into one — the SDK only accepts a single
        # string and our prompt builder ships at most one anyway.
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        non_system = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]
        if not non_system:
            raise StubProviderError(
                "Anthropic call attempted with only system messages — "
                "the API requires at least one user message."
            )

        client = AsyncAnthropic(api_key=self.api_key)
        try:
            resp = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_text or "You are a helpful assistant.",
                messages=non_system,
            )
        except AuthenticationError as e:
            raise StubProviderError(
                "Anthropic auth failed: invalid or expired LLM_ANTHROPIC_API_KEY."
            ) from e
        except RateLimitError as e:
            raise StubProviderError(
                "Anthropic rate-limit hit. Retry in a moment, or upgrade "
                "the Anthropic plan if this is a sustained workload."
            ) from e
        except APITimeoutError as e:
            raise StubProviderError(
                "Anthropic request timed out. The document may be too "
                "large for the model's context window."
            ) from e
        except APIConnectionError as e:
            raise StubProviderError(
                f"Anthropic network error: {e}. The endpoint may be "
                "unreachable from this backend instance."
            ) from e
        except APIStatusError as e:
            # 5xx or other unexpected response. Surface the status
            # without leaking the response body (may contain prompt
            # echo).
            raise StubProviderError(
                f"Anthropic API returned status {e.status_code}."
            ) from e

        # The Messages API returns a list of content blocks. We only
        # send a single user message and request a text response, so
        # the first text block IS the answer. If for any reason there
        # are no text blocks (e.g. tool-use return), surface that
        # honestly rather than indexing into [0] blindly.
        text_blocks = [
            block.text
            for block in resp.content
            if getattr(block, "type", None) == "text"
        ]
        text = "\n\n".join(text_blocks).strip()
        if not text:
            raise StubProviderError(
                "Anthropic returned no text blocks (only tool-use or "
                "empty content). Re-running with a different prompt "
                "usually fixes this."
            )

        return LLMResponse(
            text=text,
            provider="anthropic",
            model=self.model,
            input_tokens=getattr(resp.usage, "input_tokens", None),
            output_tokens=getattr(resp.usage, "output_tokens", None),
        )
