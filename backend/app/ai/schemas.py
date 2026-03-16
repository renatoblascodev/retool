from pydantic import BaseModel, Field


class WidgetLayout(BaseModel):
    i: str
    type: str
    x: int = 0
    y: int = 0
    w: int = 12
    h: int = 8
    props: dict = Field(default_factory=dict)


class SuggestedQuery(BaseModel):
    name: str
    query: str


class GenerateAppRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)
    datasource_id: str | None = None


class GenerateAppResponse(BaseModel):
    layout: list[WidgetLayout]
    suggested_queries: list[SuggestedQuery] = Field(default_factory=list)
    explanation: str


class SuggestQueryRequest(BaseModel):
    datasource_id: str
    goal: str = Field(..., min_length=3, max_length=1000)


class SuggestQueryResponse(BaseModel):
    query: str
    explanation: str
