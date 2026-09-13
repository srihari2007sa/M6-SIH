"""Policy and PolicyVersion ORM models."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import AuditableMixin, Base


class Policy(AuditableMixin, Base):
    __tablename__ = "policies"

    policy_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    destinations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    versions: Mapped[list["PolicyVersion"]] = relationship(
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="PolicyVersion.created_at.desc()",
    )


class PolicyVersion(AuditableMixin, Base):
    __tablename__ = "policy_versions"

    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    conditions_snapshot: Mapped[list] = mapped_column(JSON, nullable=False)
    destinations_snapshot: Mapped[list] = mapped_column(JSON, nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    policy: Mapped[Policy] = relationship(back_populates="versions")
