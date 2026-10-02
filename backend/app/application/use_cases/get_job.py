"""UseCases: obter e listar jobs."""
from __future__ import annotations

from app.core.entities import Job, MediaFile, Transcription
from app.core.exceptions import JobNotFoundError
from app.core.interfaces.job_repository import IJobRepository


class GetJobUseCase:
    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    async def execute(self, job_id: str) -> Job:
        job = await self._repo.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job

    async def list_media(self, job_id: str) -> list[MediaFile]:
        return await self._repo.list_media(job_id)

    async def get_transcription(self, job_id: str) -> Transcription | None:
        return await self._repo.get_transcription(job_id)
