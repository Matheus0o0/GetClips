"""Contrato do repositório de Clips."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.entities.clip import Clip


@runtime_checkable
class IClipRepository(Protocol):
    async def save(self, clip: Clip) -> None: ...
    async def get(self, clip_id: str) -> Clip | None: ...
    async def list_by_job(self, job_id: str) -> list[Clip]: ...
    async def delete(self, clip_id: str) -> bool: ...
