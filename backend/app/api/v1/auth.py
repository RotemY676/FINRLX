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
- US-P0-04: replaying an already-rotated refresh token revokes the whole
  descendant chain (OAuth 2.0 Security BCP §4.14.2 replay detection)
"""
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
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
from app.core.rate_limit import limiter
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

logger = logging.getLogger(__name__)

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

    The flush below is load-bearing: `RefreshToken.id` is a Python-side column
    default (`default=gen_uuid`) applied at INSERT, so before flushing the
    attribute is still None. Without it, `parent.replaced_by_id = child.id`
    silently persisted NULL and the rotation chain was never actually linked —
    which US-P0-04 replay detection needs to walk.
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
    await db.flush()  # populates refresh_row.id — see docstring
    pair = TokenPair(
        access_token=access_token,
        refresh_token=refresh_plain,
        access_token_expires_at=access_expires,
    )
    return pair, refresh_row


async def _revoke_descendants(
    db: AsyncSession, start: RefreshToken, now: datetime
) -> int:
    """Revoke every token descended from ``start`` via the rotation chain.

    US-P0-04. Rotation already revoked the parent on each refresh, so a client
    presenting an *already revoked* token is replaying one that should have
    been discarded — the signature of a stolen token. Rejecting that single
    request is not enough: whoever rotated it legitimately still holds a live
    child, so the attacker (or the victim) keeps a working session.

    Walking `replaced_by_id` forward and revoking the chain kills both sides,
    forcing a fresh login. The `seen` set guards against a cyclic chain
    (corruption or a crafted row) turning this into an infinite loop.
    """
    revoked = 0
    seen = {start.id}
    cursor = start.replaced_by_id
    while cursor and cursor not in seen:
        seen.add(cursor)
        row = (await db.execute(
            select(RefreshToken).where(RefreshToken.id == cursor)
        )).scalar_one_or_none()
        if row is None:
            break
        if row.revoked_at is None:
            row.revoked_at = now
            revoked += 1
        cursor = row.replaced_by_id
    return revoked


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth)
async def signup(
    request: Request,
    payload: Annotated[SignupRequest, Body()],
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
        last_login_at=datetime.now(UTC),
    )
    db.add(user)
    await db.flush()

    tokens, _ = await _issue_token_pair(db, user, request)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(user=_to_user_public(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
@limiter.limit(settings.rate_limit_auth)
async def login(
    request: Request,
    payload: Annotated[LoginRequest, Body()],
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

    user.last_login_at = datetime.now(UTC)
    tokens, _ = await _issue_token_pair(db, user, request)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(user=_to_user_public(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit(settings.rate_limit_auth)
async def refresh(
    request: Request,
    payload: Annotated[RefreshRequest, Body()],
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_row = result.scalar_one_or_none()

    if refresh_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    now = datetime.now(UTC)
    if refresh_row.revoked_at is not None:
        # US-P0-04 replay detection: a revoked token being presented again means
        # it leaked. Kill the whole chain descended from it, not just this call.
        revoked = await _revoke_descendants(db, refresh_row, now)
        await db.commit()
        logger.warning(
            "refresh token replay detected for user %s; revoked %d descendant token(s)",
            refresh_row.user_id,
            revoked,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    # SQLite strips tz info on round-trip; treat naive timestamps as UTC.
    expires_at = refresh_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
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
        refresh_row.revoked_at = datetime.now(UTC)
        await db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return _to_user_public(current_user)


# ── Sign in with Google ─────────────────────────────────────────────


import secrets as _secrets  # noqa: E402
from urllib.parse import urlencode as _urlencode  # noqa: E402

from fastapi.responses import RedirectResponse  # noqa: E402

from app.services.google_oauth import (  # noqa: E402
    GoogleOAuthDisabled,
    GoogleOAuthError,
    build_authorization_url,
    exchange_code_for_id_token,
    verify_id_token,
)

GOOGLE_STATE_COOKIE = "finrlx_google_state"
GOOGLE_STATE_COOKIE_MAX_AGE = 600  # 10 minutes


@router.get("/google/start")
async def google_oauth_start() -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen.

    Stores a random ``state`` token in an HttpOnly cookie + embeds the
    same value in the URL. The callback verifies both match before
    accepting the response — standard CSRF protection.
    """
    try:
        state = _secrets.token_urlsafe(32)
        url = build_authorization_url(state)
    except GoogleOAuthDisabled as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    response = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        GOOGLE_STATE_COOKIE,
        state,
        max_age=GOOGLE_STATE_COOKIE_MAX_AGE,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
    )
    return response


@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Exchange Google's code for our own access token + redirect FE.

    Allowlist enforced same as password signup: a Gmail address not in
    ``email_allowlist`` cannot proceed.
    """
    # 1) Google reported an error before reaching us
    if error:
        return _google_callback_failure(f"Google: {error}")

    # 2) Required params present
    if not code or not state:
        return _google_callback_failure("missing code or state")

    # 3) State matches the cookie we set in /start
    cookie_state = request.cookies.get(GOOGLE_STATE_COOKIE)
    if not cookie_state or cookie_state != state:
        return _google_callback_failure("state mismatch")

    # 4) Exchange code → id_token, verify the signature + claims
    try:
        id_token = await exchange_code_for_id_token(code)
        claims = verify_id_token(id_token)
    except GoogleOAuthDisabled as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except GoogleOAuthError as exc:
        return _google_callback_failure(f"verification: {exc}")

    email = _normalize_email(claims.email)

    # 5) Same allowlist gate as password signup
    if not await _is_allowlisted(db, email):
        return _google_callback_failure(
            "not_allowlisted: contact the operator to be added"
        )

    # 6) Find-or-create user. Existing users keep their password (if any);
    # new users get a random unusable password — Google sign-in is the
    # only credential they have until they explicitly set one.
    existing = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is None:
        user = User(
            email=email,
            password_hash=hash_password(_secrets.token_urlsafe(48)),
            is_active=True,
            role="user",
            last_login_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()
    else:
        if not existing.is_active:
            return _google_callback_failure("account inactive")
        user = existing
        user.last_login_at = datetime.now(UTC)

    tokens, _ = await _issue_token_pair(db, user, request)
    await db.commit()
    await db.refresh(user)

    # 7) Redirect to the frontend's "finish" page with our own tokens
    # in the URL fragment so they don't hit the server log.
    frag = _urlencode(
        {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "access_token_expires_at": tokens.access_token_expires_at.isoformat(),
            "user_email": user.email,
        }
    )
    redirect = RedirectResponse(
        f"{settings.google_oauth_post_login_redirect}#{frag}",
        status_code=status.HTTP_302_FOUND,
    )
    redirect.delete_cookie(GOOGLE_STATE_COOKIE)
    return redirect


def _google_callback_failure(reason: str) -> RedirectResponse:
    """Bounce to the FE with an ``error=`` query string for display."""
    frag = _urlencode({"error": reason})
    return RedirectResponse(
        f"{settings.google_oauth_post_login_redirect}?{frag}",
        status_code=status.HTTP_302_FOUND,
    )
