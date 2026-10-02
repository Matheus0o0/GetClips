"""DTOs comuns."""
from __future__ import annotations

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class SettingsDTO(BaseModel):
    default_model: str
    default_language: str
    device: str
    max_concurrent_jobs: int
    storage_root: str
    beam_size: int
    highlight_provider: str
    highlight_configured: bool
    highlight_max_clips: int
    highlight_clip_duration_min: int
    highlight_clip_duration_max: int
    reframe_output_resolution: str


class ModelInfo(BaseModel):
    name: str
    downloaded: bool
    size_bytes: int | None = None
