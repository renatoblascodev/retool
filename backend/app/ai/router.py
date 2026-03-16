"""AI router — endpoints for app generation and query suggestion."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import service
from app.ai.schemas import (
    GenerateAppRequest,
    GenerateAppResponse,
    SuggestQueryRequest,
    SuggestQueryResponse,
    WidgetLayout,
    SuggestedQuery,
)
from app.auth.dependencies import get_current_user
from app.config import settings
from app.db import get_db_session
from app.models import DataSource, User
from app.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])


def _datasource_info(ds: DataSource) -> str:
    ds_type = getattr(ds, "ds_type", None) or "rest"
    base_url = ds.base_url or ""
    return f"type={ds_type}, base_url={base_url}, name={ds.name}"


@router.post(
    "/generate-app",
    response_model=GenerateAppResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an app layout from a natural-language prompt",
)
@limiter.limit(settings.ai_rate_limit_generate)
async def generate_app(
    request: Request,
    body: GenerateAppRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> GenerateAppResponse:
    datasource_info = "No datasource selected."

    if body.datasource_id:
        ds = await db.scalar(
            select(DataSource).where(
                DataSource.id == body.datasource_id,
                DataSource.owner_id == current_user.id,
            )
        )
        if ds is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Datasource not found",
            )
        datasource_info = _datasource_info(ds)

    try:
        data = await service.generate_app(body.prompt, datasource_info)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service timed out. Please try again.",
        )
    except ValueError as exc:
        logger.error("AI generate_app schema error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an unexpected response format.",
        )

    try:
        return GenerateAppResponse(
            layout=[WidgetLayout(**w) for w in data.get("layout", [])],
            suggested_queries=[
                SuggestedQuery(**q) for q in data.get("suggested_queries", [])
            ],
            explanation=data.get("explanation", ""),
        )
    except Exception as exc:
        logger.error("Failed to parse AI response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an invalid layout structure.",
        )


@router.post(
    "/suggest-query",
    response_model=SuggestQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest a query for a datasource based on a natural-language goal",
)
@limiter.limit(settings.ai_rate_limit_suggest)
async def suggest_query(
    request: Request,
    body: SuggestQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SuggestQueryResponse:
    ds = await db.scalar(
        select(DataSource).where(
            DataSource.id == body.datasource_id,
            DataSource.owner_id == current_user.id,
        )
    )
    if ds is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datasource not found",
        )

    ds_type = getattr(ds, "ds_type", None) or "rest"
    ds_info = _datasource_info(ds)

    try:
        data = await service.suggest_query(ds_type, ds_info, body.goal)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service timed out. Please try again.",
        )
    except ValueError as exc:
        logger.error("AI suggest_query schema error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an unexpected response format.",
        )

    return SuggestQueryResponse(
        query=data["query"],
        explanation=data.get("explanation", ""),
    )
