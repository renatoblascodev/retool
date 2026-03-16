"""Tests for invite endpoints (US-320).

Uses the project-standard sync TestClient + _FakeSession mock pattern.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import AppInvite, AppMember, ToolApp, User

# ---------------------------------------------------------------------------
# Constants / fixtures
# ---------------------------------------------------------------------------

APP_ID = "app-invites-test-001"
APP_NAME = "InviteTestApp"

OWNER = User(
    id="user-owner-inv",
    email="owner@invitetest.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)
EDITOR_USER = User(
    id="user-editor-inv",
    email="editor@invitetest.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)


def _make_app_obj() -> ToolApp:
    a = ToolApp(id=APP_ID, name=APP_NAME, owner_id=OWNER.id)
    a.created_at = datetime(2026, 1, 1)
    a.updated_at = datetime(2026, 1, 1)
    return a


def _make_owner_member() -> AppMember:
    m = AppMember(app_id=APP_ID, user_id=OWNER.id, role="owner")
    m.joined_at = datetime(2026, 1, 1)
    return m


def _make_invite(
    email: str = "invitee@invitetest.com",
    role: str = "editor",
    accepted: bool = False,
    expired: bool = False,
) -> AppInvite:
    inv = AppInvite(
        id=str(uuid4()),
        app_id=APP_ID,
        email=email,
        role=role,
        token=str(uuid4()),
        expires_at=datetime.now(tz=timezone.utc)
        + (timedelta(days=-1) if expired else timedelta(days=7)),
        created_by=OWNER.id,
    )
    inv.created_at = datetime(2026, 1, 1)
    inv.accepted_at = datetime(2026, 1, 1) if accepted else None
    return inv


# ---------------------------------------------------------------------------
# Fake DB session
# ---------------------------------------------------------------------------


class _FakeSession:
    def __init__(self, scalar_queue=None, get_queue=None):
        self._scalar_queue: list = list(scalar_queue or [])
        self._get_queue: list = list(get_queue or [])
        self.added: list = []
        self.committed = False

    async def scalar(self, _stmt):  # noqa: ANN001
        return self._scalar_queue.pop(0) if self._scalar_queue else None

    async def get(self, _model, _pk):  # noqa: ANN001
        return self._get_queue.pop(0) if self._get_queue else None

    def add(self, obj):  # noqa: ANN001
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):  # noqa: ANN001
        if not getattr(obj, "id", None):
            obj.id = str(uuid4())
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime(2026, 1, 1)


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
# POST /apps/{app_id}/invites
# ---------------------------------------------------------------------------


class CreateInviteTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_owner_creates_invite(self) -> None:
        """Owner can create an invite; no existing pending invite (first time)."""
        session = _FakeSession(
            scalar_queue=[_make_owner_member(), None],
            get_queue=[_make_app_obj()],
        )
        client = _make_client(session)

        with patch("app.invites.router.send_invite_email") as mock_send:
            r = client.post(
                f"/api/apps/{APP_ID}/invites",
                json={"email": "invitee@invitetest.com", "role": "editor"},
            )

        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["email"], "invitee@invitetest.com")
        self.assertEqual(data["role"], "editor")
        self.assertIn("token", data)
        mock_send.assert_called_once()

    def test_invalid_role_rejected(self) -> None:
        session = _FakeSession(scalar_queue=[_make_owner_member()])
        client = _make_client(session)

        r = client.post(
            f"/api/apps/{APP_ID}/invites",
            json={"email": "x@example.com", "role": "owner"},
        )
        self.assertEqual(r.status_code, 400)

    def test_non_owner_cannot_invite(self) -> None:
        editor_member = AppMember(app_id=APP_ID, user_id=EDITOR_USER.id, role="editor")
        editor_member.joined_at = datetime(2026, 1, 1)
        session = _FakeSession(scalar_queue=[editor_member])
        client = _make_client(session, acting_user=EDITOR_USER)

        r = client.post(
            f"/api/apps/{APP_ID}/invites",
            json={"email": "x@example.com", "role": "editor"},
        )
        self.assertEqual(r.status_code, 403)

    def test_unauthenticated_rejected(self) -> None:
        # HTTPBearer(auto_error=True) returns 403 when no Authorization header present
        _cleanup()
        client = TestClient(app, raise_server_exceptions=False)

        r = client.post(
            f"/api/apps/{APP_ID}/invites",
            json={"email": "x@example.com", "role": "editor"},
        )
        self.assertIn(r.status_code, (401, 403))

    def test_idempotent_reuses_existing_invite(self) -> None:
        """Duplicate invite for same email+role reuses existing token."""
        existing = _make_invite()
        session = _FakeSession(
            scalar_queue=[_make_owner_member(), existing],
            get_queue=[_make_app_obj()],
        )
        client = _make_client(session)

        with patch("app.invites.router.send_invite_email"):
            r = client.post(
                f"/api/apps/{APP_ID}/invites",
                json={"email": existing.email, "role": existing.role},
            )

        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["token"], existing.token)
        # Nothing new was added to the session
        self.assertEqual(len(session.added), 0)


# ---------------------------------------------------------------------------
# GET /invites/accept?token=...
# ---------------------------------------------------------------------------


class GetInviteInfoTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def _public_client(self, session: _FakeSession) -> TestClient:
        async def override_db():
            yield session

        app.dependency_overrides[get_db_session] = override_db
        app.dependency_overrides.pop(get_current_user, None)
        return TestClient(app, raise_server_exceptions=False)

    def test_valid_token_returns_info(self) -> None:
        invite = _make_invite()
        session = _FakeSession(
            scalar_queue=[invite],
            get_queue=[_make_app_obj(), OWNER],
        )
        client = self._public_client(session)

        r = client.get(f"/api/invites/accept?token={invite.token}")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["app_name"], APP_NAME)
        self.assertEqual(data["role"], "editor")

    def test_invalid_token_returns_404(self) -> None:
        session = _FakeSession(scalar_queue=[None])
        client = self._public_client(session)

        r = client.get(f"/api/invites/accept?token={uuid4()}")
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------------------
# POST /invites/accept
# ---------------------------------------------------------------------------


class AcceptInviteTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_valid_accept(self) -> None:
        invite = _make_invite(email=EDITOR_USER.email)
        session = _FakeSession(scalar_queue=[invite, None])
        client = _make_client(session, acting_user=EDITOR_USER)

        r = client.post("/api/invites/accept", json={"token": invite.token})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["app_id"], APP_ID)
        self.assertTrue(any(isinstance(o, AppMember) for o in session.added))

    def test_wrong_email_returns_403(self) -> None:
        invite = _make_invite(email="someone_else@test.com")
        session = _FakeSession(scalar_queue=[invite])
        client = _make_client(session, acting_user=EDITOR_USER)

        r = client.post("/api/invites/accept", json={"token": invite.token})
        self.assertEqual(r.status_code, 403)

    def test_already_accepted_returns_410(self) -> None:
        invite = _make_invite(email=EDITOR_USER.email, accepted=True)
        session = _FakeSession(scalar_queue=[invite])
        client = _make_client(session, acting_user=EDITOR_USER)

        r = client.post("/api/invites/accept", json={"token": invite.token})
        self.assertEqual(r.status_code, 410)

    def test_expired_invite_returns_404(self) -> None:
        invite = _make_invite(email=EDITOR_USER.email, expired=True)
        session = _FakeSession(scalar_queue=[invite])
        client = _make_client(session, acting_user=EDITOR_USER)

        r = client.post("/api/invites/accept", json={"token": invite.token})
        self.assertEqual(r.status_code, 404)

    def test_token_not_found_returns_404(self) -> None:
        session = _FakeSession(scalar_queue=[None])
        client = _make_client(session, acting_user=EDITOR_USER)

        r = client.post("/api/invites/accept", json={"token": str(uuid4())})
        self.assertEqual(r.status_code, 404)
