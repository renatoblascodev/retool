from pydantic import BaseModel, Field


class QueryExecuteRequest(BaseModel):
    type: str = Field(default="rest")
    name: str | None = None
    datasource_id: str | None = None
    config: dict = Field(default_factory=dict)
    variables: dict = Field(default_factory=dict)
    transform_js: str | None = None


class QueryExecuteResponse(BaseModel):
    success: bool
    data: dict | list
    status_code: int | None = None
    meta: dict = Field(default_factory=dict)
