"""Repositório SQLAlchemy para EditingTemplate."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import TemplateNotFoundError
from app.editing.templates.model import EditingTemplateConfig
from app.infrastructure.database.models.editing_template import EditingTemplateModel


class SQLAlchemyTemplateRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def list_all(self) -> list[EditingTemplateModel]:
        async with self._sm() as session:
            result = await session.execute(
                select(EditingTemplateModel).order_by(
                    EditingTemplateModel.is_default.desc(),
                    EditingTemplateModel.created_at.desc(),
                )
            )
            return list(result.scalars().all())

    async def get(self, template_id: str) -> EditingTemplateModel:
        async with self._sm() as session:
            row = await session.get(EditingTemplateModel, template_id)
        if row is None:
            raise TemplateNotFoundError(template_id)
        return row

    async def create(self, name: str, config: EditingTemplateConfig) -> EditingTemplateModel:
        now = datetime.now(timezone.utc)
        row = EditingTemplateModel(
            id=uuid4().hex,
            name=name,
            is_default=False,
            config_json=config.model_dump_json(),
            created_at=now,
            updated_at=now,
        )
        async with self._sm() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return row

    async def update(
        self,
        template_id: str,
        name: str | None,
        config: EditingTemplateConfig | None,
    ) -> EditingTemplateModel:
        row = await self.get(template_id)
        async with self._sm() as session:
            values: dict = {"updated_at": datetime.now(timezone.utc)}
            if name is not None:
                values["name"] = name
            if config is not None:
                values["config_json"] = config.model_dump_json()
            await session.execute(
                update(EditingTemplateModel)
                .where(EditingTemplateModel.id == template_id)
                .values(**values)
            )
            await session.commit()
        return await self.get(template_id)

    async def delete(self, template_id: str) -> None:
        await self.get(template_id)  # raises if not found
        async with self._sm() as session:
            row = await session.get(EditingTemplateModel, template_id)
            if row:
                await session.delete(row)
                await session.commit()

    async def set_default(self, template_id: str) -> EditingTemplateModel:
        await self.get(template_id)  # raises if not found
        now = datetime.now(timezone.utc)
        async with self._sm() as session:
            # limpa todos os defaults
            await session.execute(
                update(EditingTemplateModel).values(is_default=False, updated_at=now)
            )
            # marca o novo
            await session.execute(
                update(EditingTemplateModel)
                .where(EditingTemplateModel.id == template_id)
                .values(is_default=True, updated_at=now)
            )
            await session.commit()
        return await self.get(template_id)

    async def get_default(self) -> EditingTemplateModel | None:
        async with self._sm() as session:
            result = await session.execute(
                select(EditingTemplateModel).where(EditingTemplateModel.is_default.is_(True))
            )
            return result.scalars().first()

    @staticmethod
    def config_from_row(row: EditingTemplateModel) -> EditingTemplateConfig:
        return EditingTemplateConfig.model_validate(json.loads(row.config_json))
