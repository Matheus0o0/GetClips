"""Contexto compartilhado entre steps do pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.entities import Job, Transcription
from app.core.entities.media_file import MediaMetadata


@dataclass(slots=True)
class JobContext:
    job: Job
    is_cancelled: bool = False

    downloaded_file: Path | None = None
    download_metadata: MediaMetadata | None = None

    audio_path: Path | None = None
    transcription: Transcription | None = None
    outputs: dict[str, Path] = field(default_factory=dict)

    def cancel(self) -> None:
        self.is_cancelled = True
