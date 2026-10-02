"""Entidade Clip — corte vertical gerado a partir de um Job de transcrição."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class ClipStatus(StrEnum):
    PENDING = "pending"
    RENDERING = "rendering"
    READY = "ready"
    ERROR = "error"


class CropMode(StrEnum):
    DYNAMIC = "dynamic"
    STATIC_FALLBACK = "static_fallback"


@dataclass(slots=True)
class Clip:
    id: str = field(default_factory=_new_id)
    job_id: str = ""
    inicio: float = 0.0
    fim: float = 0.0
    hook_text: str = ""
    score: float = 0.0
    motivo: str = ""
    crop_mode: CropMode = CropMode.DYNAMIC
    status: ClipStatus = ClipStatus.PENDING
    output_path: str | None = None
    error_message: str | None = None
    progress: float = 0.0
    created_at: datetime = field(default_factory=_utcnow)
    template_id: str | None = None

    @property
    def duration(self) -> float:
        return max(0.0, self.fim - self.inicio)
