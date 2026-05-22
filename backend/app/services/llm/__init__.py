"""LLM provider abstraction (Phase O-5).

A pluggable layer that lets the operator flip the in-app Research
Assistant on by setting one env var (`LLM_PROVIDER`) and the matching
API key — without touching application code. Today, all three providers
are STUBS: invoking them raises a RuntimeError pointing at the install
+ key needed to activate them. The router and the /assistant endpoints
are fully wired so the activation flip is just configuration.
"""
from app.services.llm.router import get_provider, ProviderStatus
from app.services.llm.types import LLMMessage, LLMResponse

__all__ = ["get_provider", "ProviderStatus", "LLMMessage", "LLMResponse"]
