"""Resolução de caminhos de armazenamento por job."""
from __future__ import annotations

import re
from pathlib import Path

from app.config import Settings

_INVALID = re.compile(r"[^\w\-.]+", flags=re.UNICODE)


def slugify(value: str, max_len: int = 80) -> str:
    v = _INVALID.sub("_", value.strip())
    v = v.strip("._")
    return (v or "arquivo")[:max_len]


class PathResolver:
    def __init__(self, settings: Settings) -> None:
        self._s = settings

    def job_download_dir(self, job_id: str) -> Path:
        p = self._s.downloads_dir / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_audio_dir(self, job_id: str) -> Path:
        p = self._s.audio_dir / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_subtitles_dir(self, job_id: str) -> Path:
        p = self._s.subtitles_dir / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_transcripts_dir(self, job_id: str) -> Path:
        p = self._s.transcripts_dir / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_temp_dir(self, job_id: str) -> Path:
        p = self._s.temp_dir / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_clips_dir(self, job_id: str) -> Path:
        p = self._s.clips_dir / job_id
        p.mkdir(parents=True, exist_ok=True)
        return p
