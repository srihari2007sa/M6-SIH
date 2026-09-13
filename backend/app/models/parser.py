"""Parser and ParserVersion ORM models."""
from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import AuditableMixin, Base


class ParserStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    ROLLED_BACK = "ROLLED_BACK"


# Valid state-machine transitions
PARSER_TRANSITIONS: dict[ParserStatus, list[ParserStatus]] = {
    ParserStatus.DRAFT: [ParserStatus.PENDING_APPROVAL],
    ParserStatus.PENDING_APPROVAL: [ParserStatus.APPROVED, ParserStatus.DRAFT],
    ParserStatus.APPROVED: [ParserStatus.ACTIVE],
    ParserStatus.ACTIVE: [ParserStatus.DISABLED, ParserStatus.ROLLED_BACK],
    ParserStatus.ROLLED_BACK: [ParserStatus.ACTIVE],
    ParserStatus.DISABLED: [ParserStatus.ACTIVE],
}


class Parser(AuditableMixin, Base):
    __tablename__ = "parsers"

    parser_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor: Mapped[str] = mapped_column(String(128), nullable=False)
    product: Mapped[str] = mapped_column(String(128), nullable=False)
    format: Mapped[str] = mapped_column(String(64), nullable=False)        # e.g. syslog, cef
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    status: Mapped[ParserStatus] = mapped_column(
        Enum(ParserStatus, name="parser_status", native_enum=False),
        default=ParserStatus.DRAFT,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    versions: Mapped[list["ParserVersion"]] = relationship(
        back_populates="parser",
        cascade="all, delete-orphan",
        order_by="ParserVersion.created_at.desc()",
    )


class ParserVersion(AuditableMixin, Base):
    __tablename__ = "parser_versions"

    parser_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parsers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[ParserStatus] = mapped_column(
        Enum(ParserStatus, name="parser_status", native_enum=False), nullable=False
    )
    changed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # parser state at this version

    parser: Mapped[Parser] = relationship(back_populates="versions")
