"""Policy management service."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.audit_service import AuditService
from backend.app.core.exceptions import DuplicateError, PolicyNotFound
from backend.app.models.audit_log import AuditAction
from backend.app.models.policy import Policy
from backend.app.repositories.policy_repo import PolicyRepository
from backend.app.schemas.policy import PolicyCreate, PolicyUpdate


class PolicyRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = PolicyRepository(db)
        self._audit = AuditService(db)

    async def create(
        self, data: PolicyCreate, actor: str, actor_role: str | None
    ) -> Policy:
        if await self._repo.policy_id_exists(data.policy_id):
            raise DuplicateError(f"Policy '{data.policy_id}' already exists")
        conds = [c.model_dump() for c in data.conditions]
        policy = Policy(
            policy_id=data.policy_id,
            name=data.name,
            version=data.version,
            priority=data.priority,
            conditions=conds,
            destinations=data.destinations,
            is_enabled=data.is_enabled,
            description=data.description,
            created_by=actor,
            updated_by=actor,
        )
        policy = await self._repo.create(policy)
        await self._repo.add_version(policy, actor, "Initial version")
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.POLICY_CREATED,
            resource_type="policy", resource_id=policy.policy_id,
            version=policy.version, after_state=self._snapshot(policy),
        )
        return policy

    async def get(self, id: str) -> Policy:
        policy = await self._repo.get(id)
        if not policy:
            raise PolicyNotFound(f"Policy '{id}' not found")
        return policy

    async def get_by_policy_id(self, policy_id: str) -> Policy:
        policy = await self._repo.get_by_policy_id(policy_id)
        if not policy:
            raise PolicyNotFound(f"Policy '{policy_id}' not found")
        return policy

    async def list(
        self,
        *,
        q: str | None = None,
        is_enabled: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Policy], int]:
        skip = (page - 1) * page_size
        items, total = await self._repo.search(
            q=q, is_enabled=is_enabled, skip=skip, limit=page_size
        )
        return list(items), total

    async def update(
        self, id: str, data: PolicyUpdate, actor: str, actor_role: str | None
    ) -> Policy:
        policy = await self.get(id)
        before = self._snapshot(policy)
        update_data: dict[str, Any] = data.model_dump(exclude_none=True)
        reason = update_data.pop("reason", None)
        if "conditions" in update_data:
            update_data["conditions"] = [
                c.model_dump() if hasattr(c, "model_dump") else c
                for c in update_data["conditions"]
            ]
        update_data["updated_by"] = actor
        policy = await self._repo.update(policy, update_data)
        await self._repo.add_version(policy, actor, reason)
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.POLICY_UPDATED,
            resource_type="policy", resource_id=policy.policy_id,
            version=policy.version, before_state=before,
            after_state=self._snapshot(policy), reason=reason,
        )
        return policy

    async def enable(self, id: str, actor: str, actor_role: str | None) -> Policy:
        policy = await self.get(id)
        policy.is_enabled = True
        policy.updated_by = actor
        await self._repo._db.flush()
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.POLICY_ENABLED,
            resource_type="policy", resource_id=policy.policy_id,
        )
        return policy

    async def disable(self, id: str, actor: str, actor_role: str | None) -> Policy:
        policy = await self.get(id)
        policy.is_enabled = False
        policy.updated_by = actor
        await self._repo._db.flush()
        await self._audit.record(
            actor=actor, actor_role=actor_role, action=AuditAction.POLICY_DISABLED,
            resource_type="policy", resource_id=policy.policy_id,
        )
        return policy

    @staticmethod
    def _snapshot(p: Policy) -> dict[str, Any]:
        return {
            "policy_id": p.policy_id,
            "name": p.name,
            "version": p.version,
            "priority": p.priority,
            "is_enabled": p.is_enabled,
            "destinations": p.destinations,
        }
