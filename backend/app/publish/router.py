"""Publish router — publish/unpublish apps and serve public snapshots."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.config import settings
from app.db import get_db_session
from app.models import AppMember, Page, ToolApp, User
from app.permissions.dependencies import require_role
from app.publish.schemas import PublicAppSnapshot, PublishResponse
from app.publish.service import generate_unique_slug

router = APIRouter(tags=["publish"])
public_router = APIRouter(tags=["public"])


# ---------------------------------------------------------------------------
# POST /apps/{app_id}/publish  — owner only
# ---------------------------------------------------------------------------

@router.post(
    "/apps/{app_id}/publish",
    response_model=PublishResponse,
    status_code=status.HTTP_200_OK,
)
async def publish_app(
    app_id: str,
    _member: AppMember = Depends(require_role("owner")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PublishResponse:
    tool_app = await db.get(ToolApp, app_id)
    if tool_app is None:
        raise HTTPException(status_code=404, detail="App not found")

    # Generate slug only if not already set
    if tool_app.slug is None:
        slug = await generate_unique_slug(tool_app.name, db)
        tool_app.slug = slug
    else:
        slug = tool_app.slug

    now = datetime.now(tz=timezone.utc)
    tool_app.is_published = True
    tool_app.published_at = now

    await db.commit()
    await db.refresh(tool_app)

    return PublishResponse(
        public_url=f"{settings.frontend_url}/r/{slug}",
        slug=slug,
        published_at=now,
    )


# ---------------------------------------------------------------------------
# DELETE /apps/{app_id}/publish  — owner only
# ---------------------------------------------------------------------------

@router.delete(
    "/apps/{app_id}/publish",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unpublish_app(
    app_id: str,
    _member: AppMember = Depends(require_role("owner")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    tool_app = await db.get(ToolApp, app_id)
    if tool_app is None:
        raise HTTPException(status_code=404, detail="App not found")

    tool_app.is_published = False
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# GET /r/{slug}  — public, no auth
# ---------------------------------------------------------------------------

@public_router.get(
    "/r/{slug}",
    response_model=PublicAppSnapshot,
)
async def get_public_app(
    slug: str,
    db: AsyncSession = Depends(get_db_session),
) -> PublicAppSnapshot:
    tool_app = await db.scalar(
        select(ToolApp).where(
            ToolApp.slug == slug,
            ToolApp.is_published.is_(True),
        )
    )
    if tool_app is None:
        raise HTTPException(status_code=404, detail="App not found")

    pages = await db.scalars(
        select(Page).where(Page.app_id == tool_app.id).order_by(Page.created_at)
    )

    pages_data = [
        {
            "id": page.id,
            "name": page.name,
            "slug": page.slug,
            "layout_json": page.layout_json,
        }
        for page in pages
    ]

    return PublicAppSnapshot(
        id=tool_app.id,
        name=tool_app.name,
        pages=pages_data,
    )
