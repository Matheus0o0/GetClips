"""Endpoints de settings."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.schemas.common import SettingsDTO
from app.config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsDTO)
async def read_settings() -> SettingsDTO:
    s = get_settings()
    if s.highlight_provider == "ollama":
        configured = True
    elif s.highlight_provider in ("none", ""):
        configured = False
    elif s.highlight_provider == "openai":
        configured = bool(s.openai_api_key.strip())
    else:
        configured = bool(s.anthropic_api_key.strip())

    return SettingsDTO(
        default_model=s.default_model,
        default_language=s.default_language,
        device=s.device,
        max_concurrent_jobs=s.max_concurrent_jobs,
        storage_root=str(s.storage_root),
        beam_size=s.beam_size,
        highlight_provider=s.highlight_provider,
        highlight_configured=configured,
        highlight_max_clips=s.highlight_max_clips,
        highlight_clip_duration_min=s.highlight_clip_duration_min,
        highlight_clip_duration_max=s.highlight_clip_duration_max,
        reframe_output_resolution=s.reframe_output_resolution,
    )
