"""Step: gera legendas nos formatos configurados."""
from __future__ import annotations

from app.application.orchestrator.context import JobContext
from app.application.progress.progress_reporter import ProgressReporter
from app.core.interfaces.subtitle_generator import ISubtitleGenerator
from app.core.value_objects import JobStage
from app.infrastructure.storage.path_resolver import PathResolver, slugify


class SubtitleStep:
    def __init__(self, generator: ISubtitleGenerator, paths: PathResolver) -> None:
        self._gen = generator
        self._paths = paths

    async def run(self, ctx: JobContext, reporter: ProgressReporter) -> JobContext:
        if ctx.transcription is None:
            return ctx

        await reporter.report(
            ctx.job, JobStage.GENERATING_SUBTITLES, 0.1, "Gerando arquivos de saída"
        )

        target = self._paths.job_subtitles_dir(ctx.job.id)
        base_name = slugify(ctx.job.title or ctx.job.id)

        outputs = await self._gen.generate(
            ctx.transcription,
            target,
            base_name,
            tuple(ctx.job.params.output_formats),
        )
        ctx.outputs.update(outputs)

        await reporter.report(
            ctx.job,
            JobStage.GENERATING_SUBTITLES,
            1.0,
            f"{len(outputs)} formatos gerados",
        )
        return ctx
