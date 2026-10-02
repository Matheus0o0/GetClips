"""UseCase: listar jobs."""
from __future__ import annotations

from app.core.entities import Job
from app.core.interfaces.job_repository import IJobRepository


class ListJobsUseCase:
    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    async def execute(self, limit: int = 100, offset: int = 0) -> list[Job]:
        return await self._repo.list(limit=limit, offset=offset)
