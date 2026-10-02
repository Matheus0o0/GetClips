"""Step: persiste arquivos e transcrição no banco."""
from __future__ import annotations

from app.application.orchestrator.context import JobContext
from app.application.progress.progress_reporter import ProgressReporter
from app.core.entities.media_file import MediaFile, MediaKind
from app.core.interfaces.job_repository import IJobRepository
from app.core.value_objects import JobStage
from app.infrastructure.storage.file_system import file_size


class FinalizeStep:
    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    async def run(self, ctx: JobContext, reporter: ProgressReporter) -> JobContext:
        await reporter.report(ctx.job, JobStage.FINALIZING, 0.2, "Registrando saídas")

        if ctx.downloaded_file:
            await self._repo.attach_media(
                ctx.job.id,
                MediaFile(
                    path=ctx.downloaded_file,
                    kind=MediaKind.ORIGINAL_VIDEO,
                    format=ctx.downloaded_file.suffix.lstrip("."),
                    size_bytes=file_size(ctx.downloaded_file),
                ),
            )

        if ctx.audio_path:
            await self._repo.attach_media(
                ctx.job.id,
                MediaFile(
                    path=ctx.audio_path,
                    kind=MediaKind.PROCESSED_AUDIO,
                    format=ctx.audio_path.suffix.lstrip("."),
                    size_bytes=file_size(ctx.audio_path),
                ),
            )

        for fmt, path in ctx.outputs.items():
            kind = MediaKind.SUBTITLE if fmt in {"srt", "vtt", "ass"} else MediaKind.TRANSCRIPT
            await self._repo.attach_media(
                ctx.job.id,
                MediaFile(
                    path=path,
                    kind=kind,
                    format=fmt,
                    size_bytes=file_size(path),
                ),
            )

        if ctx.transcription:
            await self._repo.attach_transcription(ctx.job.id, ctx.transcription)

        await reporter.report(ctx.job, JobStage.FINALIZING, 1.0, "Concluído")
        return ctx
