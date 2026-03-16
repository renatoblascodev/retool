"""Tests for RBAC permission dependencies and role enforcement logic."""
from __future__ import annotations

import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app.models import AppMember, User
from app.permissions.dependencies import ROLE_RANK, require_role


# ── Helpers ───────────────────────────────────────────────────────────────────

FAKE_USER = User(
    id="user-1",
    email="owner@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

APP_ID = "app-00000000"


def _make_member(role: str, user_id: str = "user-1") -> AppMember:
    m = AppMember(app_id=APP_ID, user_id=user_id, role=role)
    m.joined_at = datetime(2026, 1, 1)
    return m


def _make_db(member: AppMember | None) -> MagicMock:
    db = MagicMock()
    db.scalar = AsyncMock(return_value=member)
    return db


# ── ROLE_RANK tests ───────────────────────────────────────────────────────────


class RoleRankTests(unittest.TestCase):
    def test_owner_outranks_editor(self) -> None:
        self.assertGreater(ROLE_RANK["owner"], ROLE_RANK["editor"])

    def test_editor_outranks_viewer(self) -> None:
        self.assertGreater(ROLE_RANK["editor"], ROLE_RANK["viewer"])

    def test_viewer_is_lowest(self) -> None:
        self.assertEqual(ROLE_RANK["viewer"], 0)

    def test_all_three_roles_present(self) -> None:
        self.assertIn("owner", ROLE_RANK)
        self.assertIn("editor", ROLE_RANK)
        self.assertIn("viewer", ROLE_RANK)


# ── require_role dependency tests ────────────────────────────────────────────


class RequireRoleDependencyTests(unittest.TestCase):
    """Test the require_role factory with mocked DB and auth."""

    def _run(self, coro):  # type: ignore[no-untyped-def]
        return asyncio.run(coro)

    def test_owner_passes_owner_requirement(self) -> None:
        dep = require_role("owner")
        db = _make_db(_make_member("owner"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        result = self._run(go())
        self.assertEqual(result.role, "owner")

    def test_editor_passes_viewer_requirement(self) -> None:
        dep = require_role("viewer")
        db = _make_db(_make_member("editor"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        result = self._run(go())
        self.assertEqual(result.role, "editor")

    def test_viewer_blocked_from_editor_requirement(self) -> None:
        dep = require_role("editor")
        db = _make_db(_make_member("viewer"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        with self.assertRaises(HTTPException) as ctx:
            self._run(go())
        self.assertEqual(ctx.exception.status_code, 403)

    def test_viewer_blocked_from_owner_requirement(self) -> None:
        dep = require_role("owner")
        db = _make_db(_make_member("viewer"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        with self.assertRaises(HTTPException) as ctx:
            self._run(go())
        self.assertEqual(ctx.exception.status_code, 403)

    def test_editor_blocked_from_owner_requirement(self) -> None:
        dep = require_role("owner")
        db = _make_db(_make_member("editor"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        with self.assertRaises(HTTPException) as ctx:
            self._run(go())
        self.assertEqual(ctx.exception.status_code, 403)

    def test_non_member_gets_404(self) -> None:
        dep = require_role("viewer")
        db = _make_db(None)  # no membership row

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        with self.assertRaises(HTTPException) as ctx:
            self._run(go())
        self.assertEqual(ctx.exception.status_code, 404)

    def test_owner_passes_editor_requirement(self) -> None:
        dep = require_role("editor")
        db = _make_db(_make_member("owner"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        result = self._run(go())
        self.assertEqual(result.role, "owner")

    def test_viewer_passes_viewer_requirement(self) -> None:
        dep = require_role("viewer")
        db = _make_db(_make_member("viewer"))

        async def go():  # type: ignore[no-untyped-def]
            return await dep(app_id=APP_ID, current_user=FAKE_USER, db=db)

        result = self._run(go())
        self.assertEqual(result.role, "viewer")


if __name__ == "__main__":
    unittest.main()
