"""Contrato de transcritor."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.core.entities.transcription import Transcription
from app.core.interfaces.downloader import ProgressCallback
from app.core.value_objects import Language, ModelType


@dataclass(slots=True)
class TranscriptionParams:
    model: ModelType = ModelType.DISTIL_LARGE_V3
    language: Language = Language.AUTO
    beam_size: int = 5
    temperature: float = 0.0
    vad_filter: bool = True


@runtime_checkable
class ITranscriber(Protocol):
    async def transcribe(
        self,
        audio_path: Path,
        params: TranscriptionParams,
        on_progress: ProgressCallback | None = None,
    ) -> Transcription: ...
