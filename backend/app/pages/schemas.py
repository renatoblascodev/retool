from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PageCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=1, max_length=120)
    layout_json: dict = Field(default_factory=dict)


class PageUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    layout_json: dict | None = None


class PageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    app_id: str
    name: str
    slug: str
    layout_json: dict
    created_at: datetime
    updated_at: datetime
