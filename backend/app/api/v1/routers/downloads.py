"""Download dos artefatos gerados por um Job."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.v1.dependencies import get_job_uc
from app.application.use_cases.get_job import GetJobUseCase

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/{job_id}/{fmt}")
async def download_output(
    job_id: str,
    fmt: str,
    uc: GetJobUseCase = Depends(get_job_uc),
) -> FileResponse:
    media = await uc.list_media(job_id)
    match = next((m for m in media if m.format.lower() == fmt.lower()), None)
    if match is None:
        raise HTTPException(404, f"Formato '{fmt}' não disponível para este job")
    p = Path(match.path)
    if not p.exists():
        raise HTTPException(410, "Arquivo removido do disco")
    return FileResponse(str(p), filename=p.name)


@router.get("/{job_id}/media/{filename}")
async def download_by_name(
    job_id: str,
    filename: str,
    uc: GetJobUseCase = Depends(get_job_uc),
) -> FileResponse:
    media = await uc.list_media(job_id)
    match = next((m for m in media if Path(m.path).name == filename), None)
    if match is None:
        raise HTTPException(404, "Arquivo não encontrado")
    p = Path(match.path)
    if not p.exists():
        raise HTTPException(410, "Arquivo removido do disco")
    return FileResponse(str(p), filename=p.name)
