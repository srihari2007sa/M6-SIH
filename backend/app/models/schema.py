"""Schema and SchemaVersion ORM models."""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import AuditableMixin, Base


class SchemaStatus(str, enum.Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class Schema(AuditableMixin, Base):
    __tablename__ = "schemas"

    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    versions: Mapped[list["SchemaVersion"]] = relationship(
        back_populates="schema",
        cascade="all, delete-orphan",
        order_by="SchemaVersion.created_at.desc()",
    )


class SchemaVersion(AuditableMixin, Base):
    __tablename__ = "schema_versions"

    schema_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schemas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[SchemaStatus] = mapped_column(
        Enum(SchemaStatus, name="schema_status", native_enum=False),
        default=SchemaStatus.ACTIVE,
        nullable=False,
    )
    json_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    schema: Mapped[Schema] = relationship(back_populates="versions")
