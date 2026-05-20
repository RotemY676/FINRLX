"""Auth endpoints (Phase MVP-1).

POST /auth/signup     — gated by email_allowlist; returns user + token pair
POST /auth/login      — email + password; returns user + token pair
POST /auth/refresh    — refresh token rotation (parent revoked, child issued)
POST /auth/logout     — revoke refresh token
GET  /auth/me         — return the authenticated user

Security notes:
- Passwords hashed with bcrypt (cost from settings)
- Refresh tokens stored as SHA-256 hash; plaintext sent to client once
- Email comparison is lower-cased to prevent case-based bypass
- Generic error messages on auth failures (no username enumeration)
- Email allowlist enforced when settings.require_email_allowlist=True
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.core.auth import (
    generate_refresh_token_pair,
    hash_password,
    hash_refresh_token,
    issue_access_token,
    refresh_expires_at,
    timing_safe_dummy_hash,
    verify_password,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.auth import EmailAllowlist, RefreshToken, User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    SignupRequest,
    TokenPair,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])


_GENERIC_AUTH_FAIL = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


async def _is_allowlisted(db: AsyncSession, email: str) -> bool:
    if not settings.require_email_allowlist:
        return True
    # Caller already normalizes via _normalize_email; defense-in-depth here too.
    normalized = email.strip().lower()
    result = await db.execute(
        select(EmailAllowlist).where(EmailAllowlist.email == normalized)
    )
    return result.scalar_one_or_none() is not None


async def _issue_token_pair(
    db: AsyncSession,
    user: User,
    request: Request,
) -> tuple[TokenPair, RefreshToken]:
    """Issue access + refresh tokens. Returns (TokenPair, refresh_row).

    The refresh_row is returned by reference so callers (e.g. /auth/refresh)
    can link parent->child without a second SELECT (which was race-prone).
    """
    access_token, access_expires = issue_access_token(user_id=user.id, role=user.role)
    refresh_plain, refresh_hashed = generate_refresh_token_pair()
    refresh_row = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hashed,
        expires_at=refresh_expires_at(),
        user_agent=(request.headers.get("user-agent") or "")[:500] or None,
        ip_address=(request.client.host if request.client else None),
    )
    db.add(refresh_row)
    pair = TokenPair(
        access_token=access_token,
        refresh_token=refresh_plain,
        access_token_expires_at=access_expires,
    )
    return pair, refresh_row


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    email = _normalize_email(payload.email)

    if not await _is_allowlisted(db, email):
        # Generic message to avoid leaking allowlist membership.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signup is currently invite-only. Contact the operator to be added.",
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        # Generic message — do not leak that the address is registered.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create account with the provided details",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
        role="user",
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    tokens, _ = await _issue_token_pair(db, user, request)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(user=_to_user_public(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    email = _normalize_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Pay the bcrypt cost on the miss-path too so timing doesn't leak existence.
        verify_password(payload.password, timing_safe_dummy_hash())
        raise _GENERIC_AUTH_FAIL

    if not user.is_active:
        raise _GENERIC_AUTH_FAIL

    if not verify_password(payload.password, user.password_hash):
        raise _GENERIC_AUTH_FAIL

    user.last_login_at = datetime.now(timezone.utc)
    tokens, _ = await _issue_token_pair(db, user, request)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(user=_to_user_public(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_row = result.scalar_one_or_none()

    if refresh_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    now = datetime.now(timezone.utc)
    if refresh_row.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    # SQLite strips tz info on round-trip; treat naive timestamps as UTC.
    expires_at = refresh_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user_result = await db.execute(select(User).where(User.id == refresh_row.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

    # Rotate: issue child + revoke parent + link, all in one transaction.
    new_tokens, new_row = await _issue_token_pair(db, user, request)
    refresh_row.revoked_at = now
    refresh_row.replaced_by_id = new_row.id
    await db.commit()
    return new_tokens


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_row = result.scalar_one_or_none()
    if refresh_row is None:
        # Idempotent: silently succeed.
        return {"ok": True}
    if refresh_row.user_id != current_user.id:
        # Token belongs to a different user — refuse without leaking ownership.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token does not belong to the authenticated user",
        )
    if refresh_row.revoked_at is None:
        refresh_row.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return _to_user_public(current_user)
