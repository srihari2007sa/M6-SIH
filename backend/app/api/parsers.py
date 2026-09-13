"""
Parser Registry API — CRUD + full lifecycle transitions.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from backend.app.core.dependencies import DepDB, dep_current_user
from backend.app.core.rbac import ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER, get_primary_role, require_roles
from backend.app.models.parser import ParserStatus
from backend.app.registry.parser_registry import ParserRegistry
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.parser import (
    ParserCreate,
    ParserLifecycleRequest,
    ParserResponse,
    ParserUpdate,
    ParserVersionResponse,
)

router = APIRouter(prefix="/parsers")


def _svc(db: DepDB) -> ParserRegistry:
    return ParserRegistry(db)


@router.get("", response_model=PaginatedResponse[ParserResponse])
async def list_parsers(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
    q: str | None = Query(None),
    status: ParserStatus | None = Query(None),
    vendor: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[ParserResponse]:
    items, total = await _svc(db).list(
        q=q, status=status, vendor=vendor, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[ParserResponse.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.post("", response_model=ParserResponse, status_code=status.HTTP_201_CREATED)
async def register_parser(
    data: ParserCreate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV))],
) -> ParserResponse:
    parser = await _svc(db).register(
        data, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.get("/{id}", response_model=ParserResponse)
async def get_parser(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
) -> ParserResponse:
    return ParserResponse.model_validate(await _svc(db).get(id))


@router.put("/{id}", response_model=ParserResponse)
async def update_parser(
    id: str,
    data: ParserUpdate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV))],
) -> ParserResponse:
    parser = await _svc(db).update(
        id, data, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.post("/{id}/submit", response_model=ParserResponse)
async def submit_parser(
    id: str,
    body: ParserLifecycleRequest,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV))],
) -> ParserResponse:
    parser = await _svc(db).submit(
        id, current_user.username, get_primary_role(current_user), body.reason  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.post("/{id}/approve", response_model=ParserResponse)
async def approve_parser(
    id: str,
    body: ParserLifecycleRequest,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> ParserResponse:
    parser = await _svc(db).approve(
        id, current_user.username, get_primary_role(current_user), body.reason  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.post("/{id}/activate", response_model=ParserResponse)
async def activate_parser(
    id: str,
    body: ParserLifecycleRequest,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> ParserResponse:
    parser = await _svc(db).activate(
        id, current_user.username, get_primary_role(current_user), body.reason  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.post("/{id}/disable", response_model=ParserResponse)
async def disable_parser(
    id: str,
    body: ParserLifecycleRequest,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV))],
) -> ParserResponse:
    parser = await _svc(db).disable(
        id, current_user.username, get_primary_role(current_user), body.reason  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.post("/{id}/rollback", response_model=ParserResponse)
async def rollback_parser(
    id: str,
    body: ParserLifecycleRequest,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> ParserResponse:
    parser = await _svc(db).rollback(
        id, current_user.username, get_primary_role(current_user), body.reason  # type: ignore[attr-defined]
    )
    return ParserResponse.model_validate(parser)


@router.get("/{id}/history", response_model=list[ParserVersionResponse])
async def get_parser_history(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
) -> list[ParserVersionResponse]:
    versions = await _svc(db).get_history(id)
    return [ParserVersionResponse.model_validate(v) for v in versions]
