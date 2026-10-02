"""Step: transcreve usando ITranscriber."""
from __future__ import annotations

from app.application.orchestrator.context import JobContext
from app.application.progress.progress_reporter import ProgressReporter
from app.core.exceptions import TranscriptionError
from app.core.interfaces.transcriber import ITranscriber, TranscriptionParams
from app.core.value_objects import JobStage


class TranscribeStep:
    def __init__(self, transcriber: ITranscriber) -> None:
        self._transcriber = transcriber

    async def run(self, ctx: JobContext, reporter: ProgressReporter) -> JobContext:
        if ctx.audio_path is None:
            raise TranscriptionError("Sem áudio para transcrever")

        params = TranscriptionParams(
            model=ctx.job.params.model,
            language=ctx.job.params.language,
            beam_size=ctx.job.params.beam_size,
        )

        async def progress(p: float, msg: str) -> None:
            await reporter.report(ctx.job, JobStage.TRANSCRIBING, p, msg)

        await reporter.report(ctx.job, JobStage.TRANSCRIBING, 0.0, "Carregando modelo")
        tr = await self._transcriber.transcribe(ctx.audio_path, params, on_progress=progress)
        ctx.transcription = tr

        await reporter.report(
            ctx.job,
            JobStage.TRANSCRIBING,
            1.0,
            f"{len(tr.segments)} segmentos ({tr.language_detected})",
        )
        return ctx
