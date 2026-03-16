from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass

import httpx


@dataclass
class SmokeContext:
    base_url: str
    email: str
    password: str


class SmokeTestError(RuntimeError):
    pass


def _assert_status(
    response: httpx.Response,
    expected: set[int],
    step: str,
) -> None:
    if response.status_code not in expected:
        raise SmokeTestError(
            (f"{step} failed with status {response.status_code}: {response.text}"),
        )


def _register_or_login(client: httpx.Client, ctx: SmokeContext) -> str:
    register_payload = {"email": ctx.email, "password": ctx.password}
    register = client.post("/api/auth/register", json=register_payload)
    _assert_status(register, {201, 409}, "register")

    login_payload = {"email": ctx.email, "password": ctx.password}
    login = client.post("/api/auth/login", json=login_payload)
    _assert_status(login, {200}, "login")

    token = login.json().get("access_token")
    if not token:
        raise SmokeTestError("login response did not include access_token")
    return str(token)


def run_smoke(ctx: SmokeContext) -> None:
    timeout = httpx.Timeout(20.0)
    with httpx.Client(base_url=ctx.base_url, timeout=timeout) as client:
        health = client.get("/health")
        _assert_status(health, {200}, "healthcheck")

        token = _register_or_login(client, ctx)
        auth_headers = {"Authorization": f"Bearer {token}"}

        app_payload = {
            "name": f"Smoke App {int(time.time())}",
            "description": "Automated smoke validation",
        }
        create_app = client.post(
            "/api/apps",
            headers=auth_headers,
            json=app_payload,
        )
        _assert_status(create_app, {201}, "create app")
        app_id = str(create_app.json().get("id"))

        page_payload = {
            "name": "Smoke Page",
            "slug": f"smoke-{int(time.time())}",
            "layout_json": {"widgets": []},
        }
        create_page = client.post(
            f"/api/apps/{app_id}/pages",
            headers=auth_headers,
            json=page_payload,
        )
        _assert_status(create_page, {201}, "create page")
        page_id = str(create_page.json().get("id"))

        layout_payload = {
            "layout_json": {
                "widgets": [
                    {
                        "id": "smoke-widget-1",
                        "type": "text",
                        "title": "Smoke Widget",
                        "x": 0,
                        "y": 0,
                        "w": 4,
                        "h": 2,
                        "props": {"content": "ok"},
                    }
                ]
            }
        }
        update_page = client.patch(
            f"/api/apps/{app_id}/pages/{page_id}",
            headers=auth_headers,
            json=layout_payload,
        )
        _assert_status(update_page, {200}, "update page layout")

        datasource = client.post(
            "/api/datasources",
            headers=auth_headers,
            json={
                "name": "Local API",
                "base_url": ctx.base_url,
                "auth_type": "bearer",
                "auth_config": {"token": "local-smoke-token"},
            },
        )
        _assert_status(datasource, {201}, "create datasource")
        datasource_id = str(datasource.json().get("id"))

        query = client.post(
            "/api/queries/execute",
            headers=auth_headers,
            json={
                "type": "rest",
                "name": "smoke_query",
                "datasource_id": datasource_id,
                "config": {"method": "GET", "url": "/health"},
                "variables": {"ok": True},
            },
        )
        _assert_status(query, {200}, "execute query")

        apps = client.get("/api/apps", headers=auth_headers)
        _assert_status(apps, {200}, "list apps")

        pages = client.get(f"/api/apps/{app_id}/pages", headers=auth_headers)
        _assert_status(pages, {200}, "list pages")

        print("SMOKE_TEST_OK")
        print(
            json.dumps(
                {
                    "user": ctx.email,
                    "app_id": app_id,
                    "page_id": page_id,
                    "datasource_id": datasource_id,
                    "health": health.json(),
                },
                indent=2,
            ),
        )


def parse_args() -> SmokeContext:
    parser = argparse.ArgumentParser(description="Run backend API smoke test")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL",
    )
    parser.add_argument(
        "--email",
        default="dev1773446943@example.com",
        help="Login email",
    )
    parser.add_argument(
        "--password",
        default="Pass1234Aa",
        help="Login password",
    )
    args = parser.parse_args()
    return SmokeContext(
        base_url=args.base_url.rstrip("/"),
        email=args.email,
        password=args.password,
    )


def main() -> None:
    ctx = parse_args()
    run_smoke(ctx)


if __name__ == "__main__":
    main()
