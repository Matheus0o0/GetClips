"""Endpoints de Clips (cortes verticais)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.v1.dependencies import (
    create_highlights_uc,
    get_clip_uc,
    list_clips_uc,
    render_clip_uc,
)
from app.api.v1.schemas.clips import ClipDTO, HighlightRequest, RenderRequest
from app.api.v1.schemas.common import MessageResponse
from app.application.use_cases.create_highlights import CreateHighlightsUseCase
from app.application.use_cases.get_clip import GetClipUseCase, ListClipsUseCase
from app.application.use_cases.render_clip import RenderClipUseCase
from app.config import get_settings
from app.core.interfaces.highlight_selector import HighlightParams

router = APIRouter(tags=["clips"])


@router.post("/jobs/{job_id}/highlights", response_model=list[ClipDTO])
async def create_highlights(
    job_id: str,
    body: HighlightRequest,
    uc: CreateHighlightsUseCase = Depends(create_highlights_uc),
) -> list[ClipDTO]:
    cfg = get_settings()
    params = HighlightParams(
        max_clips=body.max_clips or cfg.highlight_max_clips,
        duration_min=body.duration_min or cfg.highlight_clip_duration_min,
        duration_max=body.duration_max or cfg.highlight_clip_duration_max,
    )
    clips = await uc.execute(job_id, params)
    return [ClipDTO.from_entity(c) for c in clips]


@router.get("/jobs/{job_id}/clips", response_model=list[ClipDTO])
async def list_job_clips(
    job_id: str,
    uc: ListClipsUseCase = Depends(list_clips_uc),
) -> list[ClipDTO]:
    clips = await uc.execute(job_id)
    return [ClipDTO.from_entity(c) for c in clips]


@router.post("/clips/{clip_id}/render", response_model=MessageResponse)
async def render_clip(
    clip_id: str,
    body: RenderRequest = RenderRequest(),
    uc: RenderClipUseCase = Depends(render_clip_uc),
) -> MessageResponse:
    await uc.execute(clip_id, template_id=body.template_id)
    return MessageResponse(message="Render iniciado")


@router.get("/clips/{clip_id}", response_model=ClipDTO)
async def get_clip(
    clip_id: str,
    uc: GetClipUseCase = Depends(get_clip_uc),
) -> ClipDTO:
    clip = await uc.execute(clip_id)
    return ClipDTO.from_entity(clip)


@router.get("/clips/{clip_id}/download")
async def download_clip(
    clip_id: str,
    uc: GetClipUseCase = Depends(get_clip_uc),
) -> FileResponse:
    clip = await uc.execute(clip_id)
    if not clip.output_path:
        raise HTTPException(409, "Clip ainda não renderizado")
    p = Path(clip.output_path)
    if not p.exists():
        raise HTTPException(410, "Arquivo removido do disco")
    return FileResponse(str(p), filename=p.name, media_type="video/mp4")
