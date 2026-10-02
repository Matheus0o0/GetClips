"""Endpoint de histórico (alias de GET /jobs com filtros)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import list_jobs_uc
from app.api.v1.schemas.jobs import JobDTO
from app.application.use_cases.list_jobs import ListJobsUseCase

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[JobDTO])
async def get_history(
    limit: int = 200,
    offset: int = 0,
    uc: ListJobsUseCase = Depends(list_jobs_uc),
) -> list[JobDTO]:
    jobs = await uc.execute(limit=limit, offset=offset)
    return [JobDTO.from_entity(j) for j in jobs]
