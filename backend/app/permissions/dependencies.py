"""FastAPI dependencies for RBAC role enforcement."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import AppMember, User

# Numeric rank for comparison: higher number = more permissions.
ROLE_RANK: dict[str, int] = {
    "viewer": 0,
    "editor": 1,
    "owner": 2,
}


async def get_app_membership(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppMember:
    """Return the AppMember row for the current user in the given app.

    Raises 404 if the app does not exist or the user is not a member.
    """
    member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == current_user.id,
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return member


def require_role(min_role: str) -> Callable:
    """Return a FastAPI dependency that enforces a minimum role.

    Usage::

        @router.patch("/{app_id}")
        async def update(member: AppMember = Depends(require_role("editor"))):
            ...
    """

    async def _dep(
        app_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session),
    ) -> AppMember:
        member = await db.scalar(
            select(AppMember).where(
                AppMember.app_id == app_id,
                AppMember.user_id == current_user.id,
            )
        )
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="App not found",
            )
        if ROLE_RANK.get(member.role, -1) < ROLE_RANK.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{min_role}' or higher",
            )
        return member

    return _dep
