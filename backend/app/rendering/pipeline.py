"""TemplateRenderer — pipeline completo de renderização com template.

Fluxo:
  1. Extrai segmento do vídeo fonte
  2. Aplica jump cuts (remoção de silêncio/filler) se houver
  3. Reenquadra 9:16 com tracking + zoom dinâmico
  4. Queima legendas ASS sobre o vídeo final

O renderer nunca executa JSON direto do LLM — recebe um EditingPlan já
validado pelo schema Pydantic.
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

from app.config import Settings
from app.core.entities.clip import CropMode
from app.core.entities.transcription import Transcription
from app.core.interfaces.reframer import ReframeParams, ReframeProgress
from app.editing.captions.ass_generator import ass_path_for_ffmpeg, generate_ass
from app.editing.captions.chunker import chunk_segments
from app.editing.engine.jump_cuts import apply_jump_cuts
from app.editing.plans.schema import EditingPlan
from app.editing.templates.model import EditingTemplateConfig
from app.services.reframe.render import (
    ReframeError,
    _reframe_sync,
    extract_segment,
    mux_audio,
    run_ffmpeg,
)

logger = logging.getLogger(__name__)


def _burn_captions(video: Path, ass_file: Path, output: Path, crf: int = 23) -> None:
    """Queima o arquivo ASS sobre o vídeo usando o filtro subtitles do FFmpeg."""
    ass_str = ass_path_for_ffmpeg(ass_file)
    try:
        run_ffmpeg([
            "-i", str(video),
            "-vf", f"subtitles='{ass_str}'",
            "-c:v", "libx264",
            "-c:a", "copy",
            "-preset", "fast",
            "-crf", str(crf),
            str(output),
        ])
    except ReframeError as exc:
        # libass pode não estar disponível em alguns builds — apenas avisa e copia
        logger.warning("subtitles filter falhou, saída sem legenda: %s", exc)
        run_ffmpeg(["-i", str(video), "-c", "copy", str(output)])


class TemplateRenderer:
    """Renderiza um clip com template completo: tracking, zoom, jump cuts, legendas."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    async def render(
        self,
        source_video: Path,
        output_path: Path,
        plan: EditingPlan,
        template: EditingTemplateConfig,
        transcription: Transcription | None,
        on_progress: ReframeProgress | None = None,
    ) -> CropMode:
        """Executa o pipeline completo. Retorna o CropMode resultante."""
        if not source_video.exists():
            raise ReframeError(f"vídeo fonte não encontrado: {source_video}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        stem = output_path.stem
        tmp = output_path.parent
        raw = tmp / f".{stem}_raw.mp4"
        trimmed = tmp / f".{stem}_trimmed.mp4"
        reframed = tmp / f".{stem}_reframed.mp4"
        ass_file = tmp / f".{stem}.ass"

        out_w, out_h = self._s.reframe_output_size
        clip_start = plan.clip_start
        clip_end = plan.clip_end

        temp_files = [raw, trimmed, reframed, ass_file]

        try:
            # ── 1. Extrai segmento ─────────────────────────────────────────────
            if on_progress:
                await on_progress(0.02, "extraindo segmento")
            await asyncio.to_thread(extract_segment, source_video, clip_start, clip_end, raw)

            # ── 2. Jump cuts ───────────────────────────────────────────────────
            offset = clip_start
            adjusted_removes = [
                type(r)(
                    start=max(0.0, r.start - offset),
                    end=max(0.0, r.end - offset),
                    reason=r.reason,
                )
                for r in plan.remove
                if r.end > clip_start and r.start < clip_end
            ]

            if adjusted_removes:
                if on_progress:
                    await on_progress(0.08, "removendo silêncio/filler")
                await asyncio.to_thread(apply_jump_cuts, raw, adjusted_removes, trimmed)
                source_for_reframe = trimmed
            else:
                source_for_reframe = raw

            # ── 3. Reframe + zoom ──────────────────────────────────────────────
            zoom_events = [
                (max(0.0, e.start - offset), max(0.0, e.end - offset), e.scale)
                for e in plan.camera_events
            ]

            if on_progress:
                await on_progress(0.12, "reenquadrando vídeo")

            loop = asyncio.get_running_loop()

            # Arquivo de áudio para remux: raw sempre tem o áudio original
            video_only = tmp / f".{stem}_video.mp4"
            temp_files.append(video_only)

            crop_mode, _ = await asyncio.to_thread(
                _reframe_sync,
                source_for_reframe,
                video_only,
                self._s.reframe_detection_stride,
                self._s.reframe_smoothing,
                out_w,
                out_h,
                zoom_events,
                template.tracking.enabled,
                template.tracking.dead_zone_px,
                on_progress,
                loop,
            )

            await asyncio.to_thread(mux_audio, video_only, raw, reframed)

            # ── 4. Burn captions ───────────────────────────────────────────────
            if template.captions.enabled and transcription is not None:
                if on_progress:
                    await on_progress(0.92, "gravando legendas")

                emphasis_texts = frozenset(
                    e.text.lower().strip(".,!?;:")
                    for e in plan.emphasis
                )
                clip_start_ms = int(clip_start * 1000)
                clip_end_ms = int(clip_end * 1000)

                blocks = chunk_segments(
                    transcription.segments,
                    clip_start_ms=clip_start_ms,
                    clip_end_ms=clip_end_ms,
                    words_per_block=template.captions.words_per_block,
                    max_chars=template.captions.max_chars_per_block,
                    emphasis_texts=emphasis_texts,
                )

                ass_content = generate_ass(blocks, template.captions, out_w, out_h)
                ass_file.write_text(ass_content, encoding="utf-8")
                await asyncio.to_thread(_burn_captions, reframed, ass_file, output_path)
            else:
                # Sem legendas: move o reframed para o output final
                reframed.rename(output_path)
                reframed = output_path  # evita tentativa de deleção

            if on_progress:
                await on_progress(1.0, "concluído")

            return crop_mode

        finally:
            for p in temp_files:
                try:
                    if p != output_path:
                        p.unlink(missing_ok=True)
                except OSError:
                    pass
