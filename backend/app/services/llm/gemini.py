"""Google Gemini provider — Phase 17.4 free-tier fallback.

Activation:
  1. Get a free API key at https://aistudio.google.com/apikey
  2. Set `LLM_GEMINI_API_KEY` env var.
  3. Set `LLM_PROVIDER=gemini` (single-provider mode) OR add
     `gemini` to `LLM_PROVIDER_CHAIN` (cascading mode).
  4. Optionally set `LLM_MODEL` — defaults to gemini-2.5-flash, which
     has a 1M-token context window (fits full 10-K filings in one
     shot) and is on the Google free-tier today.

NOTE on model IDs: Google rotates model availability on the v1beta
endpoint frequently (1.5-flash was retired in early 2026 in favor of
2.x). If the default ID ever returns 404, the API response includes a
pointer to ModelService.ListModels — set LLM_MODEL to a currently
available ID as a hotfix while the default is updated. To list what
your key can use:

    curl "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_KEY}" \
      | jq '.models[] | select(.supportedGenerationMethods[]? == "generateContent") | .name'

Why httpx instead of the google-generativeai SDK:
  - One fewer dependency. httpx is already in requirements.txt for
    the rest of the app.
  - The REST contract is small and stable (one POST, one JSON body).
    The SDK pulls in grpc / proto / auth machinery we don't need.
  - Easier to mock in tests — we control the wire shape directly.

Free-tier note: Google enforces the free quota at their end. When the
caller exceeds it, the API returns 429; we translate that into a
StubProviderError so the cascading router can fall back to the next
provider. The budget tracker still records tokens against the gemini
bucket (cost field is paid-tier price; on free tier real cost is $0,
but we keep the worst-case estimate so the operator-visible dollar
figure stays conservative).
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.services.llm.provider import LLMProvider, StubProviderError
from app.services.llm.types import LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


_DEFAULT_MODEL = "gemini-2.5-flash"
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
_REQUEST_TIMEOUT_SECONDS = 120.0

# Retry config for transient upstream errors (5xx, timeout). One
# retry with a short backoff handles the common "Google API hiccup"
# case without making the request hang noticeably longer when the
# outage is real. Auth / rate-limit / 4xx errors are NOT retried —
# they're not going to fix themselves on the next attempt.
_MAX_RETRIES_ON_5XX = 1
_RETRY_BACKOFF_SECONDS = 1.5


class GeminiProvider(LLMProvider):
    name = "gemini"

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
        if not self.api_key:
            raise StubProviderError(
                "LLM_GEMINI_API_KEY is empty. Set it in the backend "
                "environment to activate the Gemini provider."
            )

        # Gemini's REST shape: `contents` is the conversation turn list,
        # `systemInstruction` is a separate top-level field (mirrors
        # Anthropic's `system` kwarg). Roles are "user" or "model" — we
        # translate "assistant" → "model" on the way out.
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        contents = [
            {
                "role": "model" if m.role == "assistant" else "user",
                "parts": [{"text": m.content}],
            }
            for m in messages
            if m.role != "system"
        ]
        if not contents:
            raise StubProviderError(
                "Gemini call attempted with only system messages — "
                "the API requires at least one user message."
            )

        body: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_text:
            body["systemInstruction"] = {"parts": [{"text": system_text}]}

        url = f"{_API_BASE}/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        # Retry loop: 5xx (server error) and TimeoutException are
        # transient and worth one retry. Auth / 4xx errors break out
        # immediately — they won't fix themselves.
        resp: httpx.Response | None = None
        last_transient_reason: str | None = None
        for attempt in range(_MAX_RETRIES_ON_5XX + 1):
            try:
                async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                    resp = await client.post(url, params=params, json=body)
            except httpx.TimeoutException as e:
                last_transient_reason = f"timeout: {e}"
                if attempt < _MAX_RETRIES_ON_5XX:
                    logger.warning(
                        "Gemini timed out (attempt %d/%d); retrying after %.1fs",
                        attempt + 1, _MAX_RETRIES_ON_5XX + 1, _RETRY_BACKOFF_SECONDS,
                    )
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                    continue
                raise StubProviderError(
                    "Gemini request timed out after retry. Try again in a moment "
                    "or check Google's status page (status.cloud.google.com)."
                ) from e
            except httpx.HTTPError as e:
                # Network-level failure (DNS, connection refused, etc.).
                # Not retried — usually a deploy-environment issue.
                raise StubProviderError(
                    f"Gemini network error: {e}. The endpoint may be "
                    "unreachable from this backend instance."
                ) from e

            if resp.status_code < 500:
                break  # 2xx/3xx/4xx — handled outside the loop
            # 5xx → retry once, then fall through to the error
            last_transient_reason = f"status {resp.status_code}"
            if attempt < _MAX_RETRIES_ON_5XX:
                logger.warning(
                    "Gemini returned %d (attempt %d/%d); retrying after %.1fs",
                    resp.status_code, attempt + 1, _MAX_RETRIES_ON_5XX + 1,
                    _RETRY_BACKOFF_SECONDS,
                )
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                continue

        # `resp` is guaranteed set here — every loop branch either
        # returns or assigns it.
        assert resp is not None

        if resp.status_code == 401 or resp.status_code == 403:
            raise StubProviderError(
                "Gemini auth failed: invalid or expired LLM_GEMINI_API_KEY."
            )
        if resp.status_code == 429:
            raise StubProviderError(
                "Gemini rate-limit / free-tier quota hit. Retry later, "
                "or fall back to a paid provider via LLM_PROVIDER_CHAIN."
            )
        if resp.status_code >= 500:
            # Persistent 5xx after retry = real upstream outage. Make
            # the message actionable so the operator knows where to look.
            raise StubProviderError(
                f"Gemini API returned status {resp.status_code} after "
                f"{_MAX_RETRIES_ON_5XX + 1} attempts (last: {last_transient_reason}). "
                "Likely a transient Google API outage — retry in 1–2 minutes, "
                "or check https://status.cloud.google.com. To avoid single-"
                "provider outages taking the pipeline down, configure a paid "
                "fallback (LLM_PROVIDER_CHAIN=gemini,anthropic)."
            )
        if resp.status_code >= 400:
            # 400s carry a useful error message in the body; surface it
            # without leaking the API key (which is in the query string,
            # not the response).
            try:
                detail = resp.json().get("error", {}).get("message", "")
            except ValueError:
                detail = ""
            raise StubProviderError(
                f"Gemini API rejected the request ({resp.status_code}): {detail}"
            )

        try:
            payload = resp.json()
        except ValueError as e:
            raise StubProviderError(
                "Gemini returned a non-JSON response."
            ) from e

        candidates = payload.get("candidates") or []
        if not candidates:
            # Gemini withheld content (safety filter or empty generation).
            # Surface honestly so the cascading router can fall back.
            block_reason = (
                payload.get("promptFeedback", {}).get("blockReason")
                or "no candidates returned"
            )
            raise StubProviderError(
                f"Gemini returned no candidates ({block_reason})."
            )

        parts = candidates[0].get("content", {}).get("parts") or []
        text = "\n\n".join(p.get("text", "") for p in parts if "text" in p).strip()
        if not text:
            raise StubProviderError(
                "Gemini returned an empty text response."
            )

        usage = payload.get("usageMetadata", {})
        return LLMResponse(
            text=text,
            provider="gemini",
            model=self.model,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
        )
