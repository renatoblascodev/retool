from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import Page, ToolApp, User
from app.pages.schemas import (
    PageCreateRequest,
    PageResponse,
    PageUpdateRequest,
)

router = APIRouter(prefix="/apps/{app_id}/pages", tags=["pages"])


async def _get_owned_app(
    app_id: str,
    db: AsyncSession,
    user_id: str,
) -> ToolApp:
    tool_app = await db.scalar(
        select(ToolApp).where(
            ToolApp.id == app_id,
            ToolApp.owner_id == user_id,
        ),
    )
    if tool_app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return tool_app


async def _get_owned_page(
    app_id: str,
    page_id: str,
    db: AsyncSession,
    user_id: str,
) -> Page:
    await _get_owned_app(app_id, db, user_id)

    page = await db.scalar(
        select(Page).where(Page.id == page_id, Page.app_id == app_id),
    )
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )
    return page


@router.get("", response_model=list[PageResponse])
async def list_pages(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[PageResponse]:
    await _get_owned_app(app_id, db, current_user.id)
    rows = await db.scalars(
        select(Page).where(Page.app_id == app_id).order_by(Page.created_at.desc()),
    )
    return [PageResponse.model_validate(row) for row in rows]


@router.post(
    "",
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_page(
    app_id: str,
    payload: PageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PageResponse:
    await _get_owned_app(app_id, db, current_user.id)

    page = Page(
        app_id=app_id,
        name=payload.name,
        slug=payload.slug,
        layout_json=payload.layout_json,
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return PageResponse.model_validate(page)


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    app_id: str,
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PageResponse:
    page = await _get_owned_page(app_id, page_id, db, current_user.id)
    return PageResponse.model_validate(page)


@router.patch("/{page_id}", response_model=PageResponse)
async def update_page(
    app_id: str,
    page_id: str,
    payload: PageUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PageResponse:
    page = await _get_owned_page(app_id, page_id, db, current_user.id)

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(page, key, value)

    await db.commit()
    await db.refresh(page)
    return PageResponse.model_validate(page)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    app_id: str,
    page_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    page = await _get_owned_page(app_id, page_id, db, current_user.id)
    await db.delete(page)
    await db.commit()
