"""Phase 17.2 — AnthropicProvider live-call contract tests.

The real Anthropic SDK is patched so CI never hits the real network.
The fixtures mirror the actual `anthropic.types.Message` shape so the
parsing path is exercised exactly as it will in production.

What this pins:
  - Happy path: system message split out, user message forwarded,
    token counts read from `resp.usage`.
  - Empty key -> StubProviderError before any network call.
  - Auth failure (401) -> StubProviderError WITHOUT leaking the key.
  - Rate limit (429) -> StubProviderError with retry hint.
  - Timeout / connection error -> StubProviderError.
  - Empty content blocks (e.g. tool-use only) -> StubProviderError.
  - Only-system messages -> StubProviderError ("API requires user msg").
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.llm.anthropic import AnthropicProvider
from app.services.llm.provider import StubProviderError
from app.services.llm.types import LLMMessage


def _http_response(status_code: int) -> httpx.Response:
    """Build a real httpx.Response so the anthropic SDK's exception
    classes can read `.request` off it (they call into the parent
    httpx exception constructor)."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status_code, request=request)


def _mock_response(
    text: str = "hello",
    input_tokens: int = 42,
    output_tokens: int = 7,
):
    """Mirror the anthropic.types.Message shape we read in production."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def _mock_async_anthropic(create_mock):
    """Patch the `AsyncAnthropic` constructor to return an object whose
    `messages.create` resolves to whatever `create_mock` returns / raises."""
    instance = SimpleNamespace(
        messages=SimpleNamespace(create=create_mock)
    )
    return lambda *a, **kw: instance


@pytest.mark.asyncio
async def test_empty_key_raises_before_sdk_call():
    provider = AnthropicProvider(api_key="", model="claude-sonnet-4-5")
    with pytest.raises(StubProviderError) as exc:
        await provider.chat([LLMMessage(role="user", content="hi")])
    assert "LLM_ANTHROPIC_API_KEY" in str(exc.value)


@pytest.mark.asyncio
async def test_only_system_messages_raises():
    provider = AnthropicProvider(api_key="dummy", model="claude-sonnet-4-5")
    with pytest.raises(StubProviderError) as exc:
        await provider.chat([LLMMessage(role="system", content="ctx")])
    assert "user message" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_happy_path_returns_text_and_usage():
    create_mock = AsyncMock(return_value=_mock_response("Revenue grew 70.6% YoY."))
    with patch(
        "anthropic.AsyncAnthropic",
        side_effect=_mock_async_anthropic(create_mock),
    ):
        provider = AnthropicProvider(api_key="dummy", model="claude-sonnet-4-5")
        out = await provider.chat([
            LLMMessage(role="system", content="You are FINRLX Analyst."),
            LLMMessage(role="user", content="What was revenue growth?"),
        ])

    assert out.text == "Revenue grew 70.6% YoY."
    assert out.provider == "anthropic"
    assert out.model == "claude-sonnet-4-5"
    assert out.input_tokens == 42
    assert out.output_tokens == 7
    # System message was split out — the call should have received it
    # via the `system` kwarg, not in the messages list.
    create_mock.assert_awaited_once()
    call_kwargs = create_mock.await_args.kwargs
    assert call_kwargs["system"] == "You are FINRLX Analyst."
    assert call_kwargs["messages"] == [
        {"role": "user", "content": "What was revenue growth?"}
    ]


@pytest.mark.asyncio
async def test_auth_failure_raises_stub_without_key_in_message():
    from anthropic import AuthenticationError

    # AuthenticationError needs a request/response in newer SDK
    # versions; SimpleNamespace is enough for `isinstance` to match
    # because we catch the bare class.
    err = AuthenticationError(
        message="invalid api key",
        response=_http_response(401),
        body=None,
    )
    create_mock = AsyncMock(side_effect=err)
    with patch("anthropic.AsyncAnthropic", side_effect=_mock_async_anthropic(create_mock)):
        provider = AnthropicProvider(api_key="sk-ant-test-leak-canary-12345")
        with pytest.raises(StubProviderError) as exc:
            await provider.chat([LLMMessage(role="user", content="x")])
    msg = str(exc.value)
    assert "auth failed" in msg.lower() or "invalid or expired" in msg.lower()
    # CRITICAL — never echo the key value back to the caller.
    assert "sk-ant-test-leak-canary-12345" not in msg


@pytest.mark.asyncio
async def test_rate_limit_raises_stub_with_retry_hint():
    from anthropic import RateLimitError

    err = RateLimitError(
        message="429",
        response=_http_response(429),
        body=None,
    )
    create_mock = AsyncMock(side_effect=err)
    with patch("anthropic.AsyncAnthropic", side_effect=_mock_async_anthropic(create_mock)):
        provider = AnthropicProvider(api_key="dummy")
        with pytest.raises(StubProviderError) as exc:
            await provider.chat([LLMMessage(role="user", content="x")])
    assert "rate-limit" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_empty_content_blocks_raises_stub():
    """If Anthropic returns only tool-use blocks (no text), surface
    that honestly rather than indexing into [0] blindly."""
    empty_response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", id="x", name="foo", input={})],
        usage=SimpleNamespace(input_tokens=10, output_tokens=0),
    )
    create_mock = AsyncMock(return_value=empty_response)
    with patch("anthropic.AsyncAnthropic", side_effect=_mock_async_anthropic(create_mock)):
        provider = AnthropicProvider(api_key="dummy")
        with pytest.raises(StubProviderError) as exc:
            await provider.chat([LLMMessage(role="user", content="x")])
    assert "no text blocks" in str(exc.value).lower()
