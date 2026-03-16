"""CRUD router for app membership management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.members_schemas import (
    MemberInviteRequest,
    MemberResponse,
    MemberRoleUpdateRequest,
)
from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import AppMember, User
from app.permissions.dependencies import require_role

router = APIRouter(prefix="/apps/{app_id}/members", tags=["members"])


def _to_response(member: AppMember, email: str | None = None) -> MemberResponse:
    return MemberResponse(
        app_id=member.app_id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        user_email=email,
    )


@router.get("", response_model=list[MemberResponse])
async def list_members(
    app_id: str,
    _: AppMember = Depends(require_role("viewer")),
    db: AsyncSession = Depends(get_db_session),
) -> list[MemberResponse]:
    rows = await db.scalars(
        select(AppMember).where(AppMember.app_id == app_id)
    )
    members = list(rows)
    # Enrich with emails
    if members:
        user_ids = [m.user_id for m in members]
        users = await db.scalars(select(User).where(User.id.in_(user_ids)))
        email_map = {u.id: u.email for u in users}
    else:
        email_map = {}
    return [_to_response(m, email_map.get(m.user_id)) for m in members]


@router.get("/me/role", response_model=MemberResponse)
async def get_my_role(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MemberResponse:
    member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == current_user.id,
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    return _to_response(member, current_user.email)


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    app_id: str,
    payload: MemberInviteRequest,
    _: AppMember = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db_session),
) -> MemberResponse:
    # Resolve user by email
    invitee = await db.scalar(select(User).where(User.email == payload.email))
    if invitee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check for existing membership
    existing = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == invitee.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member",
        )

    member = AppMember(app_id=app_id, user_id=invitee.id, role=payload.role)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return _to_response(member, invitee.email)


@router.patch("/{user_id}", response_model=MemberResponse)
async def update_member_role(
    app_id: str,
    user_id: str,
    payload: MemberRoleUpdateRequest,
    acting: AppMember = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db_session),
) -> MemberResponse:
    if user_id == acting.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )
    member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == user_id,
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the role of the owner",
        )
    member.role = payload.role
    await db.commit()
    await db.refresh(member)
    # Fetch email for response
    user = await db.scalar(select(User).where(User.id == user_id))
    return _to_response(member, user.email if user else None)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_member(
    app_id: str,
    user_id: str,
    acting: AppMember = Depends(require_role("owner")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    if user_id == acting.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself as owner",
        )
    member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == user_id,
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await db.delete(member)
    await db.commit()
