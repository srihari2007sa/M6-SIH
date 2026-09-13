"""Source Registry service."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.audit_service import AuditService
from backend.app.core.exceptions import DuplicateError, SourceNotFound
from backend.app.models.audit_log import AuditAction
from backend.app.models.source import Source, SourceStatus
from backend.app.repositories.source_repo import SourceRepository
from backend.app.schemas.source import SourceCreate, SourceUpdate


class SourceRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = SourceRepository(db)
        self._audit = AuditService(db)

    async def create(self, data: SourceCreate, actor: str, actor_role: str | None) -> Source:
        if await self._repo.source_id_exists(data.source_id):
            raise DuplicateError(f"Source '{data.source_id}' already exists")

        tags_str = json.dumps(data.tags) if data.tags else None
        source = Source(
            source_id=data.source_id,
            tenant_id=data.tenant_id,
            name=data.name,
            vendor=data.vendor,
            product=data.product,
            source_type=data.source_type,
            protocol=data.protocol,
            transport=data.transport,
            port=data.port,
            zone=data.zone,
            parser_id=data.parser_id,
            description=data.description,
            tags=tags_str,
            created_by=actor,
            updated_by=actor,
        )
        source = await self._repo.create(source)
        await self._audit.record(
            actor=actor,
            actor_role=actor_role,
            action=AuditAction.SOURCE_CREATED,
            resource_type="source",
            resource_id=source.source_id,
            after_state=self._snapshot(source),
        )
        return source

    async def get(self, id: str) -> Source:
        source = await self._repo.get(id)
        if not source:
            raise SourceNotFound(f"Source '{id}' not found")
        return source

    async def get_by_source_id(self, source_id: str) -> Source:
        source = await self._repo.get_by_source_id(source_id)
        if not source:
            raise SourceNotFound(f"Source '{source_id}' not found")
        return source

    async def list(
        self,
        *,
        q: str | None = None,
        vendor: str | None = None,
        status: SourceStatus | None = None,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Source], int]:
        skip = (page - 1) * page_size
        items, total = await self._repo.search(
            q=q, vendor=vendor, status=status, tenant_id=tenant_id,
            skip=skip, limit=page_size,
        )
        return list(items), total

    async def update(
        self, id: str, data: SourceUpdate, actor: str, actor_role: str | None
    ) -> Source:
        source = await self.get(id)
        before = self._snapshot(source)
        update_data: dict[str, Any] = data.model_dump(exclude_none=True)
        if "tags" in update_data:
            update_data["tags"] = json.dumps(update_data["tags"])
        update_data["updated_by"] = actor
        source = await self._repo.update(source, update_data)
        await self._audit.record(
            actor=actor,
            actor_role=actor_role,
            action=AuditAction.SOURCE_UPDATED,
            resource_type="source",
            resource_id=source.source_id,
            before_state=before,
            after_state=self._snapshot(source),
        )
        return source

    async def delete(self, id: str, actor: str, actor_role: str | None) -> None:
        source = await self.get(id)
        before = self._snapshot(source)
        await self._repo.delete(source)
        await self._audit.record(
            actor=actor,
            actor_role=actor_role,
            action=AuditAction.SOURCE_DELETED,
            resource_type="source",
            resource_id=source.source_id,
            before_state=before,
        )

    async def enable(self, id: str, actor: str, actor_role: str | None) -> Source:
        source = await self.get(id)
        source.status = SourceStatus.ACTIVE
        source.updated_by = actor
        await self._repo._db.flush()
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.SOURCE_ENABLED,
            resource_type="source", resource_id=source.source_id,
            after_state=self._snapshot(source),
        )
        return source

    async def disable(self, id: str, actor: str, actor_role: str | None) -> Source:
        source = await self.get(id)
        source.status = SourceStatus.DISABLED
        source.updated_by = actor
        await self._repo._db.flush()
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.SOURCE_DISABLED,
            resource_type="source", resource_id=source.source_id,
            after_state=self._snapshot(source),
        )
        return source

    @staticmethod
    def _snapshot(source: Source) -> dict[str, Any]:
        return {
            "source_id": source.source_id,
            "name": source.name,
            "status": source.status.value,
            "vendor": source.vendor,
            "product": source.product,
        }
