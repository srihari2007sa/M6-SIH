"""Mapping Registry service."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.audit_service import AuditService
from backend.app.core.exceptions import DuplicateError, MappingNotFound
from backend.app.models.audit_log import AuditAction
from backend.app.models.mapping import Mapping
from backend.app.repositories.mapping_repo import MappingRepository
from backend.app.schemas.mapping import MappingCreate, MappingUpdate


class MappingRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = MappingRepository(db)
        self._audit = AuditService(db)

    async def create(
        self, data: MappingCreate, actor: str, actor_role: str | None
    ) -> Mapping:
        if await self._repo.mapping_id_exists(data.mapping_id):
            raise DuplicateError(f"Mapping '{data.mapping_id}' already exists")
        mapping = Mapping(
            mapping_id=data.mapping_id,
            name=data.name,
            source_format=data.source_format,
            target_schema=data.target_schema,
            target_version=data.target_version,
            version=data.version,
            fields=data.fields,
            description=data.description,
            created_by=actor,
            updated_by=actor,
        )
        mapping = await self._repo.create(mapping)
        await self._repo.add_version(mapping, actor, "Initial version")
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.MAPPING_CREATED,
            resource_type="mapping", resource_id=mapping.mapping_id,
            after_state=self._snapshot(mapping),
        )
        return mapping

    async def get(self, id: str) -> Mapping:
        mapping = await self._repo.get(id)
        if not mapping:
            raise MappingNotFound(f"Mapping '{id}' not found")
        return mapping

    async def get_by_mapping_id(self, mapping_id: str) -> Mapping:
        mapping = await self._repo.get_by_mapping_id(mapping_id)
        if not mapping:
            raise MappingNotFound(f"Mapping '{mapping_id}' not found")
        return mapping

    async def list(
        self,
        *,
        q: str | None = None,
        source_format: str | None = None,
        target_schema: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Mapping], int]:
        skip = (page - 1) * page_size
        items, total = await self._repo.search(
            q=q, source_format=source_format, target_schema=target_schema,
            skip=skip, limit=page_size,
        )
        return list(items), total

    async def update(
        self, id: str, data: MappingUpdate, actor: str, actor_role: str | None
    ) -> Mapping:
        mapping = await self.get(id)
        before = self._snapshot(mapping)
        update_data: dict[str, Any] = data.model_dump(exclude_none=True)
        reason = update_data.pop("reason", None)
        update_data["updated_by"] = actor
        mapping = await self._repo.update(mapping, update_data)
        await self._repo.add_version(mapping, actor, reason)
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.MAPPING_UPDATED,
            resource_type="mapping", resource_id=mapping.mapping_id,
            before_state=before, after_state=self._snapshot(mapping), reason=reason,
        )
        return mapping

    @staticmethod
    def _snapshot(m: Mapping) -> dict[str, Any]:
        return {
            "mapping_id": m.mapping_id,
            "source_format": m.source_format,
            "target_schema": m.target_schema,
            "version": m.version,
        }
