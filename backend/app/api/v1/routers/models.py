"""Listagem de modelos Whisper."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.schemas.common import ModelInfo
from app.config import get_settings
from app.core.value_objects import ModelType

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelInfo])
async def list_models() -> list[ModelInfo]:
    cfg = get_settings()
    models_dir = cfg.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)

    downloaded_dirs = {p.name.lower() for p in models_dir.iterdir() if p.is_dir()}

    infos: list[ModelInfo] = []
    for m in ModelType:
        downloaded = any(m.value.lower() in d for d in downloaded_dirs)
        infos.append(ModelInfo(name=m.value, downloaded=downloaded))
    return infos
