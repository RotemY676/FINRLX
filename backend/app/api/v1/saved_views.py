"""Phase B3 — saved views CRUD.

Backs the sidebar's "Saved views" list with a per-user DB-backed
collection instead of the hardcoded array. Every endpoint is gated by
get_current_user and scoped to the caller's user_id — no cross-tenant
reads or writes.

Routes:
  GET    /api/v1/saved-views                 — list mine
  POST   /api/v1/saved-views                 — create a new view
  PATCH  /api/v1/saved-views/{id}            — rename / re-filter
  DELETE /api/v1/saved-views/{id}            — delete one
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import make_meta
from app.core.database import get_db
from app.models.auth import User
from app.models.saved_view import SavedView
from app.schemas.common import ApiResponse

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────


class SavedViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scope: str = Field(..., min_length=1, max_length=40)
    filters: dict = Field(default_factory=dict)
    tone: str | None = Field(default=None, max_length=20)


class SavedViewUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    scope: str | None = Field(default=None, min_length=1, max_length=40)
    filters: dict | None = None
    tone: str | None = Field(default=None, max_length=20)


class SavedViewResponse(BaseModel):
    id: str
    name: str
    scope: str
    filters: dict
    tone: str | None
    created_at: str
    updated_at: str


def _to_response(view: SavedView) -> SavedViewResponse:
    try:
        filters = json.loads(view.filters_json or "{}")
    except json.JSONDecodeError:
        filters = {}
    return SavedViewResponse(
        id=view.id,
        name=view.name,
        scope=view.scope,
        filters=filters,
        tone=view.tone,
        created_at=view.created_at.isoformat() if view.created_at else "",
        updated_at=view.updated_at.isoformat() if view.updated_at else "",
    )


# ── Routes ───────────────────────────────────────────────────────────


@router.get("/saved-views", response_model=ApiResponse[list[SavedViewResponse]])
async def list_my_saved_views(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(SavedView)
        .where(SavedView.user_id == user.id)
        .order_by(SavedView.created_at.asc())
    )).scalars().all()
    return ApiResponse(meta=make_meta(), data=[_to_response(r) for r in rows])


@router.post("/saved-views", response_model=ApiResponse[SavedViewResponse])
async def create_saved_view(
    body: SavedViewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    view = SavedView(
        user_id=user.id,
        name=body.name,
        scope=body.scope,
        filters_json=json.dumps(body.filters, sort_keys=True),
        tone=body.tone,
    )
    db.add(view)
    await db.commit()
    await db.refresh(view)
    return ApiResponse(meta=make_meta(), data=_to_response(view))


@router.patch("/saved-views/{view_id}", response_model=ApiResponse[SavedViewResponse])
async def update_saved_view(
    view_id: str,
    body: SavedViewUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    view = (await db.execute(
        select(SavedView).where(SavedView.id == view_id, SavedView.user_id == user.id)
    )).scalar_one_or_none()
    if view is None:
        # 404 not 403 — leaking "exists but you can't see it" is a worse signal
        # than uniformly "not found" for the tenant boundary.
        raise HTTPException(status_code=404, detail="Saved view not found")
    if body.name is not None:
        view.name = body.name
    if body.scope is not None:
        view.scope = body.scope
    if body.filters is not None:
        view.filters_json = json.dumps(body.filters, sort_keys=True)
    if body.tone is not None:
        view.tone = body.tone
    await db.commit()
    await db.refresh(view)
    return ApiResponse(meta=make_meta(), data=_to_response(view))


@router.delete("/saved-views/{view_id}", response_model=ApiResponse[dict])
async def delete_saved_view(
    view_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    view = (await db.execute(
        select(SavedView).where(SavedView.id == view_id, SavedView.user_id == user.id)
    )).scalar_one_or_none()
    if view is None:
        raise HTTPException(status_code=404, detail="Saved view not found")
    await db.delete(view)
    await db.commit()
    return ApiResponse(meta=make_meta(), data={"id": view_id, "deleted": True})
