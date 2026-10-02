"""UseCase: criar um novo Job."""
from __future__ import annotations

from app.application.queue.job_queue import JobQueue
from app.core.entities import Job, JobParams
from app.core.events.job_events import JobCreatedEvent
from app.core.interfaces.event_bus import IEventBus
from app.core.interfaces.job_repository import IJobRepository


class CreateJobUseCase:
    def __init__(
        self,
        repo: IJobRepository,
        queue: JobQueue,
        bus: IEventBus,
    ) -> None:
        self._repo = repo
        self._queue = queue
        self._bus = bus

    async def execute(
        self,
        source_url: str | None,
        source_file: str | None,
        params: JobParams,
    ) -> Job:
        if not source_url and not source_file:
            raise ValueError("Informe source_url ou source_file")

        job = Job(source_url=source_url, source_file=source_file, params=params)
        await self._repo.save(job)
        await self._queue.enqueue(job.id)
        await self._bus.publish(
            JobCreatedEvent(job_id=job.id, source=source_url or source_file or "")
        )
        return job
