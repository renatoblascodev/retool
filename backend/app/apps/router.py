from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.schemas import AppCreateRequest, AppResponse, AppUpdateRequest
from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import AppMember, ToolApp, User
from app.permissions.dependencies import require_role

router = APIRouter(prefix="/apps", tags=["apps"])


async def _get_accessible_app(
    app_id: str,
    db: AsyncSession,
    user_id: str,
) -> ToolApp:
    """Return app if user is the owner OR a member (any role). 404 otherwise."""
    # First try membership table (covers Sprint 4A+ apps)
    member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == user_id,
        )
    )
    if member is not None:
        tool_app = await db.scalar(select(ToolApp).where(ToolApp.id == app_id))
        if tool_app is not None:
            return tool_app
    # Fallback: owner_id direct check (backward-compat for apps created before Sprint 4A)
    tool_app = await db.scalar(
        select(ToolApp).where(
            ToolApp.id == app_id,
            ToolApp.owner_id == user_id,
        )
    )
    if tool_app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return tool_app


# Keep legacy helper for write operations that still require owner check
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


@router.get("", response_model=list[AppResponse])
async def list_apps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[AppResponse]:
    rows = await db.scalars(
        select(ToolApp)
        .where(ToolApp.owner_id == current_user.id)
        .order_by(ToolApp.created_at.desc()),
    )
    return [AppResponse.model_validate(row) for row in rows]


@router.post(
    "",
    response_model=AppResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_app(
    payload: AppCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    tool_app = ToolApp(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(tool_app)
    await db.flush()  # get tool_app.id without full commit

    # Auto-insert owner membership so RBAC checks work immediately
    owner_member = AppMember(
        app_id=tool_app.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(owner_member)
    await db.commit()
    await db.refresh(tool_app)
    return AppResponse.model_validate(tool_app)


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    tool_app = await _get_accessible_app(app_id, db, current_user.id)
    return AppResponse.model_validate(tool_app)


@router.patch("/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: str,
    payload: AppUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    tool_app = await _get_owned_app(app_id, db, current_user.id)

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(tool_app, key, value)

    await db.commit()
    await db.refresh(tool_app)
    return AppResponse.model_validate(tool_app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    tool_app = await _get_owned_app(app_id, db, current_user.id)
    await db.delete(tool_app)
    await db.commit()
