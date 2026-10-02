"""Endpoints de Jobs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import cancel_job_uc, create_job_uc, get_job_uc, list_jobs_uc
from app.api.v1.schemas.common import MessageResponse
from app.api.v1.schemas.jobs import (
    CreateJobRequest,
    JobDetailDTO,
    JobDTO,
    MediaFileDTO,
    RerunRequest,
    SegmentDTO,
    TranscriptionDTO,
)
from app.application.use_cases.cancel_job import CancelJobUseCase
from app.application.use_cases.create_job import CreateJobUseCase
from app.application.use_cases.get_job import GetJobUseCase
from app.application.use_cases.list_jobs import ListJobsUseCase
from app.core.entities.job import JobParams
from app.core.exceptions import JobNotFoundError

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobDTO, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    body: CreateJobRequest,
    uc: CreateJobUseCase = Depends(create_job_uc),
) -> JobDTO:
    if not body.url and not body.file_path:
        raise HTTPException(400, "url ou file_path é obrigatório")
    job = await uc.execute(
        source_url=body.url,
        source_file=body.file_path,
        params=body.params.to_entity(),
    )
    return JobDTO.from_entity(job)


@router.get("", response_model=list[JobDTO])
async def list_jobs(
    limit: int = 100,
    offset: int = 0,
    uc: ListJobsUseCase = Depends(list_jobs_uc),
) -> list[JobDTO]:
    jobs = await uc.execute(limit=limit, offset=offset)
    return [JobDTO.from_entity(j) for j in jobs]


@router.get("/{job_id}", response_model=JobDetailDTO)
async def get_job(
    job_id: str,
    uc: GetJobUseCase = Depends(get_job_uc),
) -> JobDetailDTO:
    job = await uc.execute(job_id)
    media = await uc.list_media(job_id)
    tr = await uc.get_transcription(job_id)
    return JobDetailDTO(
        job=JobDTO.from_entity(job),
        media=[MediaFileDTO.from_entity(m) for m in media],
        transcription_available=tr is not None,
    )


@router.delete("/{job_id}", response_model=MessageResponse)
async def cancel_job(
    job_id: str,
    uc: CancelJobUseCase = Depends(cancel_job_uc),
) -> MessageResponse:
    ok = await uc.execute(job_id)
    if not ok:
        raise HTTPException(404, "Job não encontrado ou já finalizado")
    return MessageResponse(message="Job cancelado")


@router.get("/{job_id}/transcription", response_model=TranscriptionDTO)
async def get_transcription(
    job_id: str,
    uc: GetJobUseCase = Depends(get_job_uc),
) -> TranscriptionDTO:
    tr = await uc.get_transcription(job_id)
    if tr is None:
        raise HTTPException(404, "Transcrição não disponível para este job")
    return TranscriptionDTO(
        full_text=tr.full_text,
        language_detected=tr.language_detected,
        language_probability=tr.language_probability,
        model_used=tr.model_used,
        duration_seconds=tr.duration_seconds,
        segments=[
            SegmentDTO(
                index=s.index,
                start_ms=s.start_ms,
                end_ms=s.end_ms,
                text=s.text,
                confidence=s.confidence,
            )
            for s in tr.segments
        ],
    )


@router.post("/{job_id}/rerun", response_model=JobDTO, status_code=status.HTTP_202_ACCEPTED)
async def rerun_job(
    job_id: str,
    body: RerunRequest,
    get_uc: GetJobUseCase = Depends(get_job_uc),
    create_uc: CreateJobUseCase = Depends(create_job_uc),
) -> JobDTO:
    """Cria um NOVO job usando a mesma fonte, mas com params opcionalmente sobrescritos.

    Útil quando o Whisper detecta o idioma errado — o usuário força pt/en/es sem
    precisar colar a URL de novo.
    """
    try:
        original = await get_uc.execute(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc

    params = JobParams(
        model=body.model or original.params.model,
        language=body.language or original.params.language,
        beam_size=body.beam_size or original.params.beam_size,
        output_formats=tuple(body.output_formats or original.params.output_formats),
        audio_only=(
            body.audio_only if body.audio_only is not None else original.params.audio_only
        ),
        keep_source_video=original.params.keep_source_video,
    )
    new_job = await create_uc.execute(
        source_url=original.source_url,
        source_file=original.source_file,
        params=params,
    )
    return JobDTO.from_entity(new_job)
