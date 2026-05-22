"""Anthropic / Claude provider — STUB.

Activation:
1. `pip install anthropic` (already on requirements.txt? — check before merging)
2. Set `ANTHROPIC_API_KEY` env var.
3. Set `LLM_PROVIDER=anthropic`.

When activated, swap `_NotConfigured.chat` for a real call:

    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=self.api_key)
    resp = await client.messages.create(
        model=self.model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_text,
        messages=[{"role": m.role, "content": m.content} for m in non_system_messages],
    )
    return LLMResponse(
        text=resp.content[0].text,
        provider="anthropic",
        model=self.model,
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
    )
"""
from __future__ import annotations

from app.services.llm.provider import LLMProvider, StubProviderError
from app.services.llm.types import LLMMessage, LLMResponse


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self.api_key = api_key
        self.model = model

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise StubProviderError(
            "AnthropicProvider is a stub. Install the `anthropic` SDK, "
            "set ANTHROPIC_API_KEY, and replace AnthropicProvider.chat with "
            "the real call shown in the module docstring."
        )
