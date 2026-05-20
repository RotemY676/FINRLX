"""Common API contracts: response envelope, errors, pagination.

Maps to API Contract doc 12, Common Response Envelope.
"""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class FreshnessState(BaseModel):
    data_as_of: datetime | None = None
    is_stale: bool = False
    staleness_reason: str | None = None


class TypedError(BaseModel):
    code: str
    category: str  # validation, not_found, conflict, internal, upstream
    message: str
    retryable: bool = False
    object_ref: str | None = None
    trace_id: str | None = None


class ResponseMeta(BaseModel):
    trace_id: str | None = None
    api_version: str = "v1"
    generated_at: datetime
    warnings: list[str] = Field(default_factory=list)
    freshness: FreshnessState | None = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope per doc 12."""
    meta: ResponseMeta
    data: T


class ErrorResponse(BaseModel):
    meta: ResponseMeta
    errors: list[TypedError]


class PaginationCursor(BaseModel):
    cursor: str | None = None
    has_more: bool = False
    total: int | None = None
