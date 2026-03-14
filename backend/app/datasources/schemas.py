from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DataSourceCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    base_url: str = Field(min_length=8, max_length=1000)
    auth_type: str = Field(default="none", pattern="^(none|bearer|basic)$")
    auth_config: dict = Field(default_factory=dict)


class DataSourceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    base_url: str | None = Field(default=None, min_length=8, max_length=1000)
    auth_type: str | None = Field(default=None, pattern="^(none|bearer|basic)$")
    auth_config: dict | None = None


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    base_url: str
    auth_type: str
    has_auth_config: bool
    created_at: datetime
    updated_at: datetime
