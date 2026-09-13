"""Parser repository."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.parser import Parser, ParserStatus, ParserVersion
from backend.app.repositories.base import BaseRepository


class ParserRepository(BaseRepository[Parser]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Parser, db)

    async def get_by_parser_id(self, parser_id: str) -> Parser | None:
        stmt = (
            select(Parser)
            .options(selectinload(Parser.versions))
            .where(Parser.parser_id == parser_id)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def get_with_versions(self, id: str) -> Parser | None:
        stmt = (
            select(Parser)
            .options(selectinload(Parser.versions))
            .where(Parser.id == id)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def search(
        self,
        *,
        q: str | None = None,
        status: ParserStatus | None = None,
        vendor: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Parser], int]:
        stmt = select(Parser)
        filters = []
        if q:
            filters.append(
                or_(
                    Parser.name.ilike(f"%{q}%"),
                    Parser.parser_id.ilike(f"%{q}%"),
                )
            )
        if status:
            filters.append(Parser.status == status)
        if vendor:
            filters.append(Parser.vendor.ilike(f"%{vendor}%"))
        if filters:
            stmt = stmt.where(*filters)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._db.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(skip).limit(limit).order_by(Parser.created_at.desc())
        items = (await self._db.execute(stmt)).scalars().all()
        return items, total

    async def add_version(
        self,
        parser: Parser,
        changed_by: str | None,
        reason: str | None,
    ) -> ParserVersion:
        import dataclasses
        snapshot = {
            "parser_id": parser.parser_id,
            "name": parser.name,
            "vendor": parser.vendor,
            "product": parser.product,
            "format": parser.format,
            "version": parser.version,
            "status": parser.status.value,
        }
        pv = ParserVersion(
            parser_id=parser.id,
            version=parser.version,
            status=parser.status,
            changed_by=changed_by,
            reason=reason,
            snapshot=snapshot,
        )
        self._db.add(pv)
        await self._db.flush()
        return pv

    async def get_versions(self, parser_db_id: str) -> Sequence[ParserVersion]:
        stmt = (
            select(ParserVersion)
            .where(ParserVersion.parser_id == parser_db_id)
            .order_by(ParserVersion.created_at.desc())
        )
        return (await self._db.execute(stmt)).scalars().all()

    async def parser_id_exists(self, parser_id: str) -> bool:
        stmt = select(func.count()).where(Parser.parser_id == parser_id)
        return (await self._db.execute(stmt)).scalar_one() > 0
