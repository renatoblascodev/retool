"""Pydantic schemas for invite endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: str  # "editor" | "viewer"


class InviteInfoResponse(BaseModel):
    token: str
    app_id: str
    app_name: str
    role: str
    email: str
    inviter_name: str | None = None


class AcceptInviteRequest(BaseModel):
    token: str


class AcceptInviteResponse(BaseModel):
    app_id: str


class InviteResponse(BaseModel):
    id: str
    app_id: str
    email: str
    role: str
    token: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime
