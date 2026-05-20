"""Shared API dependencies."""
from datetime import UTC, datetime

from app.schemas.common import ResponseMeta


def make_meta(warnings: list[str] | None = None) -> ResponseMeta:
    return ResponseMeta(
        api_version="v1",
        generated_at=datetime.now(UTC),
        warnings=warnings or [],
    )
