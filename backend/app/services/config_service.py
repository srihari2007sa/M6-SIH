"""
Configuration Distribution Service.

Architecture:
  PostgreSQL (source of truth)
      ↓ M6 validates + persists
      ↓ writes to Redis
      ↓ publishes Kafka message (if enabled)
      ← M1–M5 read from Redis

Redis key namespace:
  config:sources        – active sources JSON
  config:parsers        – active parsers JSON
  config:schemas        – schema name→version→json_schema
  config:mappings       – active mappings JSON
  config:policies       – active (enabled) policies JSON
  config:version        – monotonic integer version
  config:updated_at     – ISO-8601 timestamp
"""
from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.audit_service import AuditService
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.integrations.redis_client import get_redis_client
from backend.app.models.audit_log import AuditAction
from backend.app.models.config_version import ConfigDistributionStatus, ConfigurationVersion
from backend.app.models.mapping import Mapping
from backend.app.models.parser import Parser, ParserStatus
from backend.app.models.policy import Policy
from backend.app.models.schema import Schema
from backend.app.models.source import Source, SourceStatus

logger = get_logger("config_service")

# Redis key prefix
_REDIS_NS = "config"
_VERSION_KEY = f"{_REDIS_NS}:version"
_UPDATED_AT_KEY = f"{_REDIS_NS}:updated_at"


