"""OpenAI / GPT provider — STUB.

Activation:
1. `pip install openai`
2. Set `OPENAI_API_KEY`.
3. Set `LLM_PROVIDER=openai`.

When activated, swap `_NotConfigured.chat` for a real call:

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=self.api_key)
    resp = await client.chat.completions.create(
        model=self.model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": m.role, "content": m.content} for m in messages],
    )
    return LLMResponse(
        text=resp.choices[0].message.content or "",
        provider="openai",
        model=self.model,
        input_tokens=resp.usage.prompt_tokens if resp.usage else None,
        output_tokens=resp.usage.completion_tokens if resp.usage else None,
    )
"""
from __future__ import annotations

from app.services.llm.provider import LLMProvider, StubProviderError
from app.services.llm.types import LLMMessage, LLMResponse


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
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
            "OpenAIProvider is a stub. Install the `openai` SDK, "
            "set OPENAI_API_KEY, and replace OpenAIProvider.chat with "
            "the real call shown in the module docstring."
        )
