import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.datasources.secrets import decrypt_auth_config
from app.models import DataSource
from app.queries.schemas import QueryExecuteRequest


class QueryService:
    async def execute(
        self,
        payload: QueryExecuteRequest,
        user_id: str,
        db: AsyncSession,
    ) -> tuple[dict | list, int, dict]:
        if payload.type != "rest":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only rest query type is currently supported",
            )

        endpoint = (
            payload.config.get("url")
            or payload.config.get("endpoint")
            or "/"
        )
        method = str(payload.config.get("method", "GET")).upper()

        if payload.datasource_id:
            datasource = await db.scalar(
                select(DataSource).where(
                    DataSource.id == payload.datasource_id,
                    DataSource.owner_id == user_id,
                ),
            )
            if datasource is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Datasource not found",
                )
            base_url = datasource.base_url
            auth_type = datasource.auth_type
            auth_config = decrypt_auth_config(datasource.auth_config)
        else:
            base_url = str(payload.config.get("base_url", "")).strip()
            auth_type = str(payload.config.get("auth_type", "none"))
            auth_config = payload.config.get("auth_config") or {}

        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            request_url = endpoint
        else:
            if not base_url:
                # Backward-compatible local mock when no datasource/base_url
                # is provided.
                return (
                    {
                        "query": payload.name or "unnamed_query",
                        "type": payload.type,
                        "request": {
                            "method": method,
                            "endpoint": endpoint,
                            "variables": payload.variables,
                        },
                        "rows": [
                            {
                                "id": 1,
                                "name": "Alice",
                                "email": "alice@example.com",
                            },
                            {
                                "id": 2,
                                "name": "Bob",
                                "email": "bob@example.com",
                            },
                        ],
                    },
                    200,
                    {"mode": "mock"},
                )
            request_url = urljoin(
                base_url.rstrip("/") + "/",
                endpoint.lstrip("/"),
            )

        await self._validate_url(request_url)

        headers: dict[str, str] = dict(payload.config.get("headers") or {})
        if auth_type == "bearer" and auth_config.get("token"):
            headers["Authorization"] = f"Bearer {auth_config['token']}"
        if auth_type == "basic" and auth_config.get("username"):
            # Requests made with basic auth should not leak credentials
            # in response payloads.
            pass

        params = payload.config.get("params") or payload.variables or None
        body = payload.config.get("body")

        auth = None
        if auth_type == "basic" and auth_config.get("username"):
            auth = (
                str(auth_config.get("username", "")),
                str(auth_config.get("password", "")),
            )

        timeout = float(payload.config.get("timeout", 20))
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
        ) as client:
            response = await client.request(
                method=method,
                url=request_url,
                headers=headers,
                params=params,
                json=body,
                auth=auth,
            )

        try:
            data: dict | list = response.json()
        except ValueError:
            data = {"raw": response.text}

        return (
            data,
            response.status_code,
            {
                "mode": "rest",
                "request": {
                    "method": method,
                    "url": request_url,
                },
            },
        )

    async def _validate_url(self, request_url: str) -> None:
        parsed = urlparse(request_url)
        if parsed.scheme not in {"http", "https"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported URL scheme",
            )

        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL hostname",
            )

        # In development we allow local/private targets for local integration
        # tests.
        if settings.environment == "development":
            return

        # Allowlist: if configured, only hosts in the list are permitted.
        allow_hosts = settings.ssrf_allow_hosts
        if allow_hosts:
            if hostname.lower() not in {h.lower() for h in allow_hosts}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Host not in SSRF allowlist",
                )
            return

        # Block literal private IP addresses.
        try:
            ip_addr = ipaddress.ip_address(hostname)
            if (
                ip_addr.is_private
                or ip_addr.is_loopback
                or ip_addr.is_link_local
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Private network targets are blocked",
                )
            return
        except ValueError:
            pass

        # Block reserved local hostnames.
        lowered = hostname.lower()
        if lowered == "localhost" or lowered.endswith(".local"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local hostnames are blocked",
            )

        # DNS rebinding protection: resolve hostname and reject if any
        # resolved address is private/loopback/link-local.
        try:
            infos = await asyncio.to_thread(
                socket.getaddrinfo,
                hostname,
                None,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
            )
        except OSError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hostname could not be resolved",
            )

        for info in infos:
            raw_ip = info[4][0]
            try:
                ip_addr = ipaddress.ip_address(raw_ip)
                if (
                    ip_addr.is_private
                    or ip_addr.is_loopback
                    or ip_addr.is_link_local
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Hostname resolves to a private network address",
                    )
            except ValueError:
                pass
