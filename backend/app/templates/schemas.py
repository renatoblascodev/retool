import json
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    description: str | None
    category: str
    is_public: bool = True


class AppFromTemplateRequest(BaseModel):
    template_slug: str
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class SaveAsTemplateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(default="general", max_length=60)


# ── Built-in template definitions ────────────────────────────────────────────

_CRUD_LAYOUT = json.dumps({
    "widgets": [
        {
            "id": "tbl-1",
            "type": "table",
            "x": 0, "y": 0, "w": 12, "h": 8,
            "props": {
                "dataBinding": "{{query1.data}}",
                "columns": [{"key": "id", "label": "ID"}, {"key": "name", "label": "Name"}],
            },
        }
    ],
    "queries": [
        {
            "id": "query1",
            "name": "query1",
            "type": "rest",
            "config": {"url": "/items", "method": "GET"},
            "runOnLoad": True,
        }
    ],
})

_KPI_LAYOUT = json.dumps({
    "widgets": [
        {"id": "chart-1", "type": "chart", "x": 0, "y": 0, "w": 12, "h": 6,
         "props": {"dataBinding": "{{metrics.data}}", "chartType": "bar", "xKey": "label", "yKey": "value"}},
    ],
    "queries": [
        {"id": "metrics", "name": "metrics", "type": "rest",
         "config": {"url": "/metrics", "method": "GET"}, "runOnLoad": True},
    ],
})

_FORM_LAYOUT = json.dumps({
    "widgets": [
        {"id": "inp-name", "type": "input", "x": 0, "y": 0, "w": 6, "h": 2,
         "props": {"label": "Name", "placeholder": "Enter name"}},
        {"id": "btn-submit", "type": "button", "x": 0, "y": 2, "w": 3, "h": 2,
         "props": {"label": "Submit", "onClick": "submitForm.trigger()"}},
    ],
    "queries": [
        {"id": "submitForm", "name": "submitForm", "type": "rest",
         "config": {"url": "/submit", "method": "POST"}, "runOnLoad": False},
    ],
})


SEED_TEMPLATES = [
    {
        "id": str(uuid4()),
        "slug": "crud-table",
        "name": "CRUD Table",
        "description": "Table with REST datasource for listing and managing records.",
        "category": "data",
        "layout_json": _CRUD_LAYOUT,
    },
    {
        "id": str(uuid4()),
        "slug": "kpi-dashboard",
        "name": "KPI Dashboard",
        "description": "Bar chart connected to a metrics endpoint.",
        "category": "analytics",
        "layout_json": _KPI_LAYOUT,
    },
    {
        "id": str(uuid4()),
        "slug": "form-submit",
        "name": "Form + Submit",
        "description": "Input fields with a POST submit action.",
        "category": "forms",
        "layout_json": _FORM_LAYOUT,
    },
]
