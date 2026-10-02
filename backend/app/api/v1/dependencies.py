"""Dependências FastAPI: acessam o Container."""
from __future__ import annotations

from app.application.orchestrator.job_orchestrator import JobOrchestrator
from app.application.queue.job_queue import JobQueue
from app.application.use_cases.cancel_job import CancelJobUseCase
from app.application.use_cases.create_highlights import CreateHighlightsUseCase
from app.application.use_cases.create_job import CreateJobUseCase
from app.application.use_cases.get_clip import GetClipUseCase, ListClipsUseCase
from app.application.use_cases.get_job import GetJobUseCase
from app.application.use_cases.list_jobs import ListJobsUseCase
from app.application.use_cases.render_clip import RenderClipUseCase
from app.core.interfaces.event_bus import IEventBus
from app.core.interfaces.job_repository import IJobRepository
from app.infrastructure.container import get_container
from app.infrastructure.database.repositories.template_repository import (
    SQLAlchemyTemplateRepository,
)


def get_repo() -> IJobRepository:
    return get_container().job_repository


def get_bus() -> IEventBus:
    return get_container().event_bus


def get_queue() -> JobQueue:
    return get_container().job_queue


def get_orchestrator() -> JobOrchestrator:
    return get_container().orchestrator


def create_job_uc() -> CreateJobUseCase:
    c = get_container()
    return CreateJobUseCase(c.job_repository, c.job_queue, c.event_bus)


def cancel_job_uc() -> CancelJobUseCase:
    return CancelJobUseCase(get_container().orchestrator)


def get_job_uc() -> GetJobUseCase:
    return GetJobUseCase(get_container().job_repository)


def list_jobs_uc() -> ListJobsUseCase:
    return ListJobsUseCase(get_container().job_repository)


def create_highlights_uc() -> CreateHighlightsUseCase:
    c = get_container()
    return CreateHighlightsUseCase(c.job_repository, c.clip_repository, c.highlight_selector)


def render_clip_uc() -> RenderClipUseCase:
    c = get_container()
    return RenderClipUseCase(
        settings=c.settings,
        clip_repo=c.clip_repository,
        job_repo=c.job_repository,
        reframer=c.reframer,
        paths=c.path_resolver,
        bus=c.event_bus,
        template_repo=c.template_repository,
    )


def get_clip_uc() -> GetClipUseCase:
    return GetClipUseCase(get_container().clip_repository)


def list_clips_uc() -> ListClipsUseCase:
    return ListClipsUseCase(get_container().clip_repository)


def get_template_repository() -> SQLAlchemyTemplateRepository:
    return get_container().template_repository
