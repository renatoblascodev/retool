"""Tests for publish/unpublish endpoints (Sprint 6 — TASK 4 & 8).

Covers:
  POST   /api/apps/{app_id}/publish
  DELETE /api/apps/{app_id}/publish
  GET    /api/r/{slug}
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import AppMember, Page, ToolApp, User

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

APP_ID = "app-publish-test-001"
APP_NAME = "My Published App"
APP_SLUG = "my-published-app"

OWNER = User(
    id="user-pub-owner",
    email="pubowner@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)
EDITOR = User(
    id="user-pub-editor",
    email="pubeditor@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)


def _make_app(
    slug: str | None = None,
    is_published: bool = False,
) -> ToolApp:
    a = ToolApp(id=APP_ID, name=APP_NAME, owner_id=OWNER.id)
    a.created_at = datetime(2026, 1, 1)
    a.updated_at = datetime(2026, 1, 1)
    a.is_published = is_published
    a.published_at = datetime(2026, 1, 1, tzinfo=timezone.utc) if is_published else None
    a.slug = slug
    return a


def _make_owner_member() -> AppMember:
    m = AppMember(app_id=APP_ID, user_id=OWNER.id, role="owner")
    m.joined_at = datetime(2026, 1, 1)
    return m


def _make_editor_member() -> AppMember:
    m = AppMember(app_id=APP_ID, user_id=EDITOR.id, role="editor")
    m.joined_at = datetime(2026, 1, 1)
    return m


def _make_page(layout: dict | None = None) -> Page:
    p = Page(
        id=str(uuid4()),
        app_id=APP_ID,
        name="Home",
        slug="home",
        layout_json=layout or {"widgets": [], "queries": []},
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
        get_queue: list | None = None,
        scalars_result: list | None = None,
    ) -> None:
        self._scalar_queue: list = list(scalar_queue or [])
        self._get_queue: list = list(get_queue or [])
        self._scalars_result: list = list(scalars_result or [])
        self.added: list = []
        self.committed = False

    async def scalar(self, _stmt):
        return self._scalar_queue.pop(0) if self._scalar_queue else None

    async def scalars(self, _stmt) -> _FakeScalarsResult:
        return _FakeScalarsResult(self._scalars_result)

    async def get(self, _model, _pk):
        return self._get_queue.pop(0) if self._get_queue else None

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj) -> None:
        if not getattr(obj, "id", None):
            obj.id = str(uuid4())


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
# POST /api/apps/{app_id}/publish
# ---------------------------------------------------------------------------


class PublishAppTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_publish_app_success(self) -> None:
        """Owner can publish an app; response has public_url and slug."""
        session = _FakeSession(
            scalar_queue=[_make_owner_member(), None],  # member check, slug uniqueness
            get_queue=[_make_app()],
        )
        client = _make_client(session)
        resp = client.post(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertIn("public_url", data)
        self.assertIn("slug", data)
        self.assertIn("published_at", data)

    def test_publish_generates_slug_from_name(self) -> None:
        """Slug is derived from the app name."""
        session = _FakeSession(
            scalar_queue=[_make_owner_member(), None],
            get_queue=[_make_app()],
        )
        client = _make_client(session)
        resp = client.post(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 200)
        slug = resp.json()["slug"]
        # Slug should be URL-safe (lowercase, hyphens, alphanumeric only)
        self.assertRegex(slug, r"^[a-z0-9-]+$")

    def test_publish_slug_collision(self) -> None:
        """When slug already taken, a suffixed slug (-2) is generated."""
        # First slug check returns an existing app (collision), second returns None
        collision_app = _make_app(slug="my-published-app")
        session = _FakeSession(
            scalar_queue=[_make_owner_member(), collision_app, None],
            get_queue=[_make_app()],
        )
        client = _make_client(session)
        resp = client.post(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["slug"].endswith("-2"))

    def test_publish_requires_owner(self) -> None:
        """Editor cannot publish an app — returns 403."""
        session = _FakeSession(
            scalar_queue=[_make_editor_member()],
        )
        client = _make_client(session, acting_user=EDITOR)
        resp = client.post(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 403)

    def test_publish_idempotent(self) -> None:
        """Publishing an already-published app succeeds without re-generating slug."""
        already_published = _make_app(slug=APP_SLUG, is_published=True)
        session = _FakeSession(
            scalar_queue=[_make_owner_member()],  # no slug-check since slug already set
            get_queue=[already_published],
        )
        client = _make_client(session)
        resp = client.post(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["slug"], APP_SLUG)


# ---------------------------------------------------------------------------
# DELETE /api/apps/{app_id}/publish
# ---------------------------------------------------------------------------


class UnpublishAppTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_unpublish_app(self) -> None:
        """DELETE /publish sets is_published=False."""
        published = _make_app(slug=APP_SLUG, is_published=True)
        session = _FakeSession(
            scalar_queue=[_make_owner_member()],
            get_queue=[published],
        )
        client = _make_client(session)
        resp = client.delete(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(published.is_published)
        self.assertTrue(session.committed)

    def test_unpublish_response(self) -> None:
        """DELETE /publish returns 204 with no body."""
        published = _make_app(slug=APP_SLUG, is_published=True)
        session = _FakeSession(
            scalar_queue=[_make_owner_member()],
            get_queue=[published],
        )
        client = _make_client(session)
        resp = client.delete(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

    def test_unpublish_requires_owner(self) -> None:
        """Editor cannot unpublish — returns 403."""
        session = _FakeSession(
            scalar_queue=[_make_editor_member()],
        )
        client = _make_client(session, acting_user=EDITOR)
        resp = client.delete(f"/api/apps/{APP_ID}/publish")
        self.assertEqual(resp.status_code, 403)


# ---------------------------------------------------------------------------
# GET /api/r/{slug} — public
# ---------------------------------------------------------------------------


class PublicAppTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_get_public_app_success(self) -> None:
        """GET /r/{slug} returns 200 with app snapshot for a published app."""
        published = _make_app(slug=APP_SLUG, is_published=True)
        page = _make_page()
        # Provide DB as override but NO auth override — endpoint is public
        _cleanup()
        session = _FakeSession(
            scalar_queue=[published],
            scalars_result=[page],
        )

        async def override_db():
            yield session

        app.dependency_overrides[get_db_session] = override_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/api/r/{APP_SLUG}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], APP_ID)
        self.assertEqual(data["name"], APP_NAME)
        self.assertIsInstance(data["pages"], list)
        _cleanup()

    def test_get_public_app_not_found(self) -> None:
        """GET /r/{slug} with unknown slug returns 404."""
        _cleanup()
        session = _FakeSession(scalar_queue=[None])

        async def override_db():
            yield session

        app.dependency_overrides[get_db_session] = override_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/r/does-not-exist")
        self.assertEqual(resp.status_code, 404)
        _cleanup()

    def test_get_unpublished_app(self) -> None:
        """GET /r/{slug} for an app that exists but is_published=False returns 404."""
        # The query filters is_published=True, so unpublished app → None
        _cleanup()
        session = _FakeSession(scalar_queue=[None])

        async def override_db():
            yield session

        app.dependency_overrides[get_db_session] = override_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/api/r/{APP_SLUG}")
        self.assertEqual(resp.status_code, 404)
        _cleanup()

    def test_get_public_app_no_auth_required(self) -> None:
        """GET /r/{slug} works without any Authorization header."""
        published = _make_app(slug=APP_SLUG, is_published=True)
        _cleanup()
        session = _FakeSession(
            scalar_queue=[published],
            scalars_result=[],
        )

        async def override_db():
            yield session

        app.dependency_overrides[get_db_session] = override_db
        # NO auth override
        client = TestClient(app, raise_server_exceptions=False)
        # Not passing any Authorization header
        resp = client.get(f"/api/r/{APP_SLUG}")
        self.assertEqual(resp.status_code, 200)
        _cleanup()
