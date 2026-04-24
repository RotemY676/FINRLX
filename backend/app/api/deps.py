"""Shared API dependencies."""
from datetime import datetime, timezone

from app.schemas.common import ResponseMeta


def make_meta(warnings: list[str] | None = None) -> ResponseMeta:
    return ResponseMeta(
        api_version="v1",
        generated_at=datetime.now(timezone.utc),
        warnings=warnings or [],
    )
