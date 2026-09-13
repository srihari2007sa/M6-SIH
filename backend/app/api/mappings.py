"""Mapping Registry API."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from backend.app.core.dependencies import DepDB, dep_current_user
from backend.app.core.rbac import ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER, get_primary_role, require_roles
from backend.app.registry.mapping_registry import MappingRegistry
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.mapping import MappingCreate, MappingResponse, MappingUpdate

router = APIRouter(prefix="/mappings")


def _svc(db: DepDB) -> MappingRegistry:
    return MappingRegistry(db)


@router.get("", response_model=PaginatedResponse[MappingResponse])
async def list_mappings(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
    q: str | None = Query(None),
    source_format: str | None = Query(None),
    target_schema: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[MappingResponse]:
    items, total = await _svc(db).list(
        q=q, source_format=source_format, target_schema=target_schema,
        page=page, page_size=page_size,
    )
    return PaginatedResponse(
        items=[MappingResponse.model_validate(m) for m in items],
        total=total, page=page, page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.post("", response_model=MappingResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: MappingCreate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV))],
) -> MappingResponse:
    mapping = await _svc(db).create(
        data, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return MappingResponse.model_validate(mapping)


@router.get("/{id}", response_model=MappingResponse)
async def get_mapping(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
) -> MappingResponse:
    return MappingResponse.model_validate(await _svc(db).get(id))


@router.put("/{id}", response_model=MappingResponse)
async def update_mapping(
    id: str,
    data: MappingUpdate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV))],
) -> MappingResponse:
    mapping = await _svc(db).update(
        id, data, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return MappingResponse.model_validate(mapping)
