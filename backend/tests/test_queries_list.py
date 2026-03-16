"""Tests for GET /api/apps/{app_id}/queries (Sprint 6 — TASK 5 & 8)."""
from __future__ import annotations

import unittest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import AppMember, Page, ToolApp, User

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

APP_ID = "app-queries-list-001"

OWNER = User(
    id="user-qlist-owner",
    email="qlistowner@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)
EDITOR = User(
    id="user-qlist-editor",
    email="qlisteditor@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)
VIEWER = User(
    id="user-qlist-viewer",
    email="qlistviewer@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

_SAMPLE_QUERIES = [
    {
        "id": "q1",
        "name": "listUsers",
        "type": "rest",
        "config": {"url": "/users", "method": "GET"},
        "runOnLoad": True,
    },
    {
        "id": "q2",
        "name": "createUser",
        "type": "rest",
        "config": {"url": "/users", "method": "POST"},
        "runOnLoad": False,
    },
]


def _make_app() -> ToolApp:
    a = ToolApp(id=APP_ID, name="Query Test App", owner_id=OWNER.id)
    a.created_at = datetime(2026, 1, 1)
    a.updated_at = datetime(2026, 1, 1)
    a.is_published = False
    a.published_at = None
    a.slug = None
    return a


def _make_member(user: User, role: str) -> AppMember:
    m = AppMember(app_id=APP_ID, user_id=user.id, role=role)
    m.joined_at = datetime(2026, 1, 1)
    return m


def _make_page(queries: list | None = None) -> Page:
    p = Page(
        id=str(uuid4()),
        app_id=APP_ID,
        name="Home",
        slug="home",
        layout_json={
            "widgets": [],
            "queries": queries if queries is not None else _SAMPLE_QUERIES,
        },
    )
    p.created_at = datetime(2026, 1, 1)
    p.updated_at = datetime(2026, 1, 1)
    return p


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
    ) -> None:
        self._scalar_queue: list = list(scalar_queue or [])
        self._scalars_result: list = list(scalars_result or [])

    async def scalar(self, _stmt):
        return self._scalar_queue.pop(0) if self._scalar_queue else None

    async def scalars(self, _stmt) -> _FakeScalarsResult:
        return _FakeScalarsResult(self._scalars_result)

    def add(self, obj) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, obj) -> None:
        pass


def _make_client(fake_session: _FakeSession, acting_user: User = OWNER) -> TestClient:
    async def override_db():
        yield fake_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: acting_user
    return TestClient(app, raise_server_exceptions=False)


def _cleanup() -> None:
    app.dependency_overrides.pop(get_db_session, None)
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# GET /api/apps/{app_id}/queries
# ---------------------------------------------------------------------------


class ListQueriesTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_list_queries_owner(self) -> None:
        """Owner can list all queries for the app."""
        session = _FakeSession(
            # _get_accessible_app: member check, then app lookup
            scalar_queue=[_make_member(OWNER, "owner"), _make_app()],
            scalars_result=[_make_page()],
        )
        client = _make_client(session)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "q1")
        self.assertEqual(data[0]["name"], "listUsers")
        self.assertTrue(data[0]["run_on_load"])
        self.assertFalse(data[1]["run_on_load"])

    def test_list_queries_editor(self) -> None:
        """Editor can list queries."""
        session = _FakeSession(
            scalar_queue=[_make_member(EDITOR, "editor"), _make_app()],
            scalars_result=[_make_page()],
        )
        client = _make_client(session, acting_user=EDITOR)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.json()), 0)

    def test_list_queries_viewer(self) -> None:
        """Viewer (any role) can list queries."""
        session = _FakeSession(
            scalar_queue=[_make_member(VIEWER, "viewer"), _make_app()],
            scalars_result=[_make_page()],
        )
        client = _make_client(session, acting_user=VIEWER)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertEqual(resp.status_code, 200)

    def test_list_queries_no_access(self) -> None:
        """User with no membership gets 404 from _get_accessible_app."""
        no_member_user = User(
            id="user-no-access",
            email="noaccess@example.com",
            password_hash="x",
            created_at=datetime(2026, 1, 1),
        )
        # No member row found, then no owned app found → 404
        session = _FakeSession(scalar_queue=[None, None])
        client = _make_client(session, acting_user=no_member_user)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertEqual(resp.status_code, 404)

    def test_list_queries_unauthenticated(self) -> None:
        """No auth token → 401 or 403 (HTTPBearer)."""
        _cleanup()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertIn(resp.status_code, (401, 403))

    def test_list_queries_empty(self) -> None:
        """App with no queries returns empty list."""
        page_no_queries = _make_page(queries=[])
        session = _FakeSession(
            scalar_queue=[_make_member(OWNER, "owner"), _make_app()],
            scalars_result=[page_no_queries],
        )
        client = _make_client(session)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_list_queries_multiple_pages(self) -> None:
        """Queries from multiple pages are aggregated."""
        page1 = _make_page(queries=[{"id": "q1", "name": "q1", "type": "rest", "config": {}}])
        page2 = _make_page(queries=[{"id": "q2", "name": "q2", "type": "sql", "config": {}}])
        session = _FakeSession(
            scalar_queue=[_make_member(OWNER, "owner"), _make_app()],
            scalars_result=[page1, page2],
        )
        client = _make_client(session)
        resp = client.get(f"/api/apps/{APP_ID}/queries")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
