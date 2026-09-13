"""
Configuration Distribution API.
GET  /api/v1/configuration           – current Redis config snapshot
POST /api/v1/configuration/distribute – push all config to Redis
POST /api/v1/configuration/distribute/{key} – push one key
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from backend.app.core.dependencies import DepDB, dep_current_user
from backend.app.core.rbac import ADMIN, SEC_ANALYST, VIEWER, get_primary_role, require_roles
from backend.app.services.config_service import ConfigDistributionService

router = APIRouter(prefix="/configuration")

VALID_KEYS = {"sources", "parsers", "schemas", "mappings", "policies"}


@router.get("")
async def get_configuration(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, SEC_ANALYST, VIEWER))],
) -> dict:
    """Return current configuration snapshot from Redis."""
    svc = ConfigDistributionService(db)
    return await svc.get_current_config()


@router.post("/distribute")
async def distribute_all(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> dict:
    """Push all config keys to Redis and publish Kafka events."""
    svc = ConfigDistributionService(db)
    versions = await svc.distribute_all(
        current_user.username,  # type: ignore[attr-defined]
        get_primary_role(current_user),
    )
    return {"distributed": versions, "status": "ok"}


@router.post("/distribute/{key}")
async def distribute_key(
    key: Annotated[str, Path(description="Config key: sources|parsers|schemas|mappings|policies")],
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN))],
) -> dict:
    """Push a single config key to Redis."""
    if key not in VALID_KEYS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown key '{key}'. Valid: {VALID_KEYS}")
    svc = ConfigDistributionService(db)
    distributor = getattr(svc, f"distribute_{key}")
    version = await distributor(
        current_user.username,  # type: ignore[attr-defined]
        get_primary_role(current_user),
    )
    return {"key": key, "version": version, "status": "ok"}


@router.get("/version")
async def get_config_version(
    db: DepDB,
    current_user: Annotated[object, Depends(require_roles(ADMIN, SEC_ANALYST, VIEWER))],
) -> dict:
    """Return the current monotonic config version from Redis."""
    svc = ConfigDistributionService(db)
    version = await svc.get_config_version()
    return {"version": version}
