"""Policy Management API."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from backend.app.core.dependencies import DepDB, dep_current_user
from backend.app.core.rbac import ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER, get_primary_role, require_roles
from backend.app.registry.policy_registry import PolicyRegistry
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.policy import PolicyCreate, PolicyResponse, PolicyUpdate

router = APIRouter(prefix="/policies")


def _svc(db: DepDB) -> PolicyRegistry:
    return PolicyRegistry(db)


@router.get("", response_model=PaginatedResponse[PolicyResponse])
async def list_policies(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
    q: str | None = Query(None),
    is_enabled: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PolicyResponse]:
    items, total = await _svc(db).list(
        q=q, is_enabled=is_enabled, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[PolicyResponse.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
        pages=max(1, -(-total // page_size)),
    )


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    data: PolicyCreate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> PolicyResponse:
    policy = await _svc(db).create(
        data, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return PolicyResponse.model_validate(policy)


@router.get("/{id}", response_model=PolicyResponse)
async def get_policy(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, PARSER_DEV, SEC_ANALYST, VIEWER))],
) -> PolicyResponse:
    return PolicyResponse.model_validate(await _svc(db).get(id))


@router.put("/{id}", response_model=PolicyResponse)
async def update_policy(
    id: str,
    data: PolicyUpdate,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> PolicyResponse:
    policy = await _svc(db).update(
        id, data, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return PolicyResponse.model_validate(policy)


@router.post("/{id}/enable", response_model=PolicyResponse)
async def enable_policy(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> PolicyResponse:
    policy = await _svc(db).enable(
        id, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return PolicyResponse.model_validate(policy)


@router.post("/{id}/disable", response_model=PolicyResponse)
async def disable_policy(
    id: str,
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> PolicyResponse:
    policy = await _svc(db).disable(
        id, current_user.username, get_primary_role(current_user)  # type: ignore[attr-defined]
    )
    return PolicyResponse.model_validate(policy)
