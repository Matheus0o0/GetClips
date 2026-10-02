"""Contrato para downloaders de mídia."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Protocol, runtime_checkable

from app.core.entities.media_file import MediaMetadata

ProgressCallback = Callable[[float, str], Awaitable[None]]


@dataclass(slots=True)
class DownloadResult:
    file_path: Path
    metadata: MediaMetadata
    is_audio_only: bool


@runtime_checkable
class IDownloader(Protocol):
    async def can_handle(self, source: str) -> bool: ...

    async def fetch_metadata(self, source: str) -> MediaMetadata: ...

    async def download(
        self,
        source: str,
        output_dir: Path,
        audio_only: bool = False,
        on_progress: ProgressCallback | None = None,
    ) -> DownloadResult: ...
