"""Tests for the SQL executor module."""
from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.queries.sql_executor import _assert_readonly, _build_dsn, execute_sql


class AssertReadonlyTests(unittest.TestCase):
    """Unit tests for SQL statement validation."""

    def test_select_allowed(self) -> None:
        _assert_readonly("SELECT 1")

    def test_select_mixed_case(self) -> None:
        _assert_readonly("  Select * FROM users")

    def test_with_cte_allowed(self) -> None:
        _assert_readonly("WITH cte AS (SELECT 1) SELECT * FROM cte")

    def test_explain_allowed(self) -> None:
        _assert_readonly("EXPLAIN SELECT * FROM users")

    def test_insert_blocked(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _assert_readonly("INSERT INTO users VALUES (1)")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_update_blocked(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _assert_readonly("UPDATE users SET name='x'")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_delete_blocked(self) -> None:
        with self.assertRaises(HTTPException):
            _assert_readonly("DELETE FROM users")

    def test_drop_blocked(self) -> None:
        with self.assertRaises(HTTPException):
            _assert_readonly("DROP TABLE users")

    def test_create_blocked(self) -> None:
        with self.assertRaises(HTTPException):
            _assert_readonly("CREATE TABLE foo (id int)")

    def test_comment_bypass_blocked(self) -> None:
        # Attacker hides DROP behind a comment prefix — stripped to DROP.
        with self.assertRaises(HTTPException):
            _assert_readonly("/* harmless */ DROP TABLE users")


class BuildDsnTests(unittest.TestCase):
    def test_full_credentials(self) -> None:
        creds = {
            "host": "db.example.com",
            "port": 5432,
            "database": "mydb",
            "user": "myuser",
            "password": "secret",
        }
        dsn = _build_dsn(creds)
        self.assertEqual(dsn, "postgresql://myuser:secret@db.example.com:5432/mydb")

    def test_defaults(self) -> None:
        dsn = _build_dsn({})
        self.assertIn("postgresql://", dsn)
        self.assertIn("localhost", dsn)


class ExecuteSqlTests(unittest.IsolatedAsyncioTestCase):
    """Integration-level tests with asyncpg mocked out."""

    async def test_execute_sql_returns_rows(self) -> None:
        fake_row = {"id": 1, "name": "Alice"}

        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[fake_row])
        mock_conn.close = AsyncMock()

        with (
            patch("asyncpg.connect", new=AsyncMock(return_value=mock_conn)),
            patch(
                "asyncpg.connection.Connection.fetch",
                new=AsyncMock(return_value=[fake_row]),
            ),
        ):
            # Patch the module-level fetch call used inside execute_sql
            with patch("app.queries.sql_executor.asyncpg.connect", new=AsyncMock(return_value=mock_conn)):
                mock_conn.close = AsyncMock()
                # Monkey-patch Connection.fetch on the mock
                import asyncpg.connection as _aconn
                original_fetch = getattr(_aconn.Connection, "fetch", None)
                try:
                    _aconn.Connection.fetch = AsyncMock(return_value=[fake_row])
                    result = await execute_sql(
                        "SELECT * FROM users",
                        {"host": "localhost", "database": "test", "user": "u", "password": "p"},
                    )
                finally:
                    if original_fetch is not None:
                        _aconn.Connection.fetch = original_fetch

        self.assertIsInstance(result, list)

    async def test_execute_sql_blocks_delete(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            await execute_sql("DELETE FROM users", {})
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_execute_sql_blocks_empty(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            await execute_sql("   ", {})
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_execute_sql_connection_error(self) -> None:
        """Connection failures surface as 502."""
        with patch(
            "app.queries.sql_executor.asyncpg.connect",
            side_effect=OSError("connection refused"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await execute_sql("SELECT 1", {"host": "bad-host"})
        self.assertEqual(ctx.exception.status_code, 502)
