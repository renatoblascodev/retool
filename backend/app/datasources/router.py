from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.datasources.secrets import encrypt_auth_config
from app.datasources.schemas import (
    DataSourceCreateRequest,
    DataSourceResponse,
    DataSourceUpdateRequest,
)
from app.db import get_db_session
from app.models import DataSource, User

router = APIRouter(prefix="/datasources", tags=["datasources"])


async def _get_owned_datasource(
    datasource_id: str,
    db: AsyncSession,
    user_id: str,
) -> DataSource:
    datasource = await db.scalar(
        select(DataSource).where(
            DataSource.id == datasource_id,
            DataSource.owner_id == user_id,
        ),
    )
    if datasource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Datasource not found",
        )
    return datasource


def _to_response(datasource: DataSource) -> DataSourceResponse:
    return DataSourceResponse(
        id=datasource.id,
        owner_id=datasource.owner_id,
        name=datasource.name,
        base_url=datasource.base_url,
        auth_type=datasource.auth_type,
        has_auth_config=bool(datasource.auth_config),
        created_at=datasource.created_at,
        updated_at=datasource.updated_at,
    )


@router.get("", response_model=list[DataSourceResponse])
async def list_datasources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DataSourceResponse]:
    rows = await db.scalars(
        select(DataSource)
        .where(DataSource.owner_id == current_user.id)
        .order_by(DataSource.created_at.desc()),
    )
    return [_to_response(row) for row in rows]


@router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_datasource(
    payload: DataSourceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DataSourceResponse:
    encrypted_auth_config = (
        {} if payload.auth_type == "none" else encrypt_auth_config(payload.auth_config)
    )

    datasource = DataSource(
        owner_id=current_user.id,
        name=payload.name,
        base_url=payload.base_url,
        auth_type=payload.auth_type,
        auth_config=encrypted_auth_config,
    )
    db.add(datasource)
    await db.commit()
    await db.refresh(datasource)
    return _to_response(datasource)


@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(
    datasource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DataSourceResponse:
    datasource = await _get_owned_datasource(
        datasource_id,
        db,
        current_user.id,
    )
    return _to_response(datasource)


@router.patch("/{datasource_id}", response_model=DataSourceResponse)
async def update_datasource(
    datasource_id: str,
    payload: DataSourceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DataSourceResponse:
    datasource = await _get_owned_datasource(
        datasource_id,
        db,
        current_user.id,
    )

    data = payload.model_dump(exclude_unset=True)
    next_auth_type = str(data.get("auth_type", datasource.auth_type))

    if "auth_config" in data:
        data["auth_config"] = (
            {} if next_auth_type == "none" else encrypt_auth_config(data["auth_config"])
        )
    elif "auth_type" in data and next_auth_type == "none":
        data["auth_config"] = {}

    for key, value in data.items():
        setattr(datasource, key, value)

    await db.commit()
    await db.refresh(datasource)
    return _to_response(datasource)


@router.delete("/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    datasource = await _get_owned_datasource(
        datasource_id,
        db,
        current_user.id,
    )
    await db.delete(datasource)
    await db.commit()
