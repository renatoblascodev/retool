"""Tests for the GraphQL executor path in QueryService."""
from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi import HTTPException

from app.queries.schemas import QueryExecuteRequest
from app.queries.service import QueryService


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


def _make_datasource(url: str = "https://api.example.test/graphql") -> SimpleNamespace:
    return SimpleNamespace(
        id="ds-1",
        owner_id="user-1",
        base_url=url,
        auth_type="none",
        auth_config={},
        ds_type="graphql",
    )


def _make_db(datasource=None) -> MagicMock:
    db = MagicMock()
    db.scalar = AsyncMock(return_value=datasource)
    return db


def _mock_post_response(json_data: dict, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "https://api.example.test/graphql")
    return httpx.Response(status_code, request=request, json=json_data)


# ── Tests ─────────────────────────────────────────────────────────────────────


class GraphQLExecutorTests(unittest.TestCase):
    def test_executes_graphql_query_with_datasource(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            datasource_id="ds-1",
            config={"query": "{ users { id name } }", "variables": {}},
        )
        ds = _make_datasource()
        db = _make_db(ds)
        expected = {"data": {"users": [{"id": "1", "name": "Alice"}]}}

        async def go():  # type: ignore[no-untyped-def]
            with patch.object(
                httpx.AsyncClient,
                "post",
                new=AsyncMock(return_value=_mock_post_response(expected)),
            ):
                return await QueryService().execute(payload, "user-1", db)

        data, status, meta = _run(go())
        self.assertEqual(status, 200)
        self.assertEqual(data, expected)
        self.assertEqual(meta["mode"], "graphql")
        self.assertEqual(meta["datasource_id"], "ds-1")

    def test_executes_graphql_with_inline_url(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            config={"url": "https://api.example.test/graphql", "query": "{ ping }"},
        )
        db = MagicMock()
        expected = {"data": {"ping": "pong"}}

        async def go():  # type: ignore[no-untyped-def]
            with patch.object(
                httpx.AsyncClient,
                "post",
                new=AsyncMock(return_value=_mock_post_response(expected)),
            ):
                return await QueryService().execute(payload, "user-1", db)

        data, _, meta = _run(go())
        self.assertEqual(data, expected)
        self.assertEqual(meta["mode"], "graphql")

    def test_raises_on_missing_query(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            config={"url": "https://api.example.test/graphql"},
        )
        db = MagicMock()

        async def go():  # type: ignore[no-untyped-def]
            return await QueryService().execute(payload, "user-1", db)

        with self.assertRaises(HTTPException) as ctx:
            _run(go())
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("query", ctx.exception.detail.lower())

    def test_raises_on_missing_url_and_datasource(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            config={"query": "{ users { id } }"},
        )
        db = MagicMock()

        async def go():  # type: ignore[no-untyped-def]
            return await QueryService().execute(payload, "user-1", db)

        with self.assertRaises(HTTPException) as ctx:
            _run(go())
        self.assertEqual(ctx.exception.status_code, 400)

    def test_ssrf_blocked_for_localhost(self) -> None:
        from unittest.mock import patch as _patch

        from app.config import settings

        payload = QueryExecuteRequest(
            type="graphql",
            config={"url": "http://localhost:8080/graphql", "query": "{ ping }"},
        )
        db = MagicMock()

        async def go():  # type: ignore[no-untyped-def]
            return await QueryService().execute(payload, "user-1", db)

        # Force production mode so SSRF guard is active
        with _patch.object(settings, "environment", "production"):
            with self.assertRaises(HTTPException) as ctx:
                _run(go())
            self.assertIn(ctx.exception.status_code, {400, 422})

    def test_bearer_token_injected_from_datasource(self) -> None:
        from app.datasources.secrets import encrypt_auth_config

        auth_config = encrypt_auth_config({"token": "secret-token"})
        ds = SimpleNamespace(
            id="ds-2",
            owner_id="user-1",
            base_url="https://api.example.test/graphql",
            auth_type="bearer",
            auth_config=auth_config,
            ds_type="graphql",
        )
        db = _make_db(ds)
        payload = QueryExecuteRequest(
            type="graphql",
            datasource_id="ds-2",
            config={"query": "{ me { id } }"},
        )
        captured_headers: dict = {}

        async def fake_post(self, url, *, json, headers, **kwargs):  # type: ignore[no-untyped-def]
            captured_headers.update(headers)
            req = httpx.Request("POST", url)
            return httpx.Response(200, request=req, json={"data": {"me": {"id": "1"}}})

        async def go():  # type: ignore[no-untyped-def]
            with patch.object(httpx.AsyncClient, "post", new=fake_post):
                return await QueryService().execute(payload, "user-1", db)

        _run(go())
        self.assertIn("Authorization", captured_headers)
        self.assertTrue(captured_headers["Authorization"].startswith("Bearer "))

    def test_variables_passed_in_request_body(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            config={
                "url": "https://api.example.test/graphql",
                "query": "query GetUser($id: ID!) { user(id: $id) { name } }",
                "variables": {"id": "42"},
            },
        )
        db = MagicMock()
        captured_body: dict = {}

        async def fake_post(self, url, *, json, headers, **kwargs):  # type: ignore[no-untyped-def]
            captured_body.update(json)
            req = httpx.Request("POST", url)
            return httpx.Response(200, request=req, json={"data": {"user": {"name": "Bob"}}})

        async def go():  # type: ignore[no-untyped-def]
            with patch.object(httpx.AsyncClient, "post", new=fake_post):
                return await QueryService().execute(payload, "user-1", db)

        _run(go())
        self.assertEqual(captured_body.get("variables"), {"id": "42"})
        self.assertIn("GetUser", captured_body.get("query", ""))

    def test_non_json_response_falls_back_to_raw(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            config={"url": "https://api.example.test/graphql", "query": "{ ping }"},
        )
        db = MagicMock()

        async def fake_post(self, url, *, json, headers, **kwargs):  # type: ignore[no-untyped-def]
            req = httpx.Request("POST", url)
            return httpx.Response(200, request=req, content=b"not json at all")

        async def go():  # type: ignore[no-untyped-def]
            with patch.object(httpx.AsyncClient, "post", new=fake_post):
                return await QueryService().execute(payload, "user-1", db)

        data, status, _ = _run(go())
        self.assertEqual(status, 200)
        self.assertIn("raw", data)

    def test_datasource_not_found_returns_404(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            datasource_id="nonexistent",
            config={"query": "{ ping }"},
        )
        db = _make_db(None)  # scalar returns None

        async def go():  # type: ignore[no-untyped-def]
            return await QueryService().execute(payload, "user-1", db)

        with self.assertRaises(HTTPException) as ctx:
            _run(go())
        self.assertEqual(ctx.exception.status_code, 404)

    def test_extra_headers_merged_from_config(self) -> None:
        payload = QueryExecuteRequest(
            type="graphql",
            config={
                "url": "https://api.example.test/graphql",
                "query": "{ ping }",
                "headers": {"X-Tenant": "acme"},
            },
        )
        db = MagicMock()
        captured_headers: dict = {}

        async def fake_post(self, url, *, json, headers, **kwargs):  # type: ignore[no-untyped-def]
            captured_headers.update(headers)
            req = httpx.Request("POST", url)
            return httpx.Response(200, request=req, json={"data": {"ping": "ok"}})

        async def go():  # type: ignore[no-untyped-def]
            with patch.object(httpx.AsyncClient, "post", new=fake_post):
                return await QueryService().execute(payload, "user-1", db)

        _run(go())
        self.assertEqual(captured_headers.get("X-Tenant"), "acme")


if __name__ == "__main__":
    unittest.main()
