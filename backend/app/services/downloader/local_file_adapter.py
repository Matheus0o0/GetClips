"""Downloader trivial para arquivos já presentes no disco.

Permite reutilizar todo o pipeline para uploads locais.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.core.entities.media_file import MediaMetadata
from app.core.exceptions import UnsupportedSourceError
from app.core.interfaces.downloader import DownloadResult, ProgressCallback

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".m4v"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"}


class LocalFileDownloader:
    async def can_handle(self, source: str) -> bool:
        p = Path(source)
        return p.exists() and p.is_file() and p.suffix.lower() in (VIDEO_EXTS | AUDIO_EXTS)

    async def fetch_metadata(self, source: str) -> MediaMetadata:
        p = Path(source)
        return MediaMetadata(
            title=p.stem,
            platform="local",
            original_url=str(p),
        )

    async def download(
        self,
        source: str,
        output_dir: Path,
        audio_only: bool = False,
        on_progress: ProgressCallback | None = None,
    ) -> DownloadResult:
        src = Path(source)
        if not src.exists():
            raise UnsupportedSourceError(f"Arquivo local não encontrado: {source}")

        if on_progress:
            await on_progress(0.1, f"Copiando {src.name}")

        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / src.name
        if target.resolve() != src.resolve():
            shutil.copy2(src, target)

        if on_progress:
            await on_progress(1.0, "Arquivo pronto")

        return DownloadResult(
            file_path=target,
            metadata=await self.fetch_metadata(source),
            is_audio_only=src.suffix.lower() in AUDIO_EXTS,
        )
