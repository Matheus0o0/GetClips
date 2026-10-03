"""Adapter FFmpeg — extração e normalização de áudio."""
from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path

from app.core.exceptions import AudioProcessingError
from app.core.interfaces.audio_processor import AudioSpec

logger = logging.getLogger(__name__)


def _run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess:
    # ponytail: subprocess.run em vez de asyncio.create_subprocess_exec —
    # SelectorEventLoop do Windows não suporta subprocess async; to_thread resolve.
    return subprocess.run(args, capture_output=True)


class FFmpegAudioProcessor:
    async def extract_audio(
        self,
        source: Path,
        target_dir: Path,
        spec: AudioSpec | None = None,
    ) -> Path:
        spec = spec or AudioSpec()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{source.stem}.wav"

        args = [
            "ffmpeg", "-y", "-i", str(source),
            "-vn", "-ac", str(spec.channels),
            "-ar", str(spec.sample_rate),
            "-acodec", spec.codec,
            str(target),
        ]

        result = await asyncio.to_thread(_run_ffmpeg, args)

        if result.returncode != 0:
            msg = (result.stderr or b"").decode(errors="ignore")[-500:]
            raise AudioProcessingError(f"FFmpeg falhou ({result.returncode}): {msg}")

        if not target.exists() or target.stat().st_size == 0:
            raise AudioProcessingError("FFmpeg terminou mas não gerou saída válida")

        return target

    async def probe_duration(self, source: Path) -> float:
        args = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(source),
        ]
        result = await asyncio.to_thread(_run_ffmpeg, args)
        try:
            return float((result.stdout or b"").decode().strip())
        except ValueError:
            return 0.0
