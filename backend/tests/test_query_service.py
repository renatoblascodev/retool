from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.datasources.secrets import encrypt_auth_config
from app.queries.schemas import QueryExecuteRequest
from app.queries.service import QueryService


class QueryServiceTests(unittest.TestCase):
    def test_execute_returns_json_payload(self) -> None:
        payload = QueryExecuteRequest(
            type="rest",
            config={
                "base_url": "https://api.example.test",
                "url": "/customers",
                "method": "GET",
            },
        )

        async def run_test() -> None:
            service = QueryService()

            async def fake_request(
                self,
                method,
                url,
                **kwargs,
            ):  # type: ignore[no-untyped-def]
                self._captured = {
                    "method": method,
                    "url": url,
                    "kwargs": kwargs,
                }  # type: ignore[attr-defined]
                request = httpx.Request(method=method, url=url)
                return httpx.Response(
                    200,
                    request=request,
                    json={"rows": [{"id": 1, "name": "Alice"}]},
                )

            with patch.object(httpx.AsyncClient, "request", new=fake_request):
                data, status_code, meta = await service.execute(
                    payload,
                    "user-1",
                    db=None,
                )  # type: ignore[arg-type]

            self.assertEqual(status_code, 200)
            self.assertEqual(data, {"rows": [{"id": 1, "name": "Alice"}]})
            self.assertEqual(meta.get("mode"), "rest")
            request_info = meta.get("request", {})
            self.assertEqual(request_info.get("method"), "GET")
            self.assertEqual(
                request_info.get("url"),
                "https://api.example.test/customers",
            )

        asyncio.run(run_test())

    def test_execute_falls_back_to_mock_without_base_url(self) -> None:
        payload = QueryExecuteRequest(
            type="rest",
            name="legacy_query",
            config={"method": "GET", "url": "/legacy"},
        )

        async def run_test() -> None:
            service = QueryService()
            data, status_code, meta = await service.execute(
                payload,
                "user-1",
                db=None,
            )  # type: ignore[arg-type]
            self.assertEqual(status_code, 200)
            self.assertEqual(meta.get("mode"), "mock")
            self.assertIsInstance(data, dict)
            self.assertEqual(data.get("query"), "legacy_query")

        asyncio.run(run_test())

    def test_execute_with_encrypted_datasource_bearer(self) -> None:
        payload = QueryExecuteRequest(
            type="rest",
            datasource_id="ds-1",
            config={
                "url": "/health",
                "method": "GET",
            },
        )

        async def run_test() -> None:
            service = QueryService()
            captured_headers: dict[str, str] = {}
            datasource = SimpleNamespace(
                id="ds-1",
                owner_id="user-1",
                base_url="https://api.example.test",
                auth_type="bearer",
                auth_config=encrypt_auth_config({"token": "secret-token"}),
            )

            class FakeDb:
                async def scalar(
                    self,
                    _statement,
                ):  # type: ignore[no-untyped-def]
                    return datasource

            async def fake_request(
                self,
                method,
                url,
                **kwargs,
            ):  # type: ignore[no-untyped-def]
                request = httpx.Request(method=method, url=url)
                captured_headers.update(kwargs.get("headers", {}))
                return httpx.Response(200, request=request, json={"ok": True})

            with patch.object(httpx.AsyncClient, "request", new=fake_request):
                data, status_code, meta = await service.execute(
                    payload,
                    "user-1",
                    db=FakeDb(),
                )

            self.assertEqual(status_code, 200)
            self.assertEqual(data, {"ok": True})
            self.assertEqual(meta.get("mode"), "rest")
            self.assertEqual(
                captured_headers.get("Authorization"),
                "Bearer secret-token",
            )

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
