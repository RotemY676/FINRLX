"""Runtime inventory manifest contracts (US-P0-01).

A machine-readable snapshot of the running service: routes with their
authorization level, feature flags with live values, provider configuration
(presence only — never secret values), registered schema contracts, and runtime
pins. Consumed by an operator/admin-only endpoint so the current baseline can be
diffed against the specification without reading the code.

Security: this manifest deliberately reports only *booleans* for provider
configuration and never surfaces secrets, keys, tokens, or the database URL
(which may embed credentials). Only the database dialect is exposed.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RouteInfo(BaseModel):
    path: str
    methods: list[str]
    name: str | None = None
    tags: list[str] = Field(default_factory=list)
    auth: str  # "public" | "optional" | "required"
    response_model: str | None = None


class FlagInfo(BaseModel):
    name: str
    value: bool


class ProviderInfo(BaseModel):
    name: str
    configured: bool
    detail: str | None = None


class RuntimeInventory(BaseModel):
    generated_at: datetime
    environment: str
    pins: dict[str, str | None] = Field(default_factory=dict)
    route_count: int
    auth_summary: dict[str, int] = Field(default_factory=dict)
    # US-P0-03: split of the currently-public routes into
    # allowed / known-debt / unclassified counts. `unclassified` must be 0.
    authz: dict[str, int] = Field(default_factory=dict)
    unclassified_public_routes: list[str] = Field(default_factory=list)
    routes: list[RouteInfo] = Field(default_factory=list)
    flags: list[FlagInfo] = Field(default_factory=list)
    providers: list[ProviderInfo] = Field(default_factory=list)
    schema_contracts: list[str] = Field(default_factory=list)
