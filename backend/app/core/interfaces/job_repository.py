"""Contrato de repositório de jobs."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.entities.job import Job
from app.core.entities.media_file import MediaFile
from app.core.entities.transcription import Transcription


@runtime_checkable
class IJobRepository(Protocol):
    async def save(self, job: Job) -> None: ...

    async def get(self, job_id: str) -> Job | None: ...

    async def list(self, limit: int = 100, offset: int = 0) -> list[Job]: ...

    async def delete(self, job_id: str) -> bool: ...

    async def attach_media(self, job_id: str, media: MediaFile) -> None: ...

    async def attach_transcription(self, job_id: str, transcription: Transcription) -> None: ...

    async def list_media(self, job_id: str) -> list[MediaFile]: ...

    async def get_transcription(self, job_id: str) -> Transcription | None: ...
