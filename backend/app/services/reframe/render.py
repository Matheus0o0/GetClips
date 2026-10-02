"""Reenquadramento vertical: extrai segmento, aplica crop dinâmico + zoom, remuxa áudio.

Pipeline:
  1. ffmpeg extrai [inicio,fim] do vídeo fonte -> clip_bruto.mp4
  2. OpenCV: para cada frame, detecta rosto (a cada N frames), suaviza a
     posição, calcula o crop 9:16 centrado nele, aplica zoom dinâmico,
     escreve clip_video.mp4 (sem áudio)
  3. ffmpeg remuxa o áudio do clip_bruto no clip_video -> saída final .mp4
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

from app.core.entities.clip import CropMode
from app.core.interfaces.reframer import ReframeParams, ReframeProgress, ReframeResult
from app.services.reframe.detector import FaceDetector
from app.services.reframe.smoothing import build_smoother

logger = logging.getLogger(__name__)


class ReframeError(RuntimeError):
    pass


def run_ffmpeg(args: list[str]) -> None:
    logger.info("ffmpeg %s", " ".join(args))
    proc = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise ReframeError(f"ffmpeg falhou: {proc.stderr.decode(errors='ignore')[:400]}")


def extract_segment(source: Path, inicio: float, fim: float, out: Path) -> None:
    # -ss antes de -i faz seek rápido; -to marca o ponto final.
    run_ffmpeg([
        "-ss", f"{inicio:.3f}",
        "-to", f"{fim:.3f}",
        "-i", str(source),
        "-c", "copy",
        str(out),
    ])


def mux_audio(video_only: Path, audio_source: Path, out: Path) -> None:
    run_ffmpeg([
        "-i", str(video_only),
        "-i", str(audio_source),
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(out),
    ])


def _get_zoom_scale(
    t: float,
    zoom_events: list[tuple[float, float, float]],
) -> float:
    """Retorna o scale alvo para o timestamp t (segundos)."""
    for start, end, scale in zoom_events:
        if start <= t <= end:
            return scale
    return 1.0


def _reframe_sync(
    segment_video: Path,
    video_only_out: Path,
    detection_stride: int,
    smoothing_kind: str,
    out_w: int,
    out_h: int,
    zoom_events: list[tuple[float, float, float]],
    tracking_enabled: bool,
    dead_zone_px: int,
    on_progress: ReframeProgress | None,
    loop: asyncio.AbstractEventLoop | None,
) -> tuple[CropMode, int]:
    """Roda o loop de crop em thread — CPU-bound. Retorna (crop_mode, frames)."""
    import cv2

    cap = cv2.VideoCapture(str(segment_video))
    if not cap.isOpened():
        raise ReframeError(f"OpenCV não abriu {segment_video}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(video_only_out), fourcc, fps, (out_w, out_h))
    if not writer.isOpened():
        cap.release()
        raise ReframeError("OpenCV VideoWriter falhou ao abrir")

    detector: FaceDetector | None = None
    if tracking_enabled:
        try:
            detector = FaceDetector()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Detector indisponível, fallback crop central: %s", exc)

    smoother = build_smoother(smoothing_kind)
    default_cx = src_w / 2.0
    default_cy = src_h / 2.0
    detections = 0
    frame_idx = 0
    last_progress_pct = -1

    # Zoom suavizado — aproximação exponencial ao target (15 frames ≈ 0.5s a 30fps)
    current_zoom = 1.0
    zoom_alpha = 0.15

    # Dead zone: aceita nova posição só quando o delta excede o limiar (em px do source)
    # Escala dead_zone_px (em px do output) para o espaço do source
    dead_zone_src = dead_zone_px * src_w / out_w if dead_zone_px > 0 else 0.0
    accepted_cx = default_cx
    accepted_cy = default_cy

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            t = frame_idx / fps

            if detector is not None and (frame_idx % max(1, detection_stride) == 0):
                center = detector.detect_center(frame)
                if center is not None:
                    detections += 1
                    smoother.update((float(center[0]), float(center[1])))
                else:
                    smoother.update(None)

            smoothed = smoother._last or (default_cx, default_cy)  # noqa: SLF001

            # Body offset: desloca 10% da altura para baixo para enquadrar ombros
            raw_cx = smoothed[0]
            raw_cy = smoothed[1] + src_h * 0.10

            # Dead zone: só reposiciona quando o movimento supera o limiar
            if dead_zone_src > 0:
                if abs(raw_cx - accepted_cx) > dead_zone_src or abs(raw_cy - accepted_cy) > dead_zone_src:
                    accepted_cx = raw_cx
                    accepted_cy = raw_cy
            else:
                accepted_cx = raw_cx
                accepted_cy = raw_cy

            # Zoom: crop uma área menor e escala para out_w×out_h
            target_zoom = _get_zoom_scale(t, zoom_events)
            current_zoom += (target_zoom - current_zoom) * zoom_alpha
            zoom = max(1.0, current_zoom)

            # Dimensões efetivas do crop antes de escalar ao output
            eff_h = int(round(out_h / zoom))
            eff_w = int(round(out_w / zoom))

            scale = eff_h / src_h
            scaled_w = int(round(src_w * scale))
            scaled = cv2.resize(frame, (scaled_w, eff_h), interpolation=cv2.INTER_AREA)

            sx = accepted_cx * scale
            x0 = int(round(sx - eff_w / 2))
            if scaled_w >= eff_w:
                x0 = max(0, min(scaled_w - eff_w, x0))
                cropped = scaled[:, x0 : x0 + eff_w]
            else:
                pad = (eff_w - scaled_w) // 2
                cropped = cv2.copyMakeBorder(
                    scaled, 0, 0, pad, eff_w - scaled_w - pad,
                    cv2.BORDER_CONSTANT, value=(0, 0, 0),
                )

            # Redimensiona para a resolução final (aplica o efeito de zoom)
            out_frame = cv2.resize(cropped, (out_w, out_h), interpolation=cv2.INTER_LINEAR)
            writer.write(out_frame)

            frame_idx += 1
            if on_progress is not None and loop is not None:
                pct = int(frame_idx * 100 / total)
                if pct != last_progress_pct:
                    last_progress_pct = pct
                    asyncio.run_coroutine_threadsafe(
                        on_progress(frame_idx / total, f"render frame {frame_idx}/{total}"),
                        loop,
                    )
    finally:
        cap.release()
        writer.release()
        if detector is not None:
            detector.close()

    crop_mode = CropMode.DYNAMIC if detections > 0 else CropMode.STATIC_FALLBACK
    return crop_mode, frame_idx


class OpenCVReframer:
    """Implementa IReframer usando OpenCV + FFmpeg."""

    async def reframe(
        self,
        source_video: Path,
        params: ReframeParams,
        on_progress: ReframeProgress | None = None,
    ) -> ReframeResult:
        if not source_video.exists():
            raise ReframeError(f"vídeo fonte não encontrado: {source_video}")

        params.output_path.parent.mkdir(parents=True, exist_ok=True)
        tmpdir = params.output_path.parent
        segment = tmpdir / f".{params.output_path.stem}_segment.mp4"
        video_only = tmpdir / f".{params.output_path.stem}_video.mp4"

        try:
            if on_progress:
                await on_progress(0.02, "extraindo segmento")
            await asyncio.to_thread(
                extract_segment, source_video, params.inicio, params.fim, segment
            )

            if on_progress:
                await on_progress(0.05, "iniciando reframe")

            loop = asyncio.get_running_loop()
            crop_mode, frames = await asyncio.to_thread(
                _reframe_sync,
                segment,
                video_only,
                params.detection_stride,
                params.smoothing,
                params.output_width,
                params.output_height,
                params.zoom_events,
                params.tracking_enabled,
                params.dead_zone_px,
                on_progress,
                loop,
            )

            if on_progress:
                await on_progress(0.95, "remuxando áudio")
            await asyncio.to_thread(mux_audio, video_only, segment, params.output_path)

            if on_progress:
                await on_progress(1.0, "concluído")
            return ReframeResult(
                output_path=params.output_path,
                crop_mode=crop_mode,
                frames_processed=frames,
            )
        finally:
            for p in (segment, video_only):
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
