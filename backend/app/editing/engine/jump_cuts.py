"""Remove segmentos (silêncio/filler) do vídeo usando o filtro select do FFmpeg.

O filtro select requer re-encode (não pode usar -c copy).
Usa libx264 + aac que estão disponíveis em praticamente toda build do FFmpeg.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from app.editing.plans.schema import RemoveSegment

logger = logging.getLogger(__name__)


def _ffmpeg(*args: str) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    logger.info("jump_cuts ffmpeg %s", " ".join(args))
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou: {p.stderr.decode(errors='ignore')[:400]}")


def apply_jump_cuts(
    input_path: Path,
    removes: list[RemoveSegment],
    output_path: Path,
    *,
    crf: int = 23,
    preset: str = "fast",
) -> None:
    """Remove os intervalos em `removes` do vídeo `input_path`.

    Se `removes` for vazio, faz cópia direta (sem re-encode).
    Os timestamps em `removes` devem ser relativos ao início de `input_path`.
    """
    if not removes:
        _ffmpeg("-i", str(input_path), "-c", "copy", str(output_path))
        return

    # Filtra remoções duplicadas/inválidas e ordena
    valid = sorted(
        [r for r in removes if r.end > r.start and r.end > 0],
        key=lambda r: r.start,
    )
    if not valid:
        _ffmpeg("-i", str(input_path), "-c", "copy", str(output_path))
        return

    # Constrói expressão: not(between(t,T1,T2)+between(t,T3,T4)+...)
    conds = "+".join(
        f"between(t,{r.start:.3f},{r.end:.3f})" for r in valid
    )
    vf = f"select='not({conds})',setpts=N/FRAME_RATE/TB"
    af = f"aselect='not({conds})',asetpts=N/SR/TB"

    _ffmpeg(
        "-i", str(input_path),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", preset,
        "-crf", str(crf),
        str(output_path),
    )
