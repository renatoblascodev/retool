from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.schemas import AppCreateRequest, AppResponse, AppUpdateRequest
from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import AppMember, AppTemplate, Page, Template, ToolApp, User
from app.permissions.dependencies import require_role
from app.templates.schemas import SaveAsTemplateRequest, TemplateResponse

from uuid import uuid4
import json

router = APIRouter(prefix="/apps", tags=["apps"])


async def _get_accessible_app(
    app_id: str,
    db: AsyncSession,
    user_id: str,
) -> ToolApp:
    """Return app if user is the owner OR a member (any role). 404 otherwise."""
    # First try membership table (covers Sprint 4A+ apps)
    member = await db.scalar(
        select(AppMember).where(
            AppMember.app_id == app_id,
            AppMember.user_id == user_id,
        )
    )
    if member is not None:
        tool_app = await db.scalar(select(ToolApp).where(ToolApp.id == app_id))
        if tool_app is not None:
            return tool_app
    # Fallback: owner_id direct check (backward-compat for apps created before Sprint 4A)
    tool_app = await db.scalar(
        select(ToolApp).where(
            ToolApp.id == app_id,
            ToolApp.owner_id == user_id,
        )
    )
    if tool_app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return tool_app


# Keep legacy helper for write operations that still require owner check
async def _get_owned_app(
    app_id: str,
    db: AsyncSession,
    user_id: str,
) -> ToolApp:
    tool_app = await db.scalar(
        select(ToolApp).where(
            ToolApp.id == app_id,
            ToolApp.owner_id == user_id,
        ),
    )
    if tool_app is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    return tool_app


@router.get("", response_model=list[AppResponse])
async def list_apps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[AppResponse]:
    rows = await db.scalars(
        select(ToolApp)
        .where(ToolApp.owner_id == current_user.id)
        .order_by(ToolApp.created_at.desc()),
    )
    return [AppResponse.model_validate(row) for row in rows]


@router.post(
    "",
    response_model=AppResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_app(
    payload: AppCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    # Resolve template if provided
    template_layout: dict | None = None
    if payload.template_id is not None:
        tmpl = await db.get(AppTemplate, payload.template_id)
        if tmpl is None or not tmpl.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template not found or inactive",
            )
        # Deep copy layout_json so modifications to the app don't affect the template
        template_layout = json.loads(json.dumps(tmpl.layout_json))

    tool_app = ToolApp(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(tool_app)
    await db.flush()  # get tool_app.id without full commit

    # Auto-insert owner membership so RBAC checks work immediately
    owner_member = AppMember(
        app_id=tool_app.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(owner_member)

    # If a template was provided, create the initial "Home" page with its layout
    if template_layout is not None:
        page = Page(
            app_id=tool_app.id,
            name="Home",
            slug="home",
            layout_json=template_layout,
        )
        db.add(page)

    await db.commit()
    await db.refresh(tool_app)
    return AppResponse.model_validate(tool_app)


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    tool_app = await _get_accessible_app(app_id, db, current_user.id)
    return AppResponse.model_validate(tool_app)


@router.patch("/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: str,
    payload: AppUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> AppResponse:
    tool_app = await _get_owned_app(app_id, db, current_user.id)

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(tool_app, key, value)

    await db.commit()
    await db.refresh(tool_app)
    return AppResponse.model_validate(tool_app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    tool_app = await _get_owned_app(app_id, db, current_user.id)
    await db.delete(tool_app)
    await db.commit()


@router.post(
    "/{app_id}/as-template",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_as_template(
    app_id: str,
    payload: SaveAsTemplateRequest,
    _: AppMember = Depends(require_role("owner")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TemplateResponse:
    """Capture the first page layout and save it as a private template (owner only)."""
    page = await db.scalar(
        select(Page).where(Page.app_id == app_id).order_by(Page.created_at).limit(1)
    )
    layout_json = json.dumps(page.layout_json) if page and page.layout_json else "{}"

    slug = f"user-{current_user.id[:8]}-{str(uuid4())[:8]}"
    tmpl = Template(
        id=str(uuid4()),
        slug=slug,
        name=payload.name,
        category=payload.category,
        layout_json=layout_json,
        is_public=False,
        creator_id=current_user.id,
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return TemplateResponse.model_validate(tmpl)


# ---------------------------------------------------------------------------
# GET /apps/{app_id}/queries — list queries embedded in page layout_json
# ---------------------------------------------------------------------------

class _QueryInfo(dict):
    """Thin wrapper so we can return raw dicts from the endpoint."""


@router.get("/{app_id}/queries")
async def list_app_queries(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Return all queries defined across the app's pages (stored in layout_json)."""
    # Verify the user has any membership (viewer+)
    await _get_accessible_app(app_id, db, current_user.id)

    pages = await db.scalars(
        select(Page).where(Page.app_id == app_id).order_by(Page.created_at)
    )

    queries: list[dict] = []
    for page in pages:
        layout = page.layout_json or {}
        for q in layout.get("queries", []):
            entry = {
                "id": q.get("id"),
                "name": q.get("name"),
                "datasource_id": q.get("datasource_id"),
                "type": q.get("type", "rest"),
                "config": q.get("config", {}),
                "transform_js": q.get("transform_js"),
                "run_on_load": bool(q.get("runOnLoad", q.get("run_on_load", False))),
                "page_id": page.id,
            }
            queries.append(entry)
    return queries

