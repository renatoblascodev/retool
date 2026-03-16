"""Integration tests for the templates router."""
from __future__ import annotations

import json
import unittest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import Template, User

# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_USER = User(
    id="user-1",
    email="owner@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)


def _make_template(slug: str = "crud-table", name: str = "CRUD Table") -> Template:
    t = Template(
        slug=slug,
        name=name,
        description="A test template",
        category="data",
        layout_json=json.dumps({"widgets": [], "queries": []}),
    )
    t.id = str(uuid4())
    t.created_at = datetime(2026, 1, 1)
    return t


class _FakeScalarsResult:
    def __init__(self, items: list) -> None:
        self._items = items

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._items)


class _FakeSession:
    def __init__(
        self,
        scalar_queue: list | None = None,
        scalars_result: list | None = None,
    ) -> None:
        self._scalar_queue: list = list(scalar_queue or [])
        self._scalars_result: list = scalars_result or []
        self.added: list = []
        self.committed = False

    async def scalars(self, _statement) -> _FakeScalarsResult:  # type: ignore[no-untyped-def]
        return _FakeScalarsResult(self._scalars_result)

    async def scalar(self, _statement) -> object:  # type: ignore[no-untyped-def]
        if self._scalar_queue:
            return self._scalar_queue.pop(0)
        return None

    def add(self, obj) -> None:  # type: ignore[no-untyped-def]
        self.added.append(obj)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj) -> None:  # type: ignore[no-untyped-def]
        if not getattr(obj, "id", None):
            obj.id = str(uuid4())
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime(2026, 1, 1)
        if not getattr(obj, "updated_at", None):
            obj.updated_at = datetime(2026, 1, 1)

    async def delete(self, obj) -> None:  # type: ignore[no-untyped-def]
        pass


def _make_client(fake_session: _FakeSession) -> TestClient:
    async def override_db():  # type: ignore[no-untyped-def]
        yield fake_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app, raise_server_exceptions=True)


def _cleanup() -> None:
    app.dependency_overrides.pop(get_db_session, None)
    app.dependency_overrides.pop(get_current_user, None)


# ── Test cases ────────────────────────────────────────────────────────────────


class ListTemplatesTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_returns_list_of_templates(self) -> None:
        t1 = _make_template("crud-table", "CRUD Table")
        t2 = _make_template("kpi-dashboard", "KPI Dashboard")
        # scalar_queue: first call checks for existing templates (returns one → no seed)
        session = _FakeSession(scalar_queue=[t1], scalars_result=[t1, t2])
        client = _make_client(session)
        resp = client.get("/api/templates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_template_response_has_required_fields(self) -> None:
        t = _make_template()
        session = _FakeSession(scalar_queue=[t], scalars_result=[t])
        client = _make_client(session)
        resp = client.get("/api/templates")
        self.assertEqual(resp.status_code, 200)
        item = resp.json()[0]
        self.assertIn("id", item)
        self.assertIn("slug", item)
        self.assertIn("name", item)
        self.assertIn("category", item)

    def test_empty_table_triggers_seed(self) -> None:
        # scalar returns None → seeds are inserted; scalars returns [] (empty after seed commit)
        session = _FakeSession(scalar_queue=[None], scalars_result=[])
        client = _make_client(session)
        resp = client.get("/api/templates")
        self.assertEqual(resp.status_code, 200)
        # Seeds were added to session
        self.assertTrue(len(session.added) > 0)


class CreateFromTemplateTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_creates_app_from_template(self) -> None:
        tmpl = _make_template("crud-table", "CRUD Table")
        # scalar_queue: [ensure_seeds check, template lookup]
        session = _FakeSession(scalar_queue=[tmpl, tmpl])
        client = _make_client(session)
        resp = client.post(
            "/api/templates/from-template",
            json={"template_slug": "crud-table", "name": "My App"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["name"], "My App")

    def test_invalid_slug_returns_404(self) -> None:
        tmpl = _make_template()
        session = _FakeSession(scalar_queue=[tmpl, None])  # template lookup returns None
        client = _make_client(session)
        resp = client.post(
            "/api/templates/from-template",
            json={"template_slug": "nonexistent", "name": "My App"},
        )
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
