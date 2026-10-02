"""Use case: renderiza um Clip em background.

Sem template → usa OpenCVReframer (crop + tracking apenas).
Com template  → usa TemplateRenderer (tracking + zoom + jump cuts + legendas).
"""
from __future__ import annotations

import asyncio
import logging

from app.config import Settings
from app.core.entities.clip import ClipStatus
from app.core.entities.media_file import MediaKind
from app.core.events.job_events import JobProgressEvent
from app.core.exceptions import ClipNotFoundError, SourceVideoUnavailableError
from app.core.interfaces.clip_repository import IClipRepository
from app.core.interfaces.event_bus import IEventBus
from app.core.interfaces.job_repository import IJobRepository
from app.core.interfaces.reframer import IReframer, ReframeParams
from app.editing.plans.schema import EditingPlan
from app.infrastructure.database.repositories.template_repository import (
    SQLAlchemyTemplateRepository,
)
from app.infrastructure.storage.path_resolver import PathResolver

logger = logging.getLogger(__name__)


class RenderClipUseCase:
    def __init__(
        self,
        settings: Settings,
        clip_repo: IClipRepository,
        job_repo: IJobRepository,
        reframer: IReframer,
        paths: PathResolver,
        bus: IEventBus,
        template_repo: SQLAlchemyTemplateRepository | None = None,
    ) -> None:
        self._s = settings
        self._clips = clip_repo
        self._jobs = job_repo
        self._reframer = reframer
        self._paths = paths
        self._bus = bus
        self._templates = template_repo

    async def execute(self, clip_id: str, template_id: str | None = None) -> None:
        clip = await self._clips.get(clip_id)
        if clip is None:
            raise ClipNotFoundError(clip_id)

        # Descobre vídeo fonte
        media = await self._jobs.list_media(clip.job_id)
        source = next((m for m in media if m.kind == MediaKind.ORIGINAL_VIDEO), None)
        if source is None:
            raise SourceVideoUnavailableError(
                "Job não guardou o vídeo original — regere com keep_source_video=true"
            )

        # Persiste template_id no clip se fornecido
        effective_template_id = template_id or clip.template_id
        if effective_template_id and clip.template_id != effective_template_id:
            clip.template_id = effective_template_id

        clip.status = ClipStatus.RENDERING
        clip.progress = 0.0
        clip.error_message = None
        await self._clips.save(clip)

        asyncio.create_task(
            self._run(clip.id, clip.job_id, source.path, clip.inicio, clip.fim, effective_template_id)
        )

    async def _run(
        self,
        clip_id: str,
        job_id: str,
        source_path,
        inicio: float,
        fim: float,
        template_id: str | None,
    ) -> None:
        async def _progress(pct: float, msg: str) -> None:
            c = await self._clips.get(clip_id)
            if c is None:
                return
            c.progress = pct
            await self._clips.save(c)
            await self._bus.publish(
                JobProgressEvent(
                    job_id=job_id,
                    stage="RENDERING_CLIP",
                    progress=pct,
                    message=f"{clip_id[:8]}: {msg}",
                )
            )

        try:
            out_w, out_h = self._s.reframe_output_size
            out_dir = self._paths.job_clips_dir(job_id)
            out_path = out_dir / f"{clip_id}.mp4"

            if template_id and self._templates is not None:
                crop_mode = await self._render_with_template(
                    source_path, out_path, inicio, fim, template_id, job_id, _progress
                )
            else:
                crop_mode = await self._render_basic(
                    source_path, out_path, inicio, fim, out_w, out_h, _progress
                )

            c = await self._clips.get(clip_id)
            if c is None:
                return
            c.status = ClipStatus.READY
            c.progress = 1.0
            c.output_path = str(out_path)
            c.crop_mode = crop_mode
            await self._clips.save(c)

        except Exception as exc:  # noqa: BLE001
            logger.exception("render do clip %s falhou", clip_id)
            c = await self._clips.get(clip_id)
            if c is not None:
                c.status = ClipStatus.ERROR
                c.error_message = str(exc)
                await self._clips.save(c)

    async def _render_basic(self, source_path, out_path, inicio, fim, out_w, out_h, on_progress):
        """Render sem template: só crop dinâmico."""
        from app.core.entities.clip import CropMode

        params = ReframeParams(
            inicio=inicio,
            fim=fim,
            output_path=out_path,
            detection_stride=self._s.reframe_detection_stride,
            smoothing=self._s.reframe_smoothing,
            output_width=out_w,
            output_height=out_h,
        )
        result = await self._reframer.reframe(source_path, params, on_progress)
        return result.crop_mode

    async def _render_with_template(
        self, source_path, out_path, inicio, fim, template_id, job_id, on_progress
    ):
        """Render com template: tracking + zoom + jump cuts + legendas."""
        from app.rendering.pipeline import TemplateRenderer

        template_row = await self._templates.get(template_id)
        template_cfg = SQLAlchemyTemplateRepository.config_from_row(template_row)

        transcription = await self._jobs.get_transcription(job_id)

        # EditingPlan mínimo a partir dos dados do clip
        # (jump cuts e zoom events virão do LLM na Fase 3)
        plan = EditingPlan(
            clip_start=inicio,
            clip_end=fim,
            hook_text="",
            score=0.0,
        )

        renderer = TemplateRenderer(self._s)
        return await renderer.render(
            source_video=source_path,
            output_path=out_path,
            plan=plan,
            template=template_cfg,
            transcription=transcription,
            on_progress=on_progress,
        )
