"""Schema Registry service."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.audit_service import AuditService
from backend.app.core.exceptions import DuplicateError, SchemaNotFound
from backend.app.models.audit_log import AuditAction
from backend.app.models.schema import Schema, SchemaVersion
from backend.app.repositories.schema_repo import SchemaRepository
from backend.app.schemas.schema import SchemaCreate, SchemaVersionCreate


class SchemaRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = SchemaRepository(db)
        self._audit = AuditService(db)

    async def create(
        self, data: SchemaCreate, actor: str, actor_role: str | None
    ) -> Schema:
        if await self._repo.name_exists(data.name):
            raise DuplicateError(f"Schema '{data.name}' already exists")
        schema = Schema(name=data.name, description=data.description, created_by=actor)
        schema = await self._repo.create(schema)
        if data.initial_version:
            await self._repo.add_version(
                schema,
                version=data.initial_version.version,
                json_schema=data.initial_version.json_schema,
                changelog=data.initial_version.changelog,
                created_by=actor,
            )
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.SCHEMA_CREATED,
            resource_type="schema", resource_id=schema.name,
            after_state={"name": schema.name},
        )
        return await self._repo.get_by_name(data.name)  # type: ignore[return-value]

    async def add_version(
        self,
        name: str,
        data: SchemaVersionCreate,
        actor: str,
        actor_role: str | None,
    ) -> SchemaVersion:
        schema = await self._get_schema(name)
        sv = await self._repo.add_version(
            schema,
            version=data.version,
            json_schema=data.json_schema,
            changelog=data.changelog,
            created_by=actor,
        )
        await self._audit.record(
            actor=actor, actor_role=actor_role,
            action=AuditAction.SCHEMA_VERSION_ADDED,
            resource_type="schema", resource_id=name,
            version=data.version,
        )
        return sv

    async def get(self, name: str) -> Schema:
        return await self._get_schema(name)

    async def get_version(self, name: str, version: str) -> SchemaVersion:
        sv = await self._repo.get_version(name, version)
        if not sv:
            raise SchemaNotFound(f"Schema '{name}' version '{version}' not found")
        return sv

    async def list(self, *, page: int = 1, page_size: int = 20) -> tuple[list[Schema], int]:
        skip = (page - 1) * page_size
        items, total = await self._repo.list_schemas(skip=skip, limit=page_size)
        return list(items), total

    async def _get_schema(self, name: str) -> Schema:
        schema = await self._repo.get_by_name(name)
        if not schema:
            raise SchemaNotFound(f"Schema '{name}' not found")
        return schema
