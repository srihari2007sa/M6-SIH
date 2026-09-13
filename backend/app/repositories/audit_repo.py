"""Audit log repository — append-only writes, filtered reads."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit_log import AuditAction, AuditLog, AuditResult
from backend.app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AuditLog, db)

    async def append(
        self,
        *,
        actor: str,
        actor_role: str | None,
        action: AuditAction,
        resource_type: str,
        resource_id: str | None = None,
        version: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        reason: str | None = None,
        result: AuditResult = AuditResult.SUCCESS,
        request_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            actor=actor,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            version=version,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            result=result,
            request_id=request_id,
            extra=extra,
        )
        self._db.add(log)
        await self._db.flush()
        return log

    async def search(
        self,
        *,
        actor: str | None = None,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[AuditLog], int]:
        stmt = select(AuditLog)
        filters = []
        if actor:
            filters.append(AuditLog.actor == actor)
        if action:
            filters.append(AuditLog.action == action)
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)
        if since:
            filters.append(AuditLog.timestamp >= since)
        if until:
            filters.append(AuditLog.timestamp <= until)
        if filters:
            stmt = stmt.where(*filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(skip).limit(limit).order_by(AuditLog.timestamp.desc())
        items = (await self._db.execute(stmt)).scalars().all()
        return items, total
