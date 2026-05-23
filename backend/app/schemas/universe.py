"""Universe CRUD schemas — Phase 20.

Read-only viewer endpoints (list / detail / coverage / readiness) return raw
dicts assembled by UniverseService. The new CRUD endpoints take typed bodies
so FastAPI rejects garbage input before it reaches the service.
"""
from pydantic import BaseModel, Field


class UniverseCreateRequest(BaseModel):
    """Body for POST /universes. The name uniqueness constraint is enforced
    in the DB; the service translates the IntegrityError into a 409."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1024)


class UniverseUpdateRequest(BaseModel):
    """Body for PATCH /universes/{id}. All fields optional — the service
    only touches the keys the client sent (PATCH semantics). is_active is
    exposed so deactivation can be performed via PATCH; the dedicated
    DELETE endpoint aliases is_active=false for REST friendliness."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1024)
    is_active: bool | None = None
