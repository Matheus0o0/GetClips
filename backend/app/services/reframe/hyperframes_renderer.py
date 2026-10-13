"""Reframer 9:16 com face tracking Python + render final via HyperFrames.

Pipeline:
  1. ffmpeg extrai segmento
  2. OpenCV + FaceDetector amostram posições do rosto
  3. Gera composição HyperFrames (HTML + keyframes GSAP)
  4. npx hyperframes render → MP4 final com crop dinâmico
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.entities.clip import CropMode
from app.core.interfaces.reframer import ReframeParams, ReframeProgress, ReframeResult
from app.services.reframe.render import ReframeError, extract_segment
from app.services.reframe.smoothing import build_smoother

logger = logging.getLogger(__name__)

# ponytail: browser-render é ~5× mais lento que OpenCV puro.
# Troque por OpenCVReframer em container.py se throughput for crítico.
_NPX = shutil.which("npx") or ("npx.cmd" if sys.platform == "win32" else "npx")


class HyperFramesReframer:
    """Implementa IReframer: face tracking em Python, rendering via HyperFrames."""

    def __init__(self, models_dir: Path | None = None) -> None:
        self._models_dir = models_dir

    async def reframe(
        self,
        source_video: Path,
        params: ReframeParams,
        on_progress: ReframeProgress | None = None,
    ) -> ReframeResult:
        if not source_video.exists():
            raise ReframeError(f"vídeo não encontrado: {source_video}")

        params.output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            segment = tmp / "segment.mp4"
            public = tmp / "public"
            public.mkdir()

            if on_progress:
                await on_progress(0.02, "extraindo segmento")
            await asyncio.to_thread(extract_segment, source_video, params.inicio, params.fim, segment)

            src_w, src_h, fps = await asyncio.to_thread(_probe_video, segment)
            duration = params.fim - params.inicio

            if on_progress:
                await on_progress(0.08, "detectando rosto")
            face_positions: dict[float, int] = {}
            if params.tracking_enabled:
                face_positions = await asyncio.to_thread(
                    _sample_faces, segment, fps, params.detection_stride, self._models_dir
                )
            crop_mode = CropMode.DYNAMIC if face_positions else CropMode.STATIC_FALLBACK

            # Re-encode com keyframes densos para seek correto no browser
            if on_progress:
                await on_progress(0.12, "preparando vídeo")
            await asyncio.to_thread(_prepare_for_hf, segment, public / "video.mp4", int(round(fps)))

            scale = params.output_height / src_h
            html = _make_composition(
                duration=duration,
                fps=fps,
                out_w=params.output_width,
                out_h=params.output_height,
                scaled_w=int(src_w * scale),
                scale=scale,
                face_positions=face_positions,
            )
            (public / "index.html").write_text(html, encoding="utf-8")

            if on_progress:
                await on_progress(0.18, "renderizando via HyperFrames")
            await asyncio.to_thread(_hf_render, public, params.output_path)

            if on_progress:
                await on_progress(1.0, "concluído")

        return ReframeResult(
            output_path=params.output_path,
            crop_mode=crop_mode,
            frames_processed=int(duration * fps),
        )


def _probe_video(path: Path) -> tuple[int, int, float]:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    s = json.loads(r.stdout)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return s["width"], s["height"], float(num) / float(den)


def _prepare_for_hf(src: Path, dst: Path, fps: int) -> None:
    """Re-encode com GOP curto para seek frame-a-frame no browser."""
    proc = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(src),
         "-c:v", "libx264", "-crf", "18",
         "-g", str(fps), "-keyint_min", str(fps),
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-c:a", "aac",
         str(dst)],
        capture_output=True,
    )
    if proc.returncode != 0:
        shutil.copy2(src, dst)


def _sample_faces(
    video: Path, fps: float, stride: int, models_dir: Path | None
) -> dict[float, int]:
    import cv2
    from app.services.reframe.detector import FaceDetector

    detector = FaceDetector(models_dir=models_dir)
    smoother = build_smoother("kalman")
    positions: dict[float, int] = {}

    cap = cv2.VideoCapture(str(video))
    try:
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % max(1, stride) == 0:
                center = detector.detect_center(frame)
                smoothed = smoother.update(
                    (float(center[0]), float(center[1])) if center else None
                )
                if smoothed:
                    positions[idx / fps] = int(smoothed[0])
            idx += 1
    finally:
        cap.release()
        detector.close()

    return positions


def _make_composition(
    duration: float,
    fps: float,
    out_w: int,
    out_h: int,
    scaled_w: int,
    scale: float,
    face_positions: dict[float, int],
) -> str:
    fps_int = max(1, int(round(fps)))
    initial_left = (out_w - scaled_w) // 2  # centro como fallback

    keyframes: list[str] = []
    prev_left = initial_left
    for t, fx in sorted(face_positions.items()):
        # Centraliza o rosto no frame de saída
        left = out_w // 2 - int(fx * scale)
        # Garante que o vídeo não deixe bordas pretas
        left = max(out_w - scaled_w, min(0, left))
        if left != prev_left:
            keyframes.append(
                f"tl.to('#src-v',{{left:{left},duration:0.4,ease:'power2.inOut'}},{t:.3f});"
            )
            prev_left = left

    kf_js = "\n      ".join(keyframes) if keyframes else "// sem detecção — crop central estático"

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width={out_w},height={out_h}">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{out_w}px;height:{out_h}px;overflow:hidden;background:#000}}
#stage{{position:relative;width:100%;height:100%}}
#vhost{{position:absolute;overflow:hidden;left:0;top:0;width:{out_w}px;height:{out_h}px}}
#src-v{{position:absolute;top:0;left:{initial_left}px;height:{out_h}px;width:{scaled_w}px}}
</style>
</head><body>
<div id="stage"
  data-composition-id="clip"
  data-start="0"
  data-duration="{duration:.3f}"
  data-fps="{fps_int}"
  data-width="{out_w}"
  data-height="{out_h}">
  <div id="vhost">
    <video id="src-v" src="video.mp4" playsinline
      data-has-audio="true"
      data-start="0"
      data-duration="{duration:.3f}"
      data-track-index="1"></video>
  </div>
  <script>
    (function(){{
      const tl=window.gsap.timeline({{paused:true}});
      {kf_js}
      window.__timelines=window.__timelines||{{}};
      window.__timelines["clip"]=tl;
    }})();
  </script>
</div>
</body></html>"""


def _hf_render(public_dir: Path, output: Path) -> None:
    proc = subprocess.run(
        [_NPX, "--yes", "hyperframes", "render", str(public_dir),
         "--output", str(output), "--quality", "looks"],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise ReframeError(
            f"hyperframes render falhou (verifique se o browser está instalado: "
            f"`npx hyperframes doctor`):\n{proc.stderr[-600:]}"
        )
