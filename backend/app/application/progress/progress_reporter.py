"""ProgressReporter — atualiza Job, publica evento e persiste."""
from __future__ import annotations

import time

from app.core.entities import Job
from app.core.events.job_events import JobProgressEvent, JobStageChangedEvent
from app.core.interfaces.event_bus import IEventBus
from app.core.interfaces.job_repository import IJobRepository
from app.core.value_objects import JobStage

# Pesos aproximados de cada estágio para compor progresso global (0..1)
_STAGE_WEIGHTS: dict[JobStage, tuple[float, float]] = {
    JobStage.QUEUED: (0.0, 0.02),
    JobStage.DOWNLOADING: (0.02, 0.32),
    JobStage.EXTRACTING_AUDIO: (0.32, 0.40),
    JobStage.TRANSCRIBING: (0.40, 0.90),
    JobStage.GENERATING_SUBTITLES: (0.90, 0.97),
    JobStage.FINALIZING: (0.97, 1.0),
    JobStage.DONE: (1.0, 1.0),
}


class ProgressReporter:
    def __init__(self, bus: IEventBus, repo: IJobRepository) -> None:
        self._bus = bus
        self._repo = repo
        self._last_stage: dict[str, JobStage] = {}
        self._last_persist: dict[str, float] = {}

    async def report(
        self,
        job: Job,
        stage: JobStage,
        stage_progress: float,
        message: str = "",
    ) -> None:
        lo, hi = _STAGE_WEIGHTS.get(stage, (0.0, 1.0))
        overall = lo + (hi - lo) * max(0.0, min(1.0, stage_progress))
        job.update_progress(stage, overall, message)

        # Emite stage_changed apenas uma vez por transição
        if self._last_stage.get(job.id) != stage:
            self._last_stage[job.id] = stage
            await self._bus.publish(
                JobStageChangedEvent(job_id=job.id, stage=stage.value, message=message)
            )

        await self._bus.publish(
            JobProgressEvent(
                job_id=job.id,
                stage=stage.value,
                progress=overall,
                message=message,
            )
        )

        # Persistência com throttling (a cada 0.5s ou fim/start de stage)
        now = time.monotonic()
        last = self._last_persist.get(job.id, 0.0)
        if stage_progress in (0.0, 1.0) or (now - last) > 0.5:
            self._last_persist[job.id] = now
            await self._repo.save(job)
