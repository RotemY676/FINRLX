"""Assistant API (Phase O-5) — provider-routed LLM endpoints.

These endpoints exist so the in-app Research Assistant has a fixed
contract the FE can target. Today, every endpoint returns 503 unless
`LLM_PROVIDER` is configured AND the matching API key is present.

When the operator decides to spend tokens:
1. `pip install` the relevant SDK (anthropic / openai).
2. Replace the stub `chat()` in the matching provider module with the
   real SDK call (templates are in each provider's module docstring).
3. Set `LLM_PROVIDER=anthropic` (or openai or local) and the API key.

The endpoints stay the same shape — the FE light-up is one env-var flip.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.models.auth import User
from app.schemas.common import ApiResponse
from app.services.llm import LLMMessage, get_provider
from app.services.llm.provider import StubProviderError
from app.services.llm.router import get_provider_status

router = APIRouter()


SYSTEM_PROMPT = (
    "You are FINRLX Analyst, a specialist for the FINRLX decision-intelligence "
    "platform. Answer only from the context the caller provides. Cite the section "
    "you used. FINRLX is decision support, not investment advice. Refuse trade "
    "instructions and market-direction predictions."
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    context: str = Field(default="", max_length=80000)


class ChatResponse(BaseModel):
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class NarrativeRequest(BaseModel):
    recommendation_id: str = Field(..., max_length=36)
    context: str = Field(..., max_length=80000)


class NewsExplainRequest(BaseModel):
    headline: str = Field(..., min_length=1, max_length=400)
    summary: str | None = Field(default=None, max_length=2000)
    context: str = Field(default="", max_length=80000)


def _service_unavailable(extra_detail: str = "") -> HTTPException:
    status_obj = get_provider_status()
    detail = (
        "LLM provider not configured. " + status_obj.detail
        + " Use the operator console at /operator for the manual ChatGPT/Claude workflow."
    )
    if extra_detail:
        detail = f"{detail} ({extra_detail})"
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


@router.get(
    "/assistant/status",
    response_model=ApiResponse[dict],
)
async def assistant_status(
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Diagnostics — does NOT call the provider; cheap to poll."""
    _ = user  # auth-required so the endpoint is not anonymously enumerable
    s = get_provider_status()
    return ApiResponse(
        meta=make_meta(),
        data={
            "configured": s.configured,
            "provider": s.provider_name,
            "detail": s.detail,
        },
    )


async def _chat_or_503(messages: list[LLMMessage], *, max_tokens: int = 1024) -> ChatResponse:
    provider = get_provider()
    if provider is None:
        raise _service_unavailable()
    try:
        resp = await provider.chat(messages, max_tokens=max_tokens)
    except StubProviderError as e:
        raise _service_unavailable(str(e))
    return ChatResponse(
        text=resp.text,
        provider=resp.provider,
        model=resp.model,
        input_tokens=resp.input_tokens,
        output_tokens=resp.output_tokens,
    )


@router.post(
    "/assistant/chat",
    response_model=ApiResponse[ChatResponse],
)
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
) -> ApiResponse[ChatResponse]:
    _ = user
    messages: list[LLMMessage] = [LLMMessage(role="system", content=SYSTEM_PROMPT)]
    if payload.context:
        messages.append(LLMMessage(role="user", content=f"Context:\n{payload.context}"))
    messages.append(LLMMessage(role="user", content=payload.question))
    data = await _chat_or_503(messages, max_tokens=1024)
    return ApiResponse(meta=make_meta(), data=data)


@router.post(
    "/assistant/narrative",
    response_model=ApiResponse[ChatResponse],
)
async def narrative(
    payload: NarrativeRequest,
    user: User = Depends(get_current_user),
) -> ApiResponse[ChatResponse]:
    _ = user
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=(
                "Synthesize a 3-paragraph evidence narrative for the recommendation "
                f"below. Cite the engine driver(s). Recommendation ID: {payload.recommendation_id}.\n\n"
                f"{payload.context}"
            ),
        ),
    ]
    data = await _chat_or_503(messages, max_tokens=800)
    return ApiResponse(meta=make_meta(), data=data)


@router.post(
    "/assistant/news-explain",
    response_model=ApiResponse[ChatResponse],
)
async def news_explain(
    payload: NewsExplainRequest,
    user: User = Depends(get_current_user),
) -> ApiResponse[ChatResponse]:
    _ = user
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=(
                "Explain in 2-3 sentences why this headline might matter to the "
                "portfolio context below. Do not predict direction. Cite the "
                "portfolio constraint or position that would be affected.\n\n"
                f"Headline: {payload.headline}\n"
                f"Summary: {payload.summary or '(none)'}\n\n"
                f"Portfolio context:\n{payload.context}"
            ),
        ),
    ]
    data = await _chat_or_503(messages, max_tokens=400)
    return ApiResponse(meta=make_meta(), data=data)
