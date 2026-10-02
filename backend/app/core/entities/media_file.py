"""Entidades de arquivo de mídia."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class MediaKind(StrEnum):
    ORIGINAL_VIDEO = "original_video"
    ORIGINAL_AUDIO = "original_audio"
    PROCESSED_AUDIO = "processed_audio"
    SUBTITLE = "subtitle"
    TRANSCRIPT = "transcript"


@dataclass(slots=True)
class MediaFile:
    path: Path
    kind: MediaKind
    format: str
    size_bytes: int = 0
    duration_seconds: float | None = None

    @property
    def name(self) -> str:
        return self.path.name


@dataclass(slots=True)
class MediaMetadata:
    title: str | None = None
    duration_seconds: float | None = None
    platform: str | None = None
    uploader: str | None = None
    thumbnail_url: str | None = None
    original_url: str | None = None
    extra: dict[str, str] = field(default_factory=dict)
