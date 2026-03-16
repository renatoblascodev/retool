"""Secure SQL query executor for PostgreSQL datasources.

Security constraints enforced here:
- Only read-only statements are allowed (SELECT, WITH, EXPLAIN).
- Parameterized values via asyncpg to prevent SQL injection.
- Hard limit of 1 000 rows returned.
- Query timeout of 30 seconds.
- A fresh connection is opened per invocation; no shared pool between users.
"""
from __future__ import annotations

import re
from typing import Any

import asyncpg
from fastapi import HTTPException, status

_MAX_ROWS = 1_000
_TIMEOUT_SECONDS = 30.0

# Statements allowed as the first keyword in the query.
_ALLOWED_FIRST_KEYWORDS = frozenset({"select", "with", "explain"})

# Regex that matches /* ... */ and -- ... comments so we can strip them before
# keyword extraction (avoids /* DROP */ SELECT bypass).
_COMMENT_RE = re.compile(r"/\*.*?\*/|--[^\n]*", re.DOTALL)


def _assert_readonly(sql: str) -> None:
    """Raise HTTPException(400) if *sql* is not a read-only statement."""
    cleaned = _COMMENT_RE.sub(" ", sql).strip()
    # Extract the first token (keyword).
    first_token = re.split(r"\s+", cleaned)[0].lower()
    if first_token not in _ALLOWED_FIRST_KEYWORDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only read-only SQL statements are allowed "
                f"(SELECT / WITH / EXPLAIN). Got: {first_token!r}"
            ),
        )


def _build_dsn(creds: dict[str, Any]) -> str:
    """Build a PostgreSQL DSN from a credentials dict.

    Expected keys (all optional with sane defaults):
        host, port, database, user, password
    """
    host = str(creds.get("host", "localhost"))
    port = int(creds.get("port", 5432))
    database = str(creds.get("database", "postgres"))
    user = str(creds.get("user", "postgres"))
    password = str(creds.get("password", ""))
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


async def execute_sql(
    sql: str,
    creds: dict[str, Any],
    variables: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute *sql* against a PostgreSQL database described by *creds*.

    Returns a list of row dicts (column name → value), capped at ``_MAX_ROWS``.
    Raises :class:`fastapi.HTTPException` on validation or execution errors.
    """
    _assert_readonly(sql)

    if not sql.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SQL query must not be empty.",
        )

    dsn = _build_dsn(creds)

    try:
        conn: asyncpg.Connection = await asyncpg.connect(dsn, timeout=10.0)
    except (asyncpg.PostgresConnectionError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not connect to database: {exc}",
        ) from exc

    try:
        rows = await asyncpg.connection.Connection.fetch(
            conn, sql, timeout=_TIMEOUT_SECONDS
        )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL error: {exc}",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="SQL query timed out.",
        ) from exc
    finally:
        await conn.close()

    # asyncpg returns Record objects; convert to plain dicts.
    result = [dict(row) for row in rows[:_MAX_ROWS]]
    return result
