from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataSourceCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    ds_type: str = Field(default="rest", pattern="^(rest|sql)$")
    # base_url required for REST; omitted for SQL (credentials go in auth_config)
    base_url: str = Field(default="", max_length=1000)
    auth_type: str = Field(default="none", pattern="^(none|bearer|basic)$")
    auth_config: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_rest_url(self) -> "DataSourceCreateRequest":
        if self.ds_type == "rest" and len(self.base_url) < 8:
            raise ValueError("base_url must be at least 8 characters for REST datasources")
        return self


class DataSourceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    ds_type: str | None = Field(default=None, pattern="^(rest|sql)$")
    base_url: str | None = Field(default=None, max_length=1000)
    auth_type: str | None = Field(default=None, pattern="^(none|bearer|basic)$")
    auth_config: dict | None = None


class DataSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    ds_type: str
    base_url: str
    auth_type: str
    has_auth_config: bool
    created_at: datetime
    updated_at: datetime
