"""Step: baixa o vídeo/áudio da fonte."""
from __future__ import annotations

from app.application.orchestrator.context import JobContext
from app.application.progress.progress_reporter import ProgressReporter
from app.core.exceptions import UnsupportedSourceError
from app.core.interfaces.downloader import IDownloader
from app.core.value_objects import JobStage
from app.infrastructure.storage.path_resolver import PathResolver


class DownloadStep:
    def __init__(self, downloaders: list[IDownloader], paths: PathResolver) -> None:
        self._downloaders = downloaders
        self._paths = paths

    async def run(self, ctx: JobContext, reporter: ProgressReporter) -> JobContext:
        source = ctx.job.source_url or ctx.job.source_file
        if not source:
            raise UnsupportedSourceError("Job sem source_url nem source_file")

        downloader: IDownloader | None = None
        for d in self._downloaders:
            if await d.can_handle(source):
                downloader = d
                break

        if downloader is None:
            raise UnsupportedSourceError(f"Nenhum downloader aceita: {source}")

        output_dir = self._paths.job_download_dir(ctx.job.id)

        async def progress(p: float, msg: str) -> None:
            await reporter.report(ctx.job, JobStage.DOWNLOADING, p, msg)

        await reporter.report(ctx.job, JobStage.DOWNLOADING, 0.0, "Iniciando download")

        result = await downloader.download(
            source, output_dir, audio_only=ctx.job.params.audio_only, on_progress=progress
        )

        ctx.downloaded_file = result.file_path
        ctx.download_metadata = result.metadata

        if result.metadata.title:
            ctx.job.title = result.metadata.title
            ctx.job.metadata["title"] = result.metadata.title
        if result.metadata.platform:
            ctx.job.metadata["platform"] = result.metadata.platform
        if result.metadata.duration_seconds:
            ctx.job.metadata["duration_seconds"] = result.metadata.duration_seconds

        await reporter.report(ctx.job, JobStage.DOWNLOADING, 1.0, "Download concluído")
        return ctx
