"""Step: extrai áudio WAV 16 kHz mono."""
from __future__ import annotations

from app.application.orchestrator.context import JobContext
from app.application.progress.progress_reporter import ProgressReporter
from app.core.exceptions import AudioProcessingError
from app.core.interfaces.audio_processor import AudioSpec, IAudioProcessor
from app.core.value_objects import JobStage
from app.infrastructure.storage.path_resolver import PathResolver


class ExtractAudioStep:
    def __init__(self, processor: IAudioProcessor, paths: PathResolver) -> None:
        self._proc = processor
        self._paths = paths

    async def run(self, ctx: JobContext, reporter: ProgressReporter) -> JobContext:
        if ctx.downloaded_file is None:
            raise AudioProcessingError("Nada para extrair — sem arquivo baixado")

        await reporter.report(
            ctx.job, JobStage.EXTRACTING_AUDIO, 0.0, "Extraindo áudio"
        )

        target_dir = self._paths.job_audio_dir(ctx.job.id)
        audio = await self._proc.extract_audio(ctx.downloaded_file, target_dir, AudioSpec())
        ctx.audio_path = audio

        await reporter.report(
            ctx.job, JobStage.EXTRACTING_AUDIO, 1.0, f"Áudio pronto: {audio.name}"
        )
        return ctx
