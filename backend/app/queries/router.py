from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db import get_db_session
from app.models import User
from app.queries.schemas import QueryExecuteRequest, QueryExecuteResponse
from app.queries.service import QueryService

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/execute", response_model=QueryExecuteResponse)
async def execute_query(
    payload: QueryExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    service: QueryService = Depends(QueryService),
) -> QueryExecuteResponse:
    result, status_code, meta = await service.execute(
        payload,
        current_user.id,
        db,
    )
    return QueryExecuteResponse(
        success=True,
        data=result,
        status_code=status_code,
        meta=meta,
    )
