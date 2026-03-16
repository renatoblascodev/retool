"""Integration tests for the datasource router using FastAPI TestClient.

Dependencies are overridden to avoid needing a live PostgreSQL instance:
  - ``get_current_user`` → fixed test user
  - ``get_db_session`` → in-memory fake async session
"""
from __future__ import annotations

import unittest
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import DataSource, User

# ── Shared fixtures ──────────────────────────────────────────────────────────

FAKE_USER = User(
    id="user-1",
    email="test@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)


def _make_datasource(
    *,
    ds_id: str | None = None,
    owner_id: str = "user-1",
    name: str = "Test API",
    base_url: str = "https://api.test",
    auth_type: str = "none",
    auth_config: dict | None = None,
) -> DataSource:
    ds = DataSource(
        owner_id=owner_id,
        name=name,
        base_url=base_url,
        auth_type=auth_type,
        auth_config=auth_config or {},
    )
    ds.id = ds_id or str(uuid4())
    ds.created_at = datetime(2026, 1, 1)
    ds.updated_at = datetime(2026, 1, 1)
    return ds


class _FakeScalarsResult:
    """Minimal stand-in for SQLAlchemy's ScalarResult."""

    def __init__(self, items: list) -> None:
        self._items = items

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._items)


class _FakeSession:
    """Async session that stores objects in memory.

    The ``scalars`` / ``scalar`` method ignores the SQLAlchemy statement and
    returns whatever was pre-loaded via the constructor.  This is intentional:
    tests verify HTTP-level behaviour, not query construction.
    """

    def __init__(
        self,
        scalars_result: list | None = None,
        scalar_result: object = None,
    ) -> None:
        self._scalars_result: list = scalars_result or []
        self._scalar_result = scalar_result
        self.added: list = []
        self.deleted: list = []
        self.committed = False

    async def scalars(self, _statement) -> _FakeScalarsResult:  # type: ignore[no-untyped-def]
        return _FakeScalarsResult(self._scalars_result)

    async def scalar(self, _statement) -> object:  # type: ignore[no-untyped-def]
        return self._scalar_result

    def add(self, obj) -> None:  # type: ignore[no-untyped-def]
        self.added.append(obj)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj) -> None:  # type: ignore[no-untyped-def]
        """Simulate DB refresh: assign defaults that would normally be DB-set."""
        if not getattr(obj, "id", None):
            obj.id = str(uuid4())
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime(2026, 1, 1)
        if not getattr(obj, "updated_at", None):
            obj.updated_at = datetime(2026, 1, 1)

    async def delete(self, obj) -> None:  # type: ignore[no-untyped-def]
        self.deleted.append(obj)


def _make_client(fake_session: _FakeSession) -> TestClient:
    """Return a TestClient with both auth and DB dependencies overridden."""

    async def override_db():  # type: ignore[no-untyped-def]
        yield fake_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER

    client = TestClient(app, raise_server_exceptions=True)
    return client


def _cleanup() -> None:
    app.dependency_overrides.pop(get_db_session, None)
    app.dependency_overrides.pop(get_current_user, None)


# ── Test cases ────────────────────────────────────────────────────────────────


class ListDatasourcesTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_returns_empty_list_when_no_datasources(self) -> None:
        client = _make_client(_FakeSession(scalars_result=[]))
        response = client.get("/api/datasources")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_returns_datasource_list(self) -> None:
        ds = _make_datasource(ds_id="ds-1", name="Orders API")
        client = _make_client(_FakeSession(scalars_result=[ds]))
        response = client.get("/api/datasources")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "ds-1")
        self.assertEqual(data[0]["name"], "Orders API")
        self.assertNotIn("auth_config", data[0])  # credentials never exposed

    def test_datasource_response_shape(self) -> None:
        ds = _make_datasource(ds_id="ds-2", auth_type="bearer", auth_config={"_encrypted": True, "ciphertext": "abc"})
        client = _make_client(_FakeSession(scalars_result=[ds]))
        response = client.get("/api/datasources")
        self.assertEqual(response.status_code, 200)
        item = response.json()[0]
        self.assertIn("id", item)
        self.assertIn("name", item)
        self.assertIn("base_url", item)
        self.assertIn("auth_type", item)
        self.assertIn("has_auth_config", item)
        self.assertTrue(item["has_auth_config"])
        # Raw auth credentials must never appear in the response.
        self.assertNotIn("auth_config", item)


class CreateDatasourceTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_create_minimal_datasource(self) -> None:
        session = _FakeSession()
        client = _make_client(session)
        payload = {
            "name": "Public API",
            "base_url": "https://public.example.test",
            "auth_type": "none",
            "auth_config": {},
        }
        response = client.post("/api/datasources", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Public API")
        self.assertEqual(data["base_url"], "https://public.example.test")
        self.assertEqual(data["auth_type"], "none")
        self.assertFalse(data["has_auth_config"])
        self.assertTrue(session.committed)
        self.assertEqual(len(session.added), 1)

    def test_create_bearer_datasource_credentials_not_exposed(self) -> None:
        """Bearer token must be encrypted before storage; response must exclude it."""
        session = _FakeSession()
        client = _make_client(session)
        payload = {
            "name": "Secure API",
            "base_url": "https://secure.example.test",
            "auth_type": "bearer",
            "auth_config": {"token": "super-secret-token"},
        }
        response = client.post("/api/datasources", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["auth_type"], "bearer")
        self.assertTrue(data["has_auth_config"])
        # The raw token must NOT appear in the response.
        self.assertNotIn("auth_config", data)
        self.assertNotIn("super-secret-token", response.text)

        # Verify persisted object has encrypted payload (not plain token).
        stored: DataSource = session.added[0]
        raw_config = stored.auth_config
        self.assertNotEqual(raw_config.get("token"), "super-secret-token")
        self.assertTrue(raw_config.get("_encrypted"))

    def test_create_basic_datasource(self) -> None:
        session = _FakeSession()
        client = _make_client(session)
        payload = {
            "name": "Internal API",
            "base_url": "https://internal.example.test",
            "auth_type": "basic",
            "auth_config": {"username": "admin", "password": "secret"},
        }
        response = client.post("/api/datasources", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["auth_type"], "basic")
        self.assertTrue(data["has_auth_config"])
        self.assertNotIn("secret", response.text)


class GetDatasourceTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_get_owned_datasource(self) -> None:
        ds = _make_datasource(ds_id="ds-10", name="My API")
        session = _FakeSession(scalar_result=ds)
        client = _make_client(session)
        response = client.get("/api/datasources/ds-10")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "ds-10")
        self.assertEqual(response.json()["name"], "My API")

    def test_get_returns_404_when_not_found(self) -> None:
        session = _FakeSession(scalar_result=None)
        client = _make_client(session)
        response = client.get("/api/datasources/missing-id")
        self.assertEqual(response.status_code, 404)


class DeleteDatasourceTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_delete_owned_datasource_returns_204(self) -> None:
        ds = _make_datasource(ds_id="ds-20")
        session = _FakeSession(scalar_result=ds)
        client = _make_client(session)
        response = client.delete("/api/datasources/ds-20")
        self.assertEqual(response.status_code, 204)
        self.assertTrue(session.committed)
        self.assertIn(ds, session.deleted)

    def test_delete_returns_404_when_not_owned(self) -> None:
        session = _FakeSession(scalar_result=None)
        client = _make_client(session)
        response = client.delete("/api/datasources/not-mine")
        self.assertEqual(response.status_code, 404)


class UpdateDatasourceTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_patch_name_and_url(self) -> None:
        ds = _make_datasource(ds_id="ds-30", name="Old Name", base_url="https://old.test")
        session = _FakeSession(scalar_result=ds)
        client = _make_client(session)
        response = client.patch(
            "/api/datasources/ds-30",
            json={"name": "New Name", "base_url": "https://new.test"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "New Name")
        self.assertEqual(data["base_url"], "https://new.test")
        self.assertTrue(session.committed)

    def test_patch_returns_404_when_not_owned(self) -> None:
        session = _FakeSession(scalar_result=None)
        client = _make_client(session)
        response = client.patch("/api/datasources/missing", json={"name": "New Name"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
