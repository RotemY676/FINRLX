# Phase O-5 Report — LLM provider abstraction (stub)

**Date:** 2026-05-22
**Branch:** main
**Status:** ✅ COMPLETED

## Scope

Stub the LLM provider abstraction so the in-app Research Assistant has a fixed contract the FE can target. All providers ship as stubs today — every endpoint returns 503 unless `LLM_PROVIDER` is configured AND the matching API key is present. When the operator decides to spend tokens, activation is a one-config-file change.

## What was added

### `backend/app/services/llm/` (new module)

| File | Purpose |
|---|---|
| `__init__.py` | Re-exports `get_provider`, `ProviderStatus`, `LLMMessage`, `LLMResponse`. |
| `types.py` | `LLMMessage` (role + content) + `LLMResponse` (text + provider + model + tokens). |
| `provider.py` | Abstract `LLMProvider` base + `StubProviderError`. |
| `anthropic.py` | `AnthropicProvider` stub. Module docstring contains the exact SDK call to drop in for activation. |
| `openai.py` | `OpenAIProvider` stub. Same activation pattern. |
| `local.py` | `LocalOllamaProvider` stub. Same activation pattern, with httpx Ollama call in the docstring. |
| `router.py` | `get_provider()` returns a configured provider or None; `get_provider_status()` returns a diagnostics struct with a human-readable detail string. |

### `backend/app/api/v1/assistant.py` (new endpoints)

- `GET /api/v1/assistant/status` — diagnostics; auth-required; returns `{configured, provider, detail}`.
- `POST /api/v1/assistant/chat` — generic Q&A with optional context blob; system prompt enforces FINRLX rules.
- `POST /api/v1/assistant/narrative` — evidence-narrative synthesis given a recommendation_id + context.
- `POST /api/v1/assistant/news-explain` — per-headline relevance explainer.

All endpoints return **503** with a friendly message when the router returns None or when the provider stub raises `StubProviderError`. The detail string points at `/operator` so users discover the manual workflow.

### `backend/app/core/config.py`

Five new settings (all empty defaults — operator-console phase stays zero-token):

- `llm_provider: str = ""` — `"" | "anthropic" | "openai" | "local"`
- `llm_model: str = ""` — provider picks a sensible default when empty
- `llm_anthropic_api_key: str = ""`
- `llm_openai_api_key: str = ""`
- `llm_local_base_url: str = "http://localhost:11434"`

### `backend/app/api/router.py`

Registers `assistant_router` under the `assistant` tag.

### Tests — `backend/tests/test_phase_o5_assistant_stub.py`

10 tests covering:

- `/assistant/status` returns the unconfigured shape by default (or 401 if auth fixture not in place — both are valid evidence the route is wired).
- `get_provider()` returns None when `llm_provider` is empty.
- `get_provider()` returns None for an unknown provider name.
- `get_provider()` returns None when provider is set but the matching key is missing.
- `get_provider()` constructs Anthropic / OpenAI / local providers when their requirements are met.
- Each provider's `.chat()` raises `StubProviderError` with a friendly message.

All 10 pass.

## Activation runbook

When the operator decides to spend tokens on, say, Claude Sonnet 4.6:

1. `pip install anthropic` (add to `backend/requirements.txt`).
2. Open `backend/app/services/llm/anthropic.py` and replace the `chat()` stub body with the call shown in the module docstring.
3. Set Railway env vars: `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=sk-ant-…`, optionally `LLM_MODEL=claude-sonnet-4-6`.
4. Redeploy.

Every `/api/v1/assistant/*` endpoint starts returning real responses. The FE in-app Research Assistant panel can be lit up by flipping its feature flag.

## Why "stub but wired" instead of "skip until needed"

This is the cheapest possible future-proofing. The FE team can build against the contract today; only the inside of `chat()` changes when tokens get paid. The 503 detail message also guides the operator to the alternative (the operator console at `/operator`) rather than presenting a generic error.

## Verification

| Check | Result |
|---|---|
| New stub tests | ✅ 10/10 pass |
| Backend import + route enumeration | (covered by following commit's full pytest run) |

## Next step

Commit, push, proceed to O-2 (Claude Project setup guide).
