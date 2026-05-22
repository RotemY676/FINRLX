"""Abstract LLM provider base class."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.llm.types import LLMMessage, LLMResponse


class LLMProvider(ABC):
    """Stable interface every concrete provider implements."""

    name: str = "abstract"
    model: str = ""

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Synchronous (non-streaming) completion. Streaming arrives in a
        follow-up phase once the operator decides to spend tokens."""
        raise NotImplementedError


class StubProviderError(RuntimeError):
    """Raised by stub providers to signal they need configuration before use."""
