"""AuditLog ORM model — append-only audit trail."""
from __future__ import annotations

import enum

from sqlalchemy import DateTime, Enum, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import UTC, datetime

from backend.app.db.base import UUIDMixin, Base


class AuditAction(str, enum.Enum):
    # Sources
    SOURCE_CREATED = "SOURCE_CREATED"
    SOURCE_UPDATED = "SOURCE_UPDATED"
    SOURCE_ENABLED = "SOURCE_ENABLED"
    SOURCE_DISABLED = "SOURCE_DISABLED"
    SOURCE_DELETED = "SOURCE_DELETED"
    # Parsers
    PARSER_REGISTERED = "PARSER_REGISTERED"
    PARSER_SUBMITTED = "PARSER_SUBMITTED"
    PARSER_APPROVED = "PARSER_APPROVED"
    PARSER_REJECTED = "PARSER_REJECTED"
    PARSER_ACTIVATED = "PARSER_ACTIVATED"
    PARSER_DISABLED = "PARSER_DISABLED"
    PARSER_ROLLED_BACK = "PARSER_ROLLED_BACK"
    PARSER_UPDATED = "PARSER_UPDATED"
    # Schemas
    SCHEMA_CREATED = "SCHEMA_CREATED"
    SCHEMA_VERSION_ADDED = "SCHEMA_VERSION_ADDED"
    # Mappings
    MAPPING_CREATED = "MAPPING_CREATED"
    MAPPING_UPDATED = "MAPPING_UPDATED"
    # Policies
    POLICY_CREATED = "POLICY_CREATED"
    POLICY_UPDATED = "POLICY_UPDATED"
    POLICY_ENABLED = "POLICY_ENABLED"
    POLICY_DISABLED = "POLICY_DISABLED"
    # Configuration
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"
    CONFIGURATION_DISTRIBUTED = "CONFIGURATION_DISTRIBUTED"
    # Replay
    REPLAY_REQUESTED = "REPLAY_REQUESTED"
    REPLAY_QUEUED = "REPLAY_QUEUED"
    REPLAY_COMPLETED = "REPLAY_COMPLETED"
    REPLAY_FAILED = "REPLAY_FAILED"
    # Auth
    USER_LOGIN = "USER_LOGIN"
    USER_CREATED = "USER_CREATED"
    USER_ROLE_ASSIGNED = "USER_ROLE_ASSIGNED"


class AuditResult(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"


class AuditLog(UUIDMixin, Base):
    """
    Append-only audit log. Never update or delete rows.
    Uses its own timestamp so it differs from AuditableMixin.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_actor", "actor"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_timestamp", "timestamp"),
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[AuditResult] = mapped_column(
        Enum(AuditResult, name="audit_result"),
        default=AuditResult.SUCCESS,
        nullable=False,
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
