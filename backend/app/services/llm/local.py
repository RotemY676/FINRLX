"""Local Ollama provider — STUB.

Activation:
1. Install Ollama (https://ollama.com), pull a model:
       ollama pull llama3.1:8b-instruct
2. Set `LLM_LOCAL_BASE_URL=http://localhost:11434` (default).
3. Set `LLM_PROVIDER=local`.

When activated, replace `_NotConfigured.chat` with:

    import httpx
    async with httpx.AsyncClient(timeout=120) as c:
        resp = await c.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "options": {"temperature": temperature, "num_predict": max_tokens},
                "stream": False,
            },
        )
        resp.raise_for_status()
        body = resp.json()
    return LLMResponse(
        text=body["message"]["content"],
        provider="local",
        model=self.model,
        input_tokens=body.get("prompt_eval_count"),
        output_tokens=body.get("eval_count"),
    )

This phase intentionally does NOT add httpx-to-ollama calls so the
deploy stays GPU-free and zero-cost until the operator explicitly
opts in (Phase O-3, currently skipped per the strategy decision).
"""
from __future__ import annotations

from app.services.llm.provider import LLMProvider, StubProviderError
from app.services.llm.types import LLMMessage, LLMResponse


class LocalOllamaProvider(LLMProvider):
    name = "local"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b-instruct") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise StubProviderError(
            "LocalOllamaProvider is a stub. Install Ollama, pull a model, "
            "and replace LocalOllamaProvider.chat with the httpx call shown "
            "in the module docstring."
        )
