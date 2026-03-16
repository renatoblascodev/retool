"""Templates router — browse and instantiate app templates."""
from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.schemas import AppResponse
from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import AppMember, Page, Template, ToolApp, User
from app.templates.schemas import AppFromTemplateRequest, SEED_TEMPLATES, TemplateResponse

router = APIRouter(prefix="/templates", tags=["templates"])


async def _ensure_seeds(db: AsyncSession) -> None:
    """Insert seed templates if the table is empty."""
    count_row = await db.scalar(select(Template))
    if count_row is not None:
        return
    for seed in SEED_TEMPLATES:
        db.add(Template(**seed))
    await db.commit()


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[TemplateResponse]:
    await _ensure_seeds(db)
    rows = await db.scalars(select(Template).order_by(Template.name))
    return [TemplateResponse.model_validate(t) for t in rows]


@router.post(
    "/from-template",
    response_model=AppResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_app_from_template(
    payload: AppFromTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    await _ensure_seeds(db)
    tmpl = await db.scalar(
        select(Template).where(Template.slug == payload.template_slug)
    )
    if tmpl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{payload.template_slug}' not found",
        )

    # Parse layout to extract queries for the first page
    try:
        layout = json.loads(tmpl.layout_json)
    except (json.JSONDecodeError, TypeError):
        layout = {}

    tool_app = ToolApp(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description or tmpl.description,
    )
    db.add(tool_app)
    await db.flush()

    # Auto-membership
    db.add(AppMember(app_id=tool_app.id, user_id=current_user.id, role="owner"))

    # Create initial page with template layout
    page_layout = {
        "widgets": layout.get("widgets", []),
        "queries": layout.get("queries", []),
    }
    page = Page(
        app_id=tool_app.id,
        name="Main",
        slug="main",
        layout_json=page_layout,
    )
    db.add(page)

    await db.commit()
    await db.refresh(tool_app)
    return AppResponse.model_validate(tool_app)
