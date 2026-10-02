"""Orquestrador de jobs — coordena Pipeline, Repository e EventBus."""
from __future__ import annotations

import logging

from app.application.orchestrator.context import JobContext
from app.application.orchestrator.pipeline import Pipeline
from app.core.events.job_events import (
    JobCancelledEvent,
    JobCompletedEvent,
    JobFailedEvent,
)
from app.core.exceptions import JobCancelledError, JobNotFoundError
from app.core.interfaces.event_bus import IEventBus
from app.core.interfaces.job_repository import IJobRepository
from app.core.value_objects import JobStage

logger = logging.getLogger(__name__)


class JobOrchestrator:
    def __init__(
        self,
        pipeline: Pipeline,
        repository: IJobRepository,
        event_bus: IEventBus,
    ) -> None:
        self._pipeline = pipeline
        self._repo = repository
        self._bus = event_bus
        self._contexts: dict[str, JobContext] = {}

    async def run(self, job_id: str) -> None:
        job = await self._repo.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)

        job.mark_started()
        await self._repo.save(job)

        ctx = JobContext(job=job)
        self._contexts[job_id] = ctx

        try:
            await self._pipeline.execute(ctx)
            job.mark_completed()
            await self._repo.save(job)
            await self._bus.publish(
                JobCompletedEvent(
                    job_id=job.id,
                    outputs={k: str(v) for k, v in ctx.outputs.items()},
                )
            )
        except JobCancelledError:
            job.mark_cancelled()
            await self._repo.save(job)
            await self._bus.publish(JobCancelledEvent(job_id=job.id))
            logger.info("Job cancelado", extra={"job_id": job.id})
        except Exception as exc:  # noqa: BLE001
            logger.exception("Falha no job", extra={"job_id": job.id})
            job.mark_failed(str(exc))
            await self._repo.save(job)
            await self._bus.publish(
                JobFailedEvent(job_id=job.id, error=str(exc), stage=job.stage.value)
            )
        finally:
            self._contexts.pop(job_id, None)

    async def cancel(self, job_id: str) -> bool:
        ctx = self._contexts.get(job_id)
        if ctx is None:
            job = await self._repo.get(job_id)
            if job is None or job.status.value in {"COMPLETED", "FAILED", "CANCELLED"}:
                return False
            job.mark_cancelled()
            job.stage = JobStage.DONE
            await self._repo.save(job)
            await self._bus.publish(JobCancelledEvent(job_id=job_id))
            return True
        ctx.cancel()
        return True
