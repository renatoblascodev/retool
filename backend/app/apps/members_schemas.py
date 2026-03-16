from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberInviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="editor", pattern="^(editor|viewer)$")


class MemberRoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(editor|viewer)$")


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    app_id: str
    user_id: str
    role: str
    joined_at: datetime
    user_email: str | None = None
