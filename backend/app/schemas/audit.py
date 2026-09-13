"""Audit log Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.models.audit_log import AuditAction, AuditResult
from backend.app.schemas.common import OrmModel


class AuditLogResponse(OrmModel):
    id: str
    timestamp: datetime
    actor: str
    actor_role: str | None
    action: AuditAction
    resource_type: str
    resource_id: str | None
    version: str | None
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    reason: str | None
    result: AuditResult
    request_id: str | None
