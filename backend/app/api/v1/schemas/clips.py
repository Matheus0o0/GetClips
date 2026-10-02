"""DTOs de Clips."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.entities.clip import Clip


class HighlightRequest(BaseModel):
    max_clips: int | None = Field(None, ge=1, le=20)
    duration_min: int | None = Field(None, ge=5, le=180)
    duration_max: int | None = Field(None, ge=5, le=300)


class RenderRequest(BaseModel):
    template_id: str | None = None


class ClipDTO(BaseModel):
    id: str
    job_id: str
    inicio: float
    fim: float
    duration: float
    hook_text: str
    score: float
    motivo: str
    crop_mode: str
    status: str
    output_path: str | None
    error_message: str | None
    progress: float
    created_at: datetime
    template_id: str | None = None

    @classmethod
    def from_entity(cls, c: Clip) -> "ClipDTO":
        return cls(
            id=c.id,
            job_id=c.job_id,
            inicio=c.inicio,
            fim=c.fim,
            duration=c.duration,
            hook_text=c.hook_text,
            score=c.score,
            motivo=c.motivo,
            crop_mode=c.crop_mode.value,
            status=c.status.value,
            output_path=c.output_path,
            error_message=c.error_message,
            progress=c.progress,
            created_at=c.created_at,
            template_id=c.template_id,
        )