class ConfigDistributionService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()

    # ── Public: distribute a specific config key ───────────────────────────────

    async def distribute_sources(self, actor: str, actor_role: str | None) -> int:
        payload = await self._build_sources()
        return await self._publish("sources", payload, actor, actor_role)

    async def distribute_parsers(self, actor: str, actor_role: str | None) -> int:
        payload = await self._build_parsers()
        return await self._publish("parsers", payload, actor, actor_role)

    async def distribute_schemas(self, actor: str, actor_role: str | None) -> int:
        payload = await self._build_schemas()
        return await self._publish("schemas", payload, actor, actor_role)

    async def distribute_mappings(self, actor: str, actor_role: str | None) -> int:
        payload = await self._build_mappings()
        return await self._publish("mappings", payload, actor, actor_role)

    async def distribute_policies(self, actor: str, actor_role: str | None) -> int:
        payload = await self._build_policies()
        return await self._publish("policies", payload, actor, actor_role)

    async def distribute_all(self, actor: str, actor_role: str | None) -> dict[str, int]:
        """Distribute every config key and return version per key."""
        results: dict[str, int] = {}
        for key, builder in [
            ("sources",  self._build_sources),
            ("parsers",  self._build_parsers),
            ("schemas",  self._build_schemas),
            ("mappings", self._build_mappings),
            ("policies", self._build_policies),
        ]:
            payload = await builder()
            version = await self._publish(key, payload, actor, actor_role)
            results[key] = version
        return results

    # ── Public: read current config from Redis ────────────────────────────────

    async def get_current_config(self) -> dict[str, Any]:
        try:
            redis = await get_redis_client()
            keys = ["sources", "parsers", "schemas", "mappings", "policies"]
            result: dict[str, Any] = {}
            for key in keys:
                raw = await redis.get(f"{_REDIS_NS}:{key}")
                result[key] = json.loads(raw) if raw else None
            result["version"] = await redis.get(_VERSION_KEY)
            result["updated_at"] = await redis.get(_UPDATED_AT_KEY)
            return result
        except Exception as exc:
            logger.warning("Could not read config from Redis", error=str(exc))
            return {"error": str(exc), "available": False}

    async def get_config_version(self) -> int:
        try:
            redis = await get_redis_client()
            v = await redis.get(_VERSION_KEY)
            return int(v) if v else 0
        except Exception:
            return 0

    # ── Internal builders ─────────────────────────────────────────────────────

    async def _build_sources(self) -> list[dict[str, Any]]:
        stmt = select(Source).where(Source.status == SourceStatus.ACTIVE)
        rows = (await self._db.execute(stmt)).scalars().all()
        return [
            {
                "source_id": s.source_id,
                "tenant_id": s.tenant_id,
                "name": s.name,
                "vendor": s.vendor,
                "product": s.product,
                "type": s.source_type,
                "protocol": s.protocol,
                "transport": s.transport,
                "port": s.port,
                "zone": s.zone,
                "parser_id": s.parser_id,
            }
            for s in rows
        ]

    async def _build_parsers(self) -> list[dict[str, Any]]:
        stmt = select(Parser).where(Parser.status == ParserStatus.ACTIVE)
        rows = (await self._db.execute(stmt)).scalars().all()
        return [
            {
                "parser_id": p.parser_id,
                "name": p.name,
                "vendor": p.vendor,
                "product": p.product,
                "format": p.format,
                "version": p.version,
            }
            for p in rows
        ]

    async def _build_schemas(self) -> dict[str, Any]:
        from backend.app.models.schema import SchemaVersion, SchemaStatus
        from sqlalchemy.orm import selectinload
        stmt = select(Schema).options(selectinload(Schema.versions))
        rows = (await self._db.execute(stmt)).scalars().all()
        result: dict[str, Any] = {}
        for schema in rows:
            result[schema.name] = {}
            for sv in schema.versions:
                if sv.status == SchemaStatus.ACTIVE:
                    result[schema.name][sv.version] = sv.json_schema
        return result

    async def _build_mappings(self) -> list[dict[str, Any]]:
        stmt = select(Mapping).where(Mapping.is_active.is_(True))
        rows = (await self._db.execute(stmt)).scalars().all()
        return [
            {
                "mapping_id": m.mapping_id,
                "source_format": m.source_format,
                "target_schema": m.target_schema,
                "target_version": m.target_version,
                "version": m.version,
                "fields": m.fields,
            }
            for m in rows
        ]

    async def _build_policies(self) -> list[dict[str, Any]]:
        stmt = select(Policy).where(Policy.is_enabled.is_(True)).order_by(
            Policy.priority.desc()
        )
        rows = (await self._db.execute(stmt)).scalars().all()
        return [
            {
                "policy_id": p.policy_id,
                "name": p.name,
                "version": p.version,
                "priority": p.priority,
                "conditions": p.conditions,
                "destinations": p.destinations,
            }
            for p in rows
        ]

    # ── Internal: publish to Redis + persist version ──────────────────────────

    async def _publish(
        self,
        config_key: str,
        payload: Any,
        actor: str,
        actor_role: str | None,
    ) -> int:
        redis_key = f"{_REDIS_NS}:{config_key}"
        serialised = json.dumps(payload, default=str)
        version = int(time.time_ns() // 1_000_000)   # millisecond timestamp as version

        # Persist version record
        cv = ConfigurationVersion(
            version=version,
            config_key=config_key,
            payload=payload if isinstance(payload, dict) else {"items": payload},
            status=ConfigDistributionStatus.PENDING,
            distributed_by=actor,
            redis_key=redis_key,
        )
        self._db.add(cv)
        await self._db.flush()

        try:
            redis = await get_redis_client()
            ttl = self._settings.redis_config_ttl_seconds
            pipe = redis.pipeline()
            pipe.set(redis_key, serialised, ex=ttl if ttl > 0 else None)
            pipe.set(_VERSION_KEY, str(version))
            pipe.set(_UPDATED_AT_KEY, datetime.now(UTC).isoformat())
            await pipe.execute()

            cv.status = ConfigDistributionStatus.DISTRIBUTED
            await self._db.flush()

            # Kafka publish (fire-and-forget, non-blocking)
            if self._settings.kafka_enabled:
                await self._publish_kafka_event(config_key, version)

            audit = AuditService(self._db)
            await audit.record(
                actor=actor,
                actor_role=actor_role,
                action=AuditAction.CONFIGURATION_DISTRIBUTED,
                resource_type="config",
                resource_id=config_key,
                version=str(version),
                after_state={"redis_key": redis_key, "version": version},
            )

            logger.info(
                "Config distributed",
                key=config_key,
                version=version,
                redis_key=redis_key,
            )
        except Exception as exc:
            cv.status = ConfigDistributionStatus.FAILED
            cv.error_message = str(exc)
            await self._db.flush()
            logger.error("Config distribution failed", key=config_key, error=str(exc))
            raise

        return version

    async def _publish_kafka_event(self, config_key: str, version: int) -> None:
        """Publish a config-change notification to Kafka (best-effort)."""
        try:
            from backend.app.integrations.kafka_client import get_kafka_producer
            producer = await get_kafka_producer()
            if producer is None:
                return
            message = json.dumps({
                "event": "config_updated",
                "config_key": config_key,
                "version": version,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            topic = self._settings.kafka_config_topic
            await producer.publish(topic, message)
        except Exception as exc:
            # Kafka publish failure is non-fatal for config distribution
            logger.warning(
                "Kafka config-change publish failed (non-fatal)",
                error=str(exc),
            )
