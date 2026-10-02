"""Upload de arquivo local + criação de Job."""
from __future__ import annotations

import shutil
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.v1.dependencies import create_job_uc
from app.api.v1.schemas.jobs import JobDTO, JobParamsDTO
from app.application.use_cases.create_job import CreateJobUseCase
from app.config import get_settings

router = APIRouter(prefix="/upload", tags=["upload"])

_MAX_UPLOAD_BYTES = 4 * 1024 * 1024 * 1024  # 4 GiB
_ALLOWED_EXTS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".m4v",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus",
}


@router.post("", response_model=JobDTO)
async def upload_and_create_job(
    file: UploadFile = File(...),
    model: str = Form("distil-large-v3"),
    language: str = Form("auto"),
    beam_size: int = Form(5),
    uc: CreateJobUseCase = Depends(create_job_uc),
) -> JobDTO:
    if not file.filename:
        raise HTTPException(400, "Nome de arquivo ausente")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(400, f"Extensão não suportada: {ext}")

    cfg = get_settings()
    cfg.temp_dir.mkdir(parents=True, exist_ok=True)

    dst = cfg.temp_dir / f"upload_{Path(file.filename).name}"
    total = 0
    async with aiofiles.open(dst, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > _MAX_UPLOAD_BYTES:
                await f.close()
                dst.unlink(missing_ok=True)
                raise HTTPException(413, "Arquivo excede tamanho máximo")
            await f.write(chunk)

    params = JobParamsDTO(model=model, language=language, beam_size=beam_size)
    job = await uc.execute(source_url=None, source_file=str(dst), params=params.to_entity())
    return JobDTO.from_entity(job)


@router.post("/import", response_model=JobDTO)
async def import_local_file(
    file_path: str = Form(...),
    model: str = Form("distil-large-v3"),
    language: str = Form("auto"),
    beam_size: int = Form(5),
    uc: CreateJobUseCase = Depends(create_job_uc),
) -> JobDTO:
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        raise HTTPException(400, f"Arquivo local inválido: {file_path}")
    params = JobParamsDTO(model=model, language=language, beam_size=beam_size)
    job = await uc.execute(source_url=None, source_file=str(p), params=params.to_entity())
    return JobDTO.from_entity(job)


# suprime unused-import falso-positivo
_ = shutil
