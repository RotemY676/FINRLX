"""Shared LLM types."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LLMRole = Literal["system", "user", "assistant"]


class LLMMessage(BaseModel):
    role: LLMRole
    content: str = Field(..., min_length=1)


class LLMResponse(BaseModel):
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
