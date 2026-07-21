"""Build the runtime inventory manifest (US-P0-01).

Enumerates the live FastAPI app into a machine-readable manifest: every route
with its authorization level (derived from the actual dependency graph), feature
flags with current values, provider configuration presence, registered schema
contracts, and runtime pins.

The builder is pure with respect to I/O: it reads the app's route table and the
settings object, and never performs network or database access. It never emits
secret values — only whether a provider is configured.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.core.config import Settings
from app.core.route_policy import classify_public_routes
from app.schemas.inventory import (
    FlagInfo,
    ProviderInfo,
    RouteInfo,
    RuntimeInventory,
)
from app.services.provenance import PIPELINE_VERSION

# Auth dependency call names we can detect in the route dependency graph.
_REQUIRED_AUTH_CALLS = {"get_current_user"}
_OPTIONAL_AUTH_CALLS = {"get_optional_user"}


def _collect_dependency_calls(dependant, seen: set[int] | None = None) -> set[str]:
    """Recursively collect the __name__ of every callable in a route's graph."""
    seen = seen if seen is not None else set()
    names: set[str] = set()
    if dependant is None or id(dependant) in seen:
        return names
    seen.add(id(dependant))
    call = getattr(dependant, "call", None)
    if call is not None:
        names.add(getattr(call, "__name__", ""))
    for sub in getattr(dependant, "dependencies", []) or []:
        names |= _collect_dependency_calls(sub, seen)
    return names


def _classify_auth(route: APIRoute) -> str:
    calls = _collect_dependency_calls(getattr(route, "dependant", None))
    if calls & _REQUIRED_AUTH_CALLS:
        return "required"
    if calls & _OPTIONAL_AUTH_CALLS:
        return "optional"
    return "public"


def _route_info(route: APIRoute) -> RouteInfo:
    methods = sorted(m for m in (route.methods or set()) if m not in {"HEAD", "OPTIONS"})
    response_model = None
    model = getattr(route, "response_model", None)
    if model is not None:
        response_model = getattr(model, "__name__", str(model))
    return RouteInfo(
        path=route.path,
        methods=methods,
        name=route.name,
        tags=[str(t) for t in (route.tags or [])],
        auth=_classify_auth(route),
        response_model=response_model,
    )


def _flags(settings: Settings) -> list[FlagInfo]:
    """All boolean flag-like settings, sorted by name."""
    # Explicit non-`feature_`-prefixed booleans that are genuine rollout flags.
    extra_flag_names = {"leap_price_chain", "insights_annotations", "finnhub_premium"}
    flags: list[FlagInfo] = []
    for name, value in settings.model_dump().items():
        is_flag = name.startswith("feature_") or name in extra_flag_names
        if is_flag and isinstance(value, bool):
            flags.append(FlagInfo(name=name, value=value))
    return sorted(flags, key=lambda f: f.name)


def _providers(settings: Settings) -> list[ProviderInfo]:
    """Provider configuration presence — booleans only, never secret values."""

    def _set(field: str) -> bool:
        return bool(str(getattr(settings, field, "") or "").strip())

    llm_configured = _set("llm_provider") or _set("llm_provider_chain")
    fundamentals_configured = _set("fundamentals_provider") and _set(
        "fundamentals_finnhub_api_key"
    )
    return [
        ProviderInfo(
            name="llm",
            configured=llm_configured,
            detail="single or cascading chain configured" if llm_configured else "unset (assistant endpoints 503)",
        ),
        ProviderInfo(
            name="llm_anthropic_key", configured=_set("llm_anthropic_api_key")
        ),
        ProviderInfo(name="llm_openai_key", configured=_set("llm_openai_api_key")),
        ProviderInfo(name="llm_gemini_key", configured=_set("llm_gemini_api_key")),
        ProviderInfo(
            name="fundamentals",
            configured=fundamentals_configured,
            detail="finnhub" if fundamentals_configured else "stub",
        ),
        ProviderInfo(name="price_chain", configured=bool(settings.leap_price_chain)),
        ProviderInfo(
            name="google_oauth", configured=_set("google_oauth_client_secret")
        ),
    ]


def _db_dialect(database_url: str) -> str:
    """Return only the scheme/dialect — never the full URL (may embed a password)."""
    scheme = database_url.split(":", 1)[0] if database_url else ""
    return scheme.split("+", 1)[0] or "unknown"


def _environment(settings: Settings) -> str:
    dialect = _db_dialect(settings.database_url)
    if settings.debug or dialect == "sqlite":
        return "development"
    return "production"


def build_runtime_inventory(*, app: FastAPI, settings: Settings, now: datetime) -> RuntimeInventory:
    api_routes = [r for r in app.routes if isinstance(r, APIRoute)]
    routes = sorted(
        (_route_info(r) for r in api_routes),
        key=lambda ri: (ri.path, ",".join(ri.methods)),
    )

    auth_summary: dict[str, int] = {"public": 0, "optional": 0, "required": 0}
    for ri in routes:
        auth_summary[ri.auth] = auth_summary.get(ri.auth, 0) + 1

    # US-P0-03 route-authorization audit over the currently-public routes.
    public_entries = [
        f"{method} {ri.path}" for ri in routes if ri.auth == "public" for method in ri.methods
    ]
    authz_split = classify_public_routes(public_entries)
    authz = {k: len(v) for k, v in authz_split.items()}

    schema_contracts = sorted(
        {ri.response_model for ri in routes if ri.response_model}
    )

    pins: dict[str, str | None] = {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "pipeline_version": PIPELINE_VERSION,
        "python_version": sys.version.split()[0],
        "db_dialect": _db_dialect(settings.database_url),
        # Railway injects the commit SHA; absent locally — never fabricated.
        "git_commit": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
    }

    return RuntimeInventory(
        generated_at=now,
        environment=_environment(settings),
        pins=pins,
        route_count=len(routes),
        auth_summary=auth_summary,
        authz=authz,
        unclassified_public_routes=authz_split["unclassified"],
        routes=routes,
        flags=_flags(settings),
        providers=_providers(settings),
        schema_contracts=schema_contracts,
    )
