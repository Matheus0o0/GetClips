"""UseCase: cancelar Job."""
from __future__ import annotations

from app.application.orchestrator.job_orchestrator import JobOrchestrator


class CancelJobUseCase:
    def __init__(self, orchestrator: JobOrchestrator) -> None:
        self._orch = orchestrator

    async def execute(self, job_id: str) -> bool:
        return await self._orch.cancel(job_id)
