"""Container de injeção de dependências.

Constrói e mantém referência a todos os serviços do sistema.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.ai.llm.no_op_provider import NoOpLLMProvider
from app.ai.llm.ollama_provider import OllamaProvider
from app.application.orchestrator.job_orchestrator import JobOrchestrator
from app.application.orchestrator.pipeline import Pipeline
from app.application.orchestrator.steps.download_step import DownloadStep
from app.application.orchestrator.steps.extract_audio_step import ExtractAudioStep
from app.application.orchestrator.steps.finalize_step import FinalizeStep
from app.application.orchestrator.steps.subtitle_step import SubtitleStep
from app.application.orchestrator.steps.transcribe_step import TranscribeStep
from app.application.progress.progress_reporter import ProgressReporter
from app.application.queue.job_queue import JobQueue
from app.application.queue.worker_pool import WorkerPool
from app.config import Settings
from app.infrastructure.database.repositories.clip_repository import SQLAlchemyClipRepository
from app.infrastructure.database.repositories.job_repository import SQLAlchemyJobRepository
from app.infrastructure.database.repositories.template_repository import (
    SQLAlchemyTemplateRepository,
)
from app.infrastructure.database.session import get_sessionmaker
from app.infrastructure.event_bus.in_memory_bus import InMemoryEventBus
from app.infrastructure.storage.path_resolver import PathResolver
from app.services.audio.ffmpeg_adapter import FFmpegAudioProcessor
from app.services.downloader.local_file_adapter import LocalFileDownloader
from app.services.downloader.ytdlp_adapter import YtDlpDownloader
from app.services.highlight_llm import LLMHighlightSelector
from app.services.reframe import OpenCVReframer
from app.services.subtitle.generator import SubtitleGenerator
from app.services.transcriber.faster_whisper_adapter import FasterWhisperTranscriber

if TYPE_CHECKING:
    from app.api.websocket.manager import WebSocketManager


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        self.event_bus = InMemoryEventBus()
        self.path_resolver = PathResolver(settings)
        self.job_repository = SQLAlchemyJobRepository(get_sessionmaker())
        self.clip_repository = SQLAlchemyClipRepository(get_sessionmaker())
        self.template_repository = SQLAlchemyTemplateRepository(get_sessionmaker())

        self.audio_processor = FFmpegAudioProcessor()
        self.transcriber = FasterWhisperTranscriber(settings)
        self.subtitle_generator = SubtitleGenerator()
        self.highlight_selector = LLMHighlightSelector(settings)
        self.reframer = OpenCVReframer()

        # LLM local — Ollama quando configurado, NoOp caso contrário
        if settings.highlight_provider == "ollama":
            self.llm_provider = OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                timeout=settings.ollama_timeout,
            )
        else:
            self.llm_provider = NoOpLLMProvider()

        self.downloaders = [
            LocalFileDownloader(),
            YtDlpDownloader(),
        ]

        self.progress_reporter = ProgressReporter(self.event_bus, self.job_repository)

        self.pipeline = Pipeline(
            steps=[
                DownloadStep(self.downloaders, self.path_resolver),
                ExtractAudioStep(self.audio_processor, self.path_resolver),
                TranscribeStep(self.transcriber),
                SubtitleStep(self.subtitle_generator, self.path_resolver),
                FinalizeStep(self.job_repository),
            ],
            reporter=self.progress_reporter,
        )

        self.orchestrator = JobOrchestrator(
            pipeline=self.pipeline,
            repository=self.job_repository,
            event_bus=self.event_bus,
        )

        self.job_queue = JobQueue()
        self.worker_pool = WorkerPool(
            queue=self.job_queue,
            orchestrator=self.orchestrator,
            max_concurrent=settings.max_concurrent_jobs,
        )

        self.websocket_manager: WebSocketManager | None = None

    @classmethod
    async def create(cls, settings: Settings) -> "Container":
        # Import tardio para evitar ciclo
        from app.api.websocket.manager import WebSocketManager

        container = cls(settings)
        container.websocket_manager = WebSocketManager()
        container.websocket_manager.bind_to_bus(container.event_bus)
        return container

    async def dispose(self) -> None:
        from app.infrastructure.database.session import dispose_engine

        await dispose_engine()


_container: Container | None = None


def set_container(c: Container) -> None:
    global _container
    _container = c


def get_container() -> Container:
    if _container is None:
        raise RuntimeError("Container não inicializado.")
    return _container
