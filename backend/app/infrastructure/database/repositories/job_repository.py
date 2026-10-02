"""Implementação SQLite/SQLAlchemy do IJobRepository."""
from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.entities import Job, JobParams, MediaFile, Segment, Transcription
from app.core.entities.media_file import MediaKind
from app.core.value_objects import JobStage, JobStatus, Language, ModelType
from app.infrastructure.database.models import (
    JobModel,
    MediaFileModel,
    SegmentModel,
    TranscriptionModel,
)


def _params_to_dict(p: JobParams) -> dict:
    d = asdict(p)
    d["output_formats"] = list(p.output_formats)
    return d


def _dict_to_params(d: dict | None) -> JobParams:
    if not d:
        return JobParams()
    return JobParams(
        model=ModelType(d.get("model", ModelType.DISTIL_LARGE_V3.value)),
        language=Language(d.get("language", Language.AUTO.value)),
        beam_size=int(d.get("beam_size", 5)),
        output_formats=tuple(d.get("output_formats", ("srt", "vtt", "txt", "md"))),
        audio_only=bool(d.get("audio_only", False)),
        keep_source_video=bool(d.get("keep_source_video", True)),
    )


def _model_to_entity(m: JobModel) -> Job:
    return Job(
        id=m.id,
        source_url=m.source_url,
        source_file=m.source_file,
        title=m.title,
        status=JobStatus(m.status),
        stage=JobStage(m.stage),
        progress=m.progress,
        message=m.message,
        error_message=m.error_message,
        params=_dict_to_params(m.params_json),
        metadata=dict(m.metadata_json or {}),
        created_at=m.created_at,
        started_at=m.started_at,
        finished_at=m.finished_at,
    )


class SQLAlchemyJobRepository:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sm = sessionmaker

    async def save(self, job: Job) -> None:
        async with self._sm() as s:
            existing = await s.get(JobModel, job.id)
            if existing is None:
                s.add(
                    JobModel(
                        id=job.id,
                        source_url=job.source_url,
                        source_file=job.source_file,
                        title=job.title,
                        status=job.status.value,
                        stage=job.stage.value,
                        progress=job.progress,
                        message=job.message,
                        error_message=job.error_message,
                        params_json=_params_to_dict(job.params),
                        metadata_json=job.metadata,
                        created_at=job.created_at,
                        started_at=job.started_at,
                        finished_at=job.finished_at,
                    )
                )
            else:
                existing.source_url = job.source_url
                existing.source_file = job.source_file
                existing.title = job.title
                existing.status = job.status.value
                existing.stage = job.stage.value
                existing.progress = job.progress
                existing.message = job.message
                existing.error_message = job.error_message
                existing.params_json = _params_to_dict(job.params)
                existing.metadata_json = job.metadata
                existing.started_at = job.started_at
                existing.finished_at = job.finished_at
            await s.commit()

    async def get(self, job_id: str) -> Job | None:
        async with self._sm() as s:
            m = await s.get(JobModel, job_id)
            return _model_to_entity(m) if m else None

    async def list(self, limit: int = 100, offset: int = 0) -> list[Job]:
        async with self._sm() as s:
            stmt = (
                select(JobModel)
                .order_by(JobModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            res = await s.execute(stmt)
            return [_model_to_entity(m) for m in res.scalars()]

    async def delete(self, job_id: str) -> bool:
        async with self._sm() as s:
            res = await s.execute(delete(JobModel).where(JobModel.id == job_id))
            await s.commit()
            return (res.rowcount or 0) > 0

    async def attach_media(self, job_id: str, media: MediaFile) -> None:
        async with self._sm() as s:
            s.add(
                MediaFileModel(
                    job_id=job_id,
                    kind=media.kind.value,
                    format=media.format,
                    path=str(media.path),
                    size_bytes=media.size_bytes,
                    duration_seconds=media.duration_seconds,
                )
            )
            await s.commit()

    async def list_media(self, job_id: str) -> list[MediaFile]:
        from pathlib import Path

        async with self._sm() as s:
            stmt = select(MediaFileModel).where(MediaFileModel.job_id == job_id)
            res = await s.execute(stmt)
            return [
                MediaFile(
                    path=Path(m.path),
                    kind=MediaKind(m.kind),
                    format=m.format,
                    size_bytes=m.size_bytes,
                    duration_seconds=m.duration_seconds,
                )
                for m in res.scalars()
            ]

    async def attach_transcription(self, job_id: str, tr: Transcription) -> None:
        async with self._sm() as s:
            existing = await s.execute(
                select(TranscriptionModel).where(TranscriptionModel.job_id == job_id)
            )
            row = existing.scalar_one_or_none()
            if row is not None:
                await s.execute(
                    delete(SegmentModel).where(SegmentModel.transcription_id == row.id)
                )
                await s.execute(
                    delete(TranscriptionModel).where(TranscriptionModel.id == row.id)
                )

            tr_model = TranscriptionModel(
                job_id=job_id,
                language_detected=tr.language_detected,
                language_probability=tr.language_probability,
                model_used=tr.model_used,
                duration_seconds=tr.duration_seconds,
            )
            s.add(tr_model)
            await s.flush()

            for seg in tr.segments:
                s.add(
                    SegmentModel(
                        transcription_id=tr_model.id,
                        idx=seg.index,
                        start_ms=seg.start_ms,
                        end_ms=seg.end_ms,
                        text=seg.text,
                        confidence=seg.confidence,
                        speaker_id=seg.speaker_id,
                    )
                )
            await s.commit()

    async def get_transcription(self, job_id: str) -> Transcription | None:
        async with self._sm() as s:
            res = await s.execute(
                select(TranscriptionModel).where(TranscriptionModel.job_id == job_id)
            )
            tr_model = res.scalar_one_or_none()
            if tr_model is None:
                return None
            seg_res = await s.execute(
                select(SegmentModel)
                .where(SegmentModel.transcription_id == tr_model.id)
                .order_by(SegmentModel.idx)
            )
            segments = [
                Segment(
                    index=r.idx,
                    start_ms=r.start_ms,
                    end_ms=r.end_ms,
                    text=r.text,
                    confidence=r.confidence,
                    speaker_id=r.speaker_id,
                )
                for r in seg_res.scalars()
            ]
            return Transcription(
                segments=segments,
                language_detected=tr_model.language_detected,
                language_probability=tr_model.language_probability,
                model_used=tr_model.model_used,
                duration_seconds=tr_model.duration_seconds,
            )
