"""Adapter que implementa ITranscriber usando faster-whisper."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.config import Settings
from app.core.entities.segment import Segment
from app.core.entities.transcription import Transcription
from app.core.exceptions import TranscriptionError
from app.core.interfaces.downloader import ProgressCallback
from app.core.interfaces.transcriber import TranscriptionParams
from app.services.transcriber.device_detector import detect_device, resolve_compute_type
from app.services.transcriber.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class FasterWhisperTranscriber:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._loader = ModelLoader(settings.models_dir)

    async def transcribe(
        self,
        audio_path: Path,
        params: TranscriptionParams,
        on_progress: ProgressCallback | None = None,
    ) -> Transcription:
        if not audio_path.exists():
            raise TranscriptionError(f"Arquivo não encontrado: {audio_path}")

        device, base_compute = detect_device(self._settings.device)
        compute_type = resolve_compute_type(self._settings.compute_type, device)

        model_name = params.model.value
        language = None if params.language.value == "auto" else params.language.value

        loop = asyncio.get_running_loop()

        model = await loop.run_in_executor(
            None, self._loader.get, model_name, device, compute_type
        )

        # Quando o idioma é auto, amostra vários segmentos e exige confiança
        # mínima para evitar detecção errada em vídeos com música/vinheta/silêncio
        # no início.
        detection_kwargs: dict = {}
        if language is None:
            detection_kwargs = {
                "language_detection_segments": 4,
                "language_detection_threshold": 0.5,
            }

        segments_iter, info = await loop.run_in_executor(
            None,
            lambda: model.transcribe(
                str(audio_path),
                language=language,
                beam_size=params.beam_size,
                temperature=params.temperature,
                vad_filter=params.vad_filter,
                condition_on_previous_text=False,
                **detection_kwargs,
            ),
        )

        logger.info(
            "Whisper info: idioma=%s prob=%.2f dur=%.1fs",
            info.language,
            float(info.language_probability or 0.0),
            float(info.duration or 0.0),
        )

        total = float(info.duration or 0.0)
        collected: list[Segment] = []

        # Consumir o gerador em thread executor, publicando progresso a cada N segmentos
        async def _drain() -> None:
            nonlocal collected
            batch: list[Segment] = []
            step = 0

            def _pull_next() -> object:
                try:
                    return next(segments_iter)
                except StopIteration:
                    return None

            while True:
                seg = await loop.run_in_executor(None, _pull_next)
                if seg is None:
                    break
                domain_seg = Segment(
                    index=step,
                    start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000),
                    text=seg.text.strip(),
                    confidence=float(getattr(seg, "avg_logprob", 0.0) or 0.0),
                )
                batch.append(domain_seg)
                step += 1

                if on_progress and total > 0:
                    progress = min(0.99, seg.end / total)
                    if step % 5 == 0:
                        await on_progress(
                            progress, f"Segmento {step} ({seg.end:.1f}s / {total:.1f}s)"
                        )

            collected = batch

        await _drain()

        if on_progress:
            await on_progress(1.0, "Transcrição concluída")

        return Transcription(
            segments=collected,
            language_detected=info.language or "unknown",
            language_probability=float(info.language_probability or 0.0),
            model_used=model_name,
            duration_seconds=total,
        )
