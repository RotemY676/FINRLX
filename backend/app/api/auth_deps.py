"""Auth dependencies (Phase MVP-1).

get_current_user — required. Returns the active User row or raises 401.
get_optional_user — returns User or None; used by mixed-auth endpoints.

Both rely on a Bearer token in the Authorization header.
"""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token
from app.core.database import get_db
from app.models.auth import User

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def _extract_bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


async def _resolve_user(request: Request, db: AsyncSession) -> User | None:
    token = _extract_bearer(request)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        return None
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _resolve_user(request, db)
    if user is None:
        raise _UNAUTHORIZED
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    return await _resolve_user(request, db)
