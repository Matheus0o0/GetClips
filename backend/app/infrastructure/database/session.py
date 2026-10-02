"""Sessão async do SQLAlchemy."""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.infrastructure.database.base import Base
# Importa os modelos para registrar no metadata
from app.infrastructure.database.models import (  # noqa: F401
    ClipModel,
    EditingTemplateModel,
    JobModel,
    MediaFileModel,
    SegmentModel,
    SettingModel,
    TranscriptionModel,
)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


async def init_db(settings: Settings) -> None:
    global _engine, _sessionmaker
    _engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )
    _sessionmaker = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("Banco não inicializado. Chame init_db() no lifespan.")
    return _sessionmaker


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def session_scope() -> AsyncIterator[AsyncSession]:
    sm = get_sessionmaker()
    async with sm() as session:
        yield session
