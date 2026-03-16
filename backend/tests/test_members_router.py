"""Integration tests for the members router using FastAPI TestClient."""
from __future__ import annotations

import unittest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import AppMember, User

# ── Fixtures ──────────────────────────────────────────────────────────────────

OWNER = User(
    id="user-owner",
    email="owner@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

EDITOR = User(
    id="user-editor",
    email="editor@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

STRANGER = User(
    id="user-stranger",
    email="stranger@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

APP_ID = "app-fixed-id-0001"


def _make_member(user_id: str, role: str) -> AppMember:
    m = AppMember(app_id=APP_ID, user_id=user_id, role=role)
    m.joined_at = datetime(2026, 1, 1)
    return m


class _FakeScalarsResult:
    def __init__(self, items: list) -> None:
        self._items = items

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._items)


class _FakeSession:
    """Multi-call capable fake session for members router tests."""

    def __init__(
        self,
        scalar_queue: list | None = None,
        scalars_result: list | None = None,
        scalars_queue: list[list] | None = None,
    ) -> None:
        # scalar() calls are served from the queue in order
        self._scalar_queue: list = list(scalar_queue or [])
        self._scalars_result: list = scalars_result or []
        # scalars_queue: each call to scalars() pops the first list
        self._scalars_queue: list[list] = list(scalars_queue or [])
        self.added: list = []
        self.deleted: list = []
        self.committed = False

    async def scalars(self, _statement) -> _FakeScalarsResult:  # type: ignore[no-untyped-def]
        if self._scalars_queue:
            return _FakeScalarsResult(self._scalars_queue.pop(0))
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
        if not getattr(obj, "joined_at", None):
            obj.joined_at = datetime(2026, 1, 1)

    async def delete(self, obj) -> None:  # type: ignore[no-untyped-def]
        self.deleted.append(obj)


def _make_client(fake_session: _FakeSession, acting_user: User = OWNER) -> TestClient:
    async def override_db():  # type: ignore[no-untyped-def]
        yield fake_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: acting_user
    return TestClient(app, raise_server_exceptions=True)


def _cleanup() -> None:
    app.dependency_overrides.pop(get_db_session, None)
    app.dependency_overrides.pop(get_current_user, None)


# ── Tests ─────────────────────────────────────────────────────────────────────


class GetMyRoleTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_returns_role_for_member(self) -> None:
        owner_member = _make_member(OWNER.id, "owner")
        session = _FakeSession(scalar_queue=[owner_member])
        client = _make_client(session)
        resp = client.get(f"/api/apps/{APP_ID}/members/me/role")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["role"], "owner")

    def test_404_for_non_member(self) -> None:
        session = _FakeSession(scalar_queue=[None])
        client = _make_client(session)
        resp = client.get(f"/api/apps/{APP_ID}/members/me/role")
        self.assertEqual(resp.status_code, 404)


class ListMembersTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_owner_can_list_members(self) -> None:
        owner_member = _make_member(OWNER.id, "owner")
        editor_member = _make_member(EDITOR.id, "editor")
        # scalar_queue: require_role("viewer") membership check
        # scalars_queue: [members list, users list (for email enrichment)]
        session = _FakeSession(
            scalar_queue=[owner_member],
            scalars_queue=[[owner_member, editor_member], [OWNER, EDITOR]],
        )
        client = _make_client(session)
        resp = client.get(f"/api/apps/{APP_ID}/members")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_non_member_blocked(self) -> None:
        session = _FakeSession(scalar_queue=[None])
        client = _make_client(session, acting_user=STRANGER)
        resp = client.get(f"/api/apps/{APP_ID}/members")
        self.assertEqual(resp.status_code, 404)


class InviteMemberTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_owner_can_invite(self) -> None:
        owner_member = _make_member(OWNER.id, "owner")
        # scalar_queue: [require_role("owner") check, resolve invitee, existing check]
        session = _FakeSession(scalar_queue=[owner_member, EDITOR, None])
        client = _make_client(session)
        resp = client.post(
            f"/api/apps/{APP_ID}/members",
            json={"email": EDITOR.email, "role": "editor"},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["role"], "editor")
        self.assertTrue(session.committed)

    def test_non_owner_cannot_invite(self) -> None:
        editor_member = _make_member(EDITOR.id, "editor")
        session = _FakeSession(scalar_queue=[editor_member])
        client = _make_client(session, acting_user=EDITOR)
        resp = client.post(
            f"/api/apps/{APP_ID}/members",
            json={"email": "stranger@example.com", "role": "viewer"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_invite_unknown_user_returns_404(self) -> None:
        owner_member = _make_member(OWNER.id, "owner")
        # resolve invitee returns None → 404
        session = _FakeSession(scalar_queue=[owner_member, None])
        client = _make_client(session)
        resp = client.post(
            f"/api/apps/{APP_ID}/members",
            json={"email": "ghost@example.com", "role": "editor"},
        )
        self.assertEqual(resp.status_code, 404)


class RemoveMemberTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_owner_can_remove_editor(self) -> None:
        owner_member = _make_member(OWNER.id, "owner")
        editor_member = _make_member(EDITOR.id, "editor")
        session = _FakeSession(scalar_queue=[owner_member, editor_member])
        client = _make_client(session)
        resp = client.delete(f"/api/apps/{APP_ID}/members/{EDITOR.id}")
        self.assertEqual(resp.status_code, 204)
        self.assertIn(editor_member, session.deleted)

    def test_owner_cannot_remove_self(self) -> None:
        owner_member = _make_member(OWNER.id, "owner")
        session = _FakeSession(scalar_queue=[owner_member])
        client = _make_client(session)
        resp = client.delete(f"/api/apps/{APP_ID}/members/{OWNER.id}")
        self.assertEqual(resp.status_code, 400)

    def test_non_owner_cannot_remove_members(self) -> None:
        editor_member = _make_member(EDITOR.id, "editor")
        session = _FakeSession(scalar_queue=[editor_member])
        client = _make_client(session, acting_user=EDITOR)
        resp = client.delete(f"/api/apps/{APP_ID}/members/{OWNER.id}")
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
