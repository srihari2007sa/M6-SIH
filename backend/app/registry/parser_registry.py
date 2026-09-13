"""Parser Registry service — enforces lifecycle state machine."""
from __future__ import annotations

import json
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.audit_service import AuditService
from backend.app.core.exceptions import DuplicateError, InvalidStateTransition, ParserNotFound
from backend.app.models.audit_log import AuditAction
from backend.app.models.parser import (
    Parser,
    ParserStatus,
    ParserVersion,
    PARSER_TRANSITIONS,
)
from backend.app.repositories.parser_repo import ParserRepository
from backend.app.schemas.parser import ParserCreate, ParserUpdate


class ParserRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = ParserRepository(db)
        self._audit = AuditService(db)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _assert_transition(self, parser: Parser, target: ParserStatus) -> None:
        allowed = PARSER_TRANSITIONS.get(parser.status, [])
        if target not in allowed:
            raise InvalidStateTransition(
                f"Cannot transition parser '{parser.parser_id}' "
                f"from {parser.status.value} to {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

    @staticmethod
    def _snapshot(p: Parser) -> dict[str, Any]:
        return {
            "parser_id": p.parser_id,
            "name": p.name,
            "status": p.status.value,
            "version": p.version,
        }

    async def _transition(
        self,
        id: str,
        target: ParserStatus,
        action: AuditAction,
        actor: str,
        actor_role: str | None,
        reason: str | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> Parser:
        parser = await self.get(id)
        self._assert_transition(parser, target)
        before = self._snapshot(parser)
        parser.status = target
        if extra_fields:
            for k, v in extra_fields.items():
                setattr(parser, k, v)
        await self._repo._db.flush()
        await self._repo.add_version(parser, actor, reason)
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=action,
            resource_type="parser", resource_id=parser.parser_id,
            version=parser.version,
            before_state=before, after_state=self._snapshot(parser),
            reason=reason,
        )
        return parser

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def register(
        self, data: ParserCreate, actor: str, actor_role: str | None
    ) -> Parser:
        if await self._repo.parser_id_exists(data.parser_id):
            raise DuplicateError(f"Parser '{data.parser_id}' already exists")
        tags_str = json.dumps(data.tags) if data.tags else None
        parser = Parser(
            parser_id=data.parser_id,
            name=data.name,
            vendor=data.vendor,
            product=data.product,
            format=data.format,
            version=data.version,
            status=ParserStatus.DRAFT,
            description=data.description,
            tags=tags_str,
            created_by=actor,
            updated_by=actor,
        )
        parser = await self._repo.create(parser)
        await self._repo.add_version(parser, actor, "Initial registration")
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.PARSER_REGISTERED,
            resource_type="parser", resource_id=parser.parser_id,
            version=parser.version, after_state=self._snapshot(parser),
        )
        return parser

    async def get(self, id: str) -> Parser:
        parser = await self._repo.get(id)
        if not parser:
            raise ParserNotFound(f"Parser '{id}' not found")
        return parser

    async def get_by_parser_id(self, parser_id: str) -> Parser:
        parser = await self._repo.get_by_parser_id(parser_id)
        if not parser:
            raise ParserNotFound(f"Parser '{parser_id}' not found")
        return parser

    async def list(
        self,
        *,
        q: str | None = None,
        status: ParserStatus | None = None,
        vendor: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Parser], int]:
        skip = (page - 1) * page_size
        items, total = await self._repo.search(
            q=q, status=status, vendor=vendor, skip=skip, limit=page_size
        )
        return list(items), total

    async def update(
        self, id: str, data: ParserUpdate, actor: str, actor_role: str | None
    ) -> Parser:
        parser = await self.get(id)
        before = self._snapshot(parser)
        update_data: dict[str, Any] = data.model_dump(exclude_none=True)
        if "tags" in update_data:
            update_data["tags"] = json.dumps(update_data["tags"])
        update_data["updated_by"] = actor
        parser = await self._repo.update(parser, update_data)
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.PARSER_UPDATED,
            resource_type="parser", resource_id=parser.parser_id,
            before_state=before, after_state=self._snapshot(parser),
        )
        return parser

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def submit(
        self, id: str, actor: str, actor_role: str | None, reason: str | None = None
    ) -> Parser:
        return await self._transition(
            id, ParserStatus.PENDING_APPROVAL,
            AuditAction.PARSER_SUBMITTED, actor, actor_role, reason
        )

    async def approve(
        self, id: str, actor: str, actor_role: str | None, reason: str | None = None
    ) -> Parser:
        return await self._transition(
            id, ParserStatus.APPROVED,
            AuditAction.PARSER_APPROVED, actor, actor_role, reason,
            extra_fields={"approved_by": actor},
        )

    async def activate(
        self, id: str, actor: str, actor_role: str | None, reason: str | None = None
    ) -> Parser:
        return await self._transition(
            id, ParserStatus.ACTIVE,
            AuditAction.PARSER_ACTIVATED, actor, actor_role, reason
        )

    async def disable(
        self, id: str, actor: str, actor_role: str | None, reason: str | None = None
    ) -> Parser:
        return await self._transition(
            id, ParserStatus.DISABLED,
            AuditAction.PARSER_DISABLED, actor, actor_role, reason
        )

    async def rollback(
        self, id: str, actor: str, actor_role: str | None, reason: str | None = None
    ) -> Parser:
        return await self._transition(
            id, ParserStatus.ROLLED_BACK,
            AuditAction.PARSER_ROLLED_BACK, actor, actor_role, reason
        )

    async def get_history(self, id: str) -> Sequence[ParserVersion]:
        parser = await self.get(id)
        return await self._repo.get_versions(parser.id)
