"""Contrato do serviço de seleção de trechos (LLM externa)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.core.entities.transcription import Transcription


@dataclass(slots=True)
class HighlightCandidate:
    inicio: float
    fim: float
    hook: str
    score: float
    motivo: str


@dataclass(slots=True)
class HighlightParams:
    max_clips: int = 5
    duration_min: int = 30
    duration_max: int = 60


@runtime_checkable
class IHighlightSelector(Protocol):
    async def select(
        self,
        transcription: Transcription,
        params: HighlightParams,
    ) -> list[HighlightCandidate]: ...
