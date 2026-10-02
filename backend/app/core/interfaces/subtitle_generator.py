"""Contrato de gerador de legendas/transcrições."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from app.core.entities.transcription import Transcription


@runtime_checkable
class ISubtitleGenerator(Protocol):
    def supported_formats(self) -> tuple[str, ...]: ...

    async def generate(
        self,
        transcription: Transcription,
        target_dir: Path,
        base_name: str,
        formats: tuple[str, ...],
    ) -> dict[str, Path]: ...
