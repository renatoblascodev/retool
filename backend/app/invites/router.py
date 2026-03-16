"""Router for invite endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.invites.schemas import (
    AcceptInviteRequest,
    AcceptInviteResponse,
    InviteCreateRequest,
    InviteInfoResponse,
    InviteResponse,
)
from app.invites.service import send_invite_email
from app.models import AppInvite, AppMember, ToolApp, User
from app.permissions.dependencies import require_role
from app.config import settings

router = APIRouter(tags=["invites"])

_INVITE_TTL_DAYS = 7


# ---------------------------------------------------------------------------
# POST /apps/{app_id}/invites  — owner only
# ---------------------------------------------------------------------------

@router.post(
    "/apps/{app_id}/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    app_id: str,
    body: InviteCreateRequest,
    _: AppMember = Depends(require_role("owner")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> InviteResponse:
    if body.role not in ("editor", "viewer"):
        raise HTTPException(status_code=400, detail="role must be 'editor' or 'viewer'")

    app = await db.get(ToolApp, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="App not found")

    # Idempotent: reuse an existing pending invite for same email+role
    existing = await db.scalar(
        select(AppInvite).where(
            AppInvite.app_id == app_id,
            AppInvite.email == body.email,
            AppInvite.role == body.role,
            AppInvite.accepted_at.is_(None),
        )
    )
    if existing:
        invite = existing
    else:
        invite = AppInvite(
            id=str(uuid4()),
            app_id=app_id,
            email=body.email,
            role=body.role,
            token=str(uuid4()),
            expires_at=datetime.now(tz=timezone.utc) + timedelta(days=_INVITE_TTL_DAYS),
            created_by=current_user.id,
        )
        db.add(invite)
        await db.commit()
        await db.refresh(invite)

    accept_link = f"{settings.frontend_url}/invites/accept?token={invite.token}"
    send_invite_email(
        to_email=invite.email,
        app_name=app.name,
        role=invite.role,
        inviter_name=current_user.email,
        accept_link=accept_link,
    )

    return InviteResponse(
        id=invite.id,
        app_id=invite.app_id,
        email=invite.email,
        role=invite.role,
        token=invite.token,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        created_at=invite.created_at,
    )


# ---------------------------------------------------------------------------
# GET /invites/accept?token=...  — public
# ---------------------------------------------------------------------------

@router.get("/invites/accept", response_model=InviteInfoResponse)
async def get_invite_info(
    token: str,
    db: AsyncSession = Depends(get_db_session),
) -> InviteInfoResponse:
    invite = await _get_valid_invite(token, db)
    app = await db.get(ToolApp, invite.app_id)
    inviter_name: str | None = None
    if invite.created_by:
        inviter = await db.get(User, invite.created_by)
        inviter_name = inviter.email if inviter else None
    return InviteInfoResponse(
        token=invite.token,
        app_id=invite.app_id,
        app_name=app.name if app else "",
        role=invite.role,
        email=invite.email,
        inviter_name=inviter_name,
    )


# ---------------------------------------------------------------------------
# POST /invites/accept  — authenticated
# ---------------------------------------------------------------------------

@router.post("/invites/accept", response_model=AcceptInviteResponse)
async def accept_invite(
    body: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AcceptInviteResponse:
    invite = await _get_valid_invite(body.token, db)

    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=403,
            detail="This invite was sent to a different email address.",
        )

    # Check if already a member
    existing_member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == invite.app_id,
            AppMember.user_id == current_user.id,
        )
    )
    if not existing_member:
        member = AppMember(
            app_id=invite.app_id,
            user_id=current_user.id,
            role=invite.role,
        )
        db.add(member)

    invite.accepted_at = datetime.now(tz=timezone.utc)
    await db.commit()

    return AcceptInviteResponse(app_id=invite.app_id)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _get_valid_invite(token: str, db: AsyncSession) -> AppInvite:
    invite = await db.scalar(select(AppInvite).where(AppInvite.token == token))
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found or expired.")
    if invite.accepted_at is not None:
        raise HTTPException(status_code=410, detail="Invite already accepted.")
    if invite.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=404, detail="Invite not found or expired.")
    return invite
