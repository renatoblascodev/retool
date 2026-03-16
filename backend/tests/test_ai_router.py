"""Tests for the AI router (POST /api/ai/generate-app and /api/ai/suggest-query)."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.main import app
from app.models import DataSource, User

# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_USER = User(
    id="user-ai",
    email="ai@example.com",
    password_hash="x",
    created_at=datetime(2026, 1, 1),
)

FAKE_DS_ID = str(uuid4())


def _make_datasource(ds_type: str = "sql") -> DataSource:
    ds = DataSource(
        id=FAKE_DS_ID,
        owner_id=FAKE_USER.id,
        name="my_db",
        base_url="postgresql://localhost/mydb",
        auth_type="none",
        ds_type=ds_type,
    )
    ds.created_at = datetime(2026, 1, 1)
    ds.updated_at = datetime(2026, 1, 1)
    return ds


VALID_GENERATE_RESPONSE = {
    "layout": [
        {
            "i": "users_table",
            "type": "Table",
            "x": 0,
            "y": 0,
            "w": 12,
            "h": 8,
            "props": {"title": "Users", "queryName": "listUsers"},
        }
    ],
    "suggested_queries": [
        {"name": "listUsers", "query": "SELECT * FROM users"}
    ],
    "explanation": "A table showing all users.",
}

VALID_SUGGEST_RESPONSE = {
    "query": "SELECT * FROM users WHERE active = true",
    "explanation": "Returns all active users from the database.",
}


class _FakeSession:
    def __init__(self, scalar_result=None) -> None:
        self._scalar_result = scalar_result

    async def scalar(self, _stmt):
        return self._scalar_result

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def _override_auth(user: User = FAKE_USER):
    def _dep():
        return user
    return _dep


def _override_db(session: _FakeSession):
    async def _dep():
        yield session
    return _dep


def _patch_service(module_fn: str, return_value: dict):
    return patch(
        f"app.ai.service.{module_fn}",
        new_callable=AsyncMock,
        return_value=return_value,
    )


# ── Tests: generate-app ───────────────────────────────────────────────────────


def test_generate_app_no_datasource():
    """Should call generate_app service and return layout."""
    with _patch_service("generate_app", VALID_GENERATE_RESPONSE):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession())
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/ai/generate-app",
            json={"prompt": "Create a user management dashboard"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "layout" in data
    assert len(data["layout"]) == 1
    assert data["layout"][0]["type"] == "Table"
    assert data["explanation"] == "A table showing all users."


def test_generate_app_with_valid_datasource():
    """Should pass datasource info to service when datasource_id provided."""
    ds = _make_datasource("sql")
    with _patch_service("generate_app", VALID_GENERATE_RESPONSE) as mock_svc:
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession(scalar_result=ds))
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/ai/generate-app",
            json={"prompt": "User list", "datasource_id": FAKE_DS_ID},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    # service was called with datasource info string
    call_args = mock_svc.call_args
    assert "my_db" in call_args[0][1] or "my_db" in str(call_args)


def test_generate_app_datasource_not_found():
    """Should return 404 when datasource_id doesn't belong to user."""
    with _patch_service("generate_app", VALID_GENERATE_RESPONSE):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession(scalar_result=None))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/ai/generate-app",
            json={"prompt": "Some app", "datasource_id": str(uuid4())},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_generate_app_prompt_too_short():
    """Pydantic validation: prompt must be >= 3 chars."""
    app.dependency_overrides[get_current_user] = _override_auth()
    app.dependency_overrides[get_db_session] = _override_db(_FakeSession())
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/ai/generate-app", json={"prompt": "hi"})
    app.dependency_overrides.clear()
    assert resp.status_code == 422


def test_generate_app_timeout():
    """Should return 503 when LLM call times out."""
    with patch(
        "app.ai.service.generate_app",
        new_callable=AsyncMock,
        side_effect=asyncio.TimeoutError,
    ):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/ai/generate-app",
            json={"prompt": "create a dashboard"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 503
    assert "timed out" in resp.json()["detail"].lower()


def test_generate_app_invalid_schema_from_llm():
    """Should return 502 when LLM returns unexpected structure."""
    with patch(
        "app.ai.service.generate_app",
        new_callable=AsyncMock,
        side_effect=ValueError("LLM returned invalid JSON"),
    ):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession())
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/ai/generate-app",
            json={"prompt": "create a dashboard"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 502


def test_generate_app_unauthenticated():
    """Should return 401/403 when no auth provided."""
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/ai/generate-app",
        json={"prompt": "create a dashboard"},
    )
    assert resp.status_code in (401, 403, 422)


def test_generate_app_response_has_suggested_queries():
    """Response should include suggested_queries list."""
    with _patch_service("generate_app", VALID_GENERATE_RESPONSE):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession())
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/ai/generate-app",
            json={"prompt": "Show me a list of all customers"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["suggested_queries"], list)
    assert data["suggested_queries"][0]["name"] == "listUsers"


# ── Tests: suggest-query ──────────────────────────────────────────────────────


def test_suggest_query_sql():
    """Should return a SQL query suggestion."""
    ds = _make_datasource("sql")
    with _patch_service("suggest_query", VALID_SUGGEST_RESPONSE):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession(scalar_result=ds))
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/ai/suggest-query",
            json={"datasource_id": FAKE_DS_ID, "goal": "list all active users"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "explanation" in data


def test_suggest_query_rest():
    """Should work for REST datasources."""
    ds = _make_datasource("rest")
    rest_response = {"query": "GET /users?active=true", "explanation": "Lists active users via REST."}
    with _patch_service("suggest_query", rest_response):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession(scalar_result=ds))
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/ai/suggest-query",
            json={"datasource_id": FAKE_DS_ID, "goal": "list active users"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200


def test_suggest_query_graphql():
    """Should work for GraphQL datasources."""
    ds = _make_datasource("graphql")
    gql_response = {
        "query": "query ListUsers { users { id name email } }",
        "explanation": "GraphQL query to list users.",
    }
    with _patch_service("suggest_query", gql_response):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession(scalar_result=ds))
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/ai/suggest-query",
            json={"datasource_id": FAKE_DS_ID, "goal": "fetch all users"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 200


def test_suggest_query_goal_too_short():
    """Pydantic validation: goal must be >= 3 chars."""
    app.dependency_overrides[get_current_user] = _override_auth()
    app.dependency_overrides[get_db_session] = _override_db(_FakeSession())
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/ai/suggest-query",
        json={"datasource_id": FAKE_DS_ID, "goal": "hi"},
    )
    app.dependency_overrides.clear()
    assert resp.status_code == 422


def test_suggest_query_datasource_not_found():
    """Should return 404 when datasource doesn't belong to user."""
    with _patch_service("suggest_query", VALID_SUGGEST_RESPONSE):
        app.dependency_overrides[get_current_user] = _override_auth()
        app.dependency_overrides[get_db_session] = _override_db(_FakeSession(scalar_result=None))
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/api/ai/suggest-query",
            json={"datasource_id": str(uuid4()), "goal": "list all users"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_suggest_query_unauthenticated():
    """Should return 401 when no auth provided."""
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/ai/suggest-query",
        json={"datasource_id": FAKE_DS_ID, "goal": "list users"},
    )
    assert resp.status_code in (401, 403, 422)
