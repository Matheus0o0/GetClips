"""Use case: pede à LLM candidatos a corte e persiste como Clip PENDING."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.entities.clip import Clip, ClipStatus
from app.core.exceptions import JobNotFoundError
from app.core.interfaces.clip_repository import IClipRepository
from app.core.interfaces.highlight_selector import HighlightParams, IHighlightSelector
from app.core.interfaces.job_repository import IJobRepository

logger = logging.getLogger(__name__)


class CreateHighlightsUseCase:
    def __init__(
        self,
        job_repo: IJobRepository,
        clip_repo: IClipRepository,
        selector: IHighlightSelector,
    ) -> None:
        self._jobs = job_repo
        self._clips = clip_repo
        self._selector = selector

    async def execute(self, job_id: str, params: HighlightParams) -> list[Clip]:
        job = await self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        tr = await self._jobs.get_transcription(job_id)
        if tr is None:
            from app.core.exceptions import DomainError

            raise DomainError("Transcrição não disponível ainda para este job")

        candidates = await self._selector.select(tr, params)

        now = datetime.now(tz=timezone.utc)
        clips: list[Clip] = []
        for c in candidates:
            clip = Clip(
                job_id=job_id,
                inicio=c.inicio,
                fim=c.fim,
                hook_text=c.hook,
                score=c.score,
                motivo=c.motivo,
                status=ClipStatus.PENDING,
                created_at=now,
            )
            await self._clips.save(clip)
            clips.append(clip)
        logger.info("job %s: %d candidatos persistidos", job_id, len(clips))
        return clips
