from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.apps.members_router import router as members_router
from app.apps.router import router as apps_router
from app.auth.router import router as auth_router
from app.config import settings
from app.datasources.router import router as datasources_router
from app.db import init_db
from app.pages.router import router as pages_router
from app.queries.router import router as queries_router
from app.templates.router import router as templates_router

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def healthcheck() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(apps_router, prefix=settings.api_v1_prefix)
app.include_router(members_router, prefix=settings.api_v1_prefix)
app.include_router(pages_router, prefix=settings.api_v1_prefix)
app.include_router(datasources_router, prefix=settings.api_v1_prefix)
app.include_router(queries_router, prefix=settings.api_v1_prefix)
app.include_router(templates_router, prefix=settings.api_v1_prefix)

# ── SPA static serving (only active in release image) ────────────
# When Dockerfile.release is used the compiled frontend is at /app/static.
# API routes registered above take precedence; this is a catch-all fallback.
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    _assets_dir = _static_dir / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="spa-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(_static_dir / "index.html")
