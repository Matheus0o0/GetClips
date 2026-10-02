"""Implementação SQLAlchemy do IClipRepository."""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.entities.clip import Clip, ClipStatus, CropMode
from app.infrastructure.database.models import ClipModel


def _to_entity(m: ClipModel) -> Clip:
    return Clip(
        id=m.id,
        job_id=m.job_id,
        inicio=m.inicio,
        fim=m.fim,
        hook_text=m.hook_text,
        score=m.score,
        motivo=m.motivo,
        crop_mode=CropMode(m.crop_mode),
        status=ClipStatus(m.status),
        output_path=m.output_path,
        error_message=m.error_message,
        progress=m.progress,
        created_at=m.created_at,
        template_id=m.template_id,
    )


class SQLAlchemyClipRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def save(self, clip: Clip) -> None:
        async with self._sm() as s:
            existing = await s.get(ClipModel, clip.id)
            if existing is None:
                s.add(
                    ClipModel(
                        id=clip.id,
                        job_id=clip.job_id,
                        inicio=clip.inicio,
                        fim=clip.fim,
                        hook_text=clip.hook_text,
                        score=clip.score,
                        motivo=clip.motivo,
                        crop_mode=clip.crop_mode.value,
                        status=clip.status.value,
                        output_path=clip.output_path,
                        error_message=clip.error_message,
                        progress=clip.progress,
                        created_at=clip.created_at,
                        template_id=clip.template_id,
                    )
                )
            else:
                existing.inicio = clip.inicio
                existing.fim = clip.fim
                existing.hook_text = clip.hook_text
                existing.score = clip.score
                existing.motivo = clip.motivo
                existing.crop_mode = clip.crop_mode.value
                existing.status = clip.status.value
                existing.output_path = clip.output_path
                existing.error_message = clip.error_message
                existing.progress = clip.progress
                existing.template_id = clip.template_id
            await s.commit()

    async def get(self, clip_id: str) -> Clip | None:
        async with self._sm() as s:
            m = await s.get(ClipModel, clip_id)
            return _to_entity(m) if m else None

    async def list_by_job(self, job_id: str) -> list[Clip]:
        async with self._sm() as s:
            stmt = (
                select(ClipModel)
                .where(ClipModel.job_id == job_id)
                .order_by(ClipModel.created_at.asc())
            )
            res = await s.execute(stmt)
            return [_to_entity(m) for m in res.scalars()]

    async def delete(self, clip_id: str) -> bool:
        async with self._sm() as s:
            res = await s.execute(delete(ClipModel).where(ClipModel.id == clip_id))
            await s.commit()
            return (res.rowcount or 0) > 0
