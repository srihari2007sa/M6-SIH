"""
Source Registry API — complete CRUD + enable/disable.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse, Response

from backend.app.core.dependencies import DepDB, dep_current_user
from backend.app.core.rbac import ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER, get_primary_role, require_roles
from backend.app.models.source import SourceStatus
from backend.app.registry.source_registry import SourceRegistry
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.source import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/sources")

# ── Helpers ────────────────────────────────────────────────────────────────────

def _svc(db: DepDB) -> SourceRegistry:
    return SourceRegistry(db)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[SourceResponse])
async def list_sources(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
    q: str | None = Query(None, description="Search query"),
    vendor: str | None = Query(None),
    status: SourceStatus | None = Query(None),
    tenant_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[SourceResponse]:
    svc = _svc(db)
    items, total = await svc.list(
        q=q, vendor=vendor, status=status, tenant_id=tenant_id,
        page=page, page_size=page_size,
    )
    return PaginatedResponse(
        items=[SourceResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> SourceResponse:
    svc = _svc(db)
    source = await svc.create(data, current_user.username, get_primary_role(current_user))  # type: ignore[attr-defined]
    return SourceResponse.model_validate(source)


@router.get("/{id}", response_model=SourceResponse)
async def get_source(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
) -> SourceResponse:
    svc = _svc(db)
    source = await svc.get(id)
    return SourceResponse.model_validate(source)


@router.put("/{id}", response_model=SourceResponse)
async def update_source(
    id: str,
    data: SourceUpdate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> SourceResponse:
    svc = _svc(db)
    source = await svc.update(id, data, current_user.username, get_primary_role(current_user))  # type: ignore[attr-defined]
    return SourceResponse.model_validate(source)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> Response:
    svc = _svc(db)
    await svc.delete(id, current_user.username, get_primary_role(current_user))  # type: ignore[attr-defined]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/enable", response_model=SourceResponse)
async def enable_source(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> SourceResponse:
    svc = _svc(db)
    source = await svc.enable(id, current_user.username, get_primary_role(current_user))  # type: ignore[attr-defined]
    return SourceResponse.model_validate(source)


@router.post("/{id}/disable", response_model=SourceResponse)
async def disable_source(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> SourceResponse:
    svc = _svc(db)
    source = await svc.disable(id, current_user.username, get_primary_role(current_user))  # type: ignore[attr-defined]
    return SourceResponse.model_validate(source)
