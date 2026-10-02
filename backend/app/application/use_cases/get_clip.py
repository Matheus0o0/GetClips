"""Use cases: get_clip / list_clips_for_job."""
from __future__ import annotations

from app.core.entities.clip import Clip
from app.core.exceptions import ClipNotFoundError
from app.core.interfaces.clip_repository import IClipRepository


class GetClipUseCase:
    def __init__(self, repo: IClipRepository) -> None:
        self._repo = repo

    async def execute(self, clip_id: str) -> Clip:
        c = await self._repo.get(clip_id)
        if c is None:
            raise ClipNotFoundError(clip_id)
        return c


class ListClipsUseCase:
    def __init__(self, repo: IClipRepository) -> None:
        self._repo = repo

    async def execute(self, job_id: str) -> list[Clip]:
        return await self._repo.list_by_job(job_id)
