from __future__ import annotations

import asyncio
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi import HTTPException

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


class ValidateUrlTests(unittest.TestCase):
    """Unit tests for _validate_url — SSRF protection."""

    def _run_validate(self, url: str, **settings_overrides) -> None:
        """Run _validate_url with optional settings patches.

        The patch is applied synchronously before asyncio.run so that
        the coroutine body executes with the mock already active (avoids
        any event-loop / anyio interaction with context-manager setup).
        """
        service = QueryService()

        with patch("app.queries.service.settings") as mock_settings:
            mock_settings.environment = settings_overrides.get(
                "environment", "production"
            )
            mock_settings.ssrf_allow_hosts = settings_overrides.get(
                "ssrf_allow_hosts", []
            )
            # Create the coroutine while the patch is active, then run it.
            coro = service._validate_url(url)
            asyncio.run(coro)

    def test_blocks_private_ip_literal(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            self._run_validate("http://192.168.1.1/secret")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_blocks_loopback_ip_literal(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            self._run_validate("http://127.0.0.1/admin")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_blocks_localhost_hostname(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            self._run_validate("http://localhost/internal")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_blocks_dot_local_hostname(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            self._run_validate("http://printer.local/ink")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_blocks_unsupported_scheme(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            self._run_validate("file:///etc/passwd")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_blocks_dns_rebinding_to_private_ip(self) -> None:
        """Hostname that resolves to a private IP must be rejected."""
        # Simulate DNS returning 10.0.0.1 for evil.example.test
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0))]

        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with self.assertRaises(HTTPException) as ctx:
                self._run_validate("http://evil.example.test/data")
        self.assertIn("private network", ctx.exception.detail.lower())

    def test_blocks_dns_rebinding_to_loopback(self) -> None:
        """Hostname that resolves to loopback must be rejected."""
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]

        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with self.assertRaises(HTTPException) as ctx:
                self._run_validate("http://rebind.example.test/admin")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_allows_public_hostname(self) -> None:
        """Hostname resolving to a public IP must pass."""
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            # Should not raise
            self._run_validate("https://example.com/api")

    def test_allowlist_permits_listed_host(self) -> None:
        """Host in ssrf_allow_hosts bypasses further checks."""
        # No DNS mock needed — allowlist returns before resolution
        self._run_validate(
            "https://api.example.test/data",
            ssrf_allow_hosts=["api.example.test"],
        )

    def test_allowlist_blocks_unlisted_host(self) -> None:
        """Host not in ssrf_allow_hosts is rejected even if otherwise valid."""
        fake_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

        with patch("socket.getaddrinfo", return_value=fake_addrinfo):
            with self.assertRaises(HTTPException) as ctx:
                self._run_validate(
                    "https://other.example.com/data",
                    ssrf_allow_hosts=["api.example.test"],
                )
        self.assertIn("allowlist", ctx.exception.detail.lower())

    def test_development_mode_allows_private_ip(self) -> None:
        """In development environment, private targets are allowed."""
        self._run_validate("http://192.168.1.1/test", environment="development")


if __name__ == "__main__":
    unittest.main()
