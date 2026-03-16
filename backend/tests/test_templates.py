"""Tests for AppTemplate catalog (Sprint 6 — TASK 3 & 8).

Tests GET /api/templates/catalog and POST /api/apps with template_id.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import AppMember, AppTemplate, ToolApp, User

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_USER = User(
    id="user-tmpl-sprint6",
    email="tmpluser@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

CRUD_LAYOUT = {
    "widgets": [
        {"id": "t1", "type": "Table", "x": 0, "y": 0, "w": 12, "h": 8,
         "props": {"data": "{{query1.data}}"}},
    ]
}


def _make_template(
    name: str = "User Management",
    category: str = "crud",
    is_active: bool = True,
    layout: dict | None = None,
) -> AppTemplate:
    t = AppTemplate(
        id=str(uuid4()),
        name=name,
        description="A sample template",
        category=category,
        thumbnail=None,
        layout_json=layout or CRUD_LAYOUT,
        is_active=is_active,
    )
    t.created_at = datetime(2026, 1, 1)
    return t


def _make_app_obj(app_id: str = "app-tmpl-001") -> ToolApp:
    a = ToolApp(id=app_id, name="My App", owner_id=FAKE_USER.id)
    a.created_at = datetime(2026, 1, 1)
    a.updated_at = datetime(2026, 1, 1)
    a.is_published = False
    a.published_at = None
    a.slug = None
    return a


def _make_owner_member(app_id: str = "app-tmpl-001") -> AppMember:
    m = AppMember(app_id=app_id, user_id=FAKE_USER.id, role="owner")
    m.joined_at = datetime(2026, 1, 1)
    return m


# ---------------------------------------------------------------------------
# Fake DB session
# ---------------------------------------------------------------------------


class _FakeScalarsResult:
    def __init__(self, items: list) -> None:
        self._items = items

    def __iter__(self):
        return iter(self._items)


class _FakeSession:
    def __init__(
        self,
        scalar_queue: list | None = None,
        scalars_result: list | None = None,
        get_queue: list | None = None,
    ) -> None:
        self._scalar_queue: list = list(scalar_queue or [])
        self._scalars_result: list = list(scalars_result or [])
        self._get_queue: list = list(get_queue or [])
        self.added: list = []
        self.committed = False
        self.flushed = False

    async def scalars(self, _statement) -> _FakeScalarsResult:
        return _FakeScalarsResult(self._scalars_result)

    async def scalar(self, _statement):
        return self._scalar_queue.pop(0) if self._scalar_queue else None

    async def get(self, _model, _pk):
        return self._get_queue.pop(0) if self._get_queue else None

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushed = True

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj) -> None:
        if not getattr(obj, "id", None):
            obj.id = str(uuid4())
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime(2026, 1, 1)
        if not getattr(obj, "updated_at", None):
            obj.updated_at = datetime(2026, 1, 1)


def _make_client(fake_session: _FakeSession, user: User = FAKE_USER) -> TestClient:
    async def override_db():
        yield fake_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def _cleanup() -> None:
    app.dependency_overrides.pop(get_db_session, None)
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# GET /api/templates/catalog — public, no auth
# ---------------------------------------------------------------------------


class ListTemplatesTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_list_templates_empty(self) -> None:
        """Returns empty list when no active templates exist."""
        session = _FakeSession(scalars_result=[])
        client = _make_client(session)
        resp = client.get("/api/templates/catalog")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_list_templates_returns_active_only(self) -> None:
        """Inactive templates are not returned."""
        active = _make_template(name="Active", is_active=True)
        # Fake DB already filters is_active=True in the query; we simulate this
        # by only putting the active one in scalars_result.
        session = _FakeSession(scalars_result=[active])
        client = _make_client(session)
        resp = client.get("/api/templates/catalog")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Active")

    def test_list_templates_returns_multiple(self) -> None:
        """Multiple active templates are returned."""
        t1 = _make_template(name="CRUD", category="crud")
        t2 = _make_template(name="KPI Dashboard", category="dashboard")
        session = _FakeSession(scalars_result=[t1, t2])
        client = _make_client(session)
        resp = client.get("/api/templates/catalog")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_list_templates_public(self) -> None:
        """Endpoint works without Authorization header."""
        _cleanup()  # remove overrides so no auth is set
        session = _FakeSession(scalars_result=[_make_template()])

        async def override_db():
            yield session

        app.dependency_overrides[get_db_session] = override_db
        # NO get_current_user override — endpoint should be public
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/templates/catalog")
        self.assertEqual(resp.status_code, 200)
        _cleanup()

    def test_list_templates_response_fields(self) -> None:
        """Response includes required fields from AppTemplateResponse."""
        t = _make_template(layout=CRUD_LAYOUT)
        session = _FakeSession(scalars_result=[t])
        client = _make_client(session)
        resp = client.get("/api/templates/catalog")
        self.assertEqual(resp.status_code, 200)
        item = resp.json()[0]
        for field in ("id", "name", "category", "layout_json"):
            self.assertIn(field, item, f"Missing field: {field}")
        self.assertIsInstance(item["layout_json"], dict)


# ---------------------------------------------------------------------------
# POST /api/apps with template_id
# ---------------------------------------------------------------------------


class CreateAppWithTemplateTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_create_app_no_template(self) -> None:
        """Create app normally without template_id — no page created."""
        session = _FakeSession(
            scalar_queue=[_make_owner_member()],
        )
        client = _make_client(session)
        resp = client.post("/api/apps", json={"name": "My App"})
        self.assertEqual(resp.status_code, 201)
        # Only the ToolApp and AppMember objects should be added
        types_added = [type(o).__name__ for o in session.added]
        self.assertIn("ToolApp", types_added)
        self.assertIn("AppMember", types_added)
        self.assertNotIn("Page", types_added)

    def test_create_app_with_template(self) -> None:
        """When template_id provided, a Home page is created with template layout_json."""
        tmpl = _make_template(layout=CRUD_LAYOUT)
        session = _FakeSession(
            get_queue=[tmpl],
        )
        client = _make_client(session)
        resp = client.post(
            "/api/apps", json={"name": "My App", "template_id": tmpl.id}
        )
        self.assertEqual(resp.status_code, 201)
        types_added = [type(o).__name__ for o in session.added]
        self.assertIn("Page", types_added)
        # The page should have the template layout
        page = next(o for o in session.added if type(o).__name__ == "Page")
        self.assertEqual(page.layout_json, CRUD_LAYOUT)

    def test_create_app_invalid_template(self) -> None:
        """Non-existent template_id returns 400."""
        session = _FakeSession(
            get_queue=[None],  # template not found
        )
        client = _make_client(session)
        resp = client.post(
            "/api/apps", json={"name": "My App", "template_id": "non-existent"}
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_app_inactive_template(self) -> None:
        """Inactive template returns 400."""
        inactive = _make_template(is_active=False)
        session = _FakeSession(
            get_queue=[inactive],
        )
        client = _make_client(session)
        resp = client.post(
            "/api/apps", json={"name": "My App", "template_id": inactive.id}
        )
        self.assertEqual(resp.status_code, 400)

    def test_template_layout_is_deep_copy(self) -> None:
        """The page's layout_json is a deep copy — modifying it doesn't affect the template."""
        original_layout = {"widgets": [{"id": "w1", "type": "Table"}]}
        tmpl = _make_template(layout=original_layout)
        session = _FakeSession(get_queue=[tmpl])
        client = _make_client(session)
        resp = client.post(
            "/api/apps", json={"name": "Clone Test", "template_id": tmpl.id}
        )
        self.assertEqual(resp.status_code, 201)
        page = next(o for o in session.added if type(o).__name__ == "Page")
        # Mutate the page layout
        page.layout_json["widgets"].append({"id": "w99", "type": "Button"})
        # Original template layout must be untouched
        self.assertEqual(len(tmpl.layout_json["widgets"]), 1)
