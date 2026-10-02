"""Adapter yt-dlp — funciona para YouTube, TikTok, Instagram, Vimeo, URLs diretas etc."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings
from app.core.entities.media_file import MediaMetadata
from app.core.exceptions import UnsupportedSourceError
from app.core.interfaces.downloader import DownloadResult, ProgressCallback
from app.services.downloader.platform_resolver import identify_platform

logger = logging.getLogger(__name__)

_YT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _is_url(s: str) -> bool:
    try:
        parsed = urlparse(s)
        return parsed.scheme in {"http", "https"}
    except ValueError:
        return False


class YtDlpDownloader:
    async def can_handle(self, source: str) -> bool:
        return _is_url(source)

    async def fetch_metadata(self, source: str) -> MediaMetadata:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, self._extract_info, source)
        return _metadata_from_info(info, source)

    async def download(
        self,
        source: str,
        output_dir: Path,
        audio_only: bool = False,
        on_progress: ProgressCallback | None = None,
    ) -> DownloadResult:
        if not _is_url(source):
            raise UnsupportedSourceError(f"URL inválida: {source}")

        output_dir.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()

        # Bridge de progresso: yt-dlp roda sync; usamos asyncio.run_coroutine_threadsafe
        main_loop = asyncio.get_event_loop()

        def hook(d: dict[str, Any]) -> None:
            if not on_progress:
                return
            try:
                if d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes") or 0
                    pct = (downloaded / total) if total else 0.0
                    speed = d.get("speed") or 0
                    msg = f"Baixando ({downloaded/1e6:.1f} MB, {speed/1e6:.1f} MB/s)"
                    asyncio.run_coroutine_threadsafe(
                        on_progress(min(0.99, pct), msg), main_loop
                    )
                elif d.get("status") == "finished":
                    asyncio.run_coroutine_threadsafe(
                        on_progress(1.0, "Download concluído"), main_loop
                    )
            except Exception:
                pass

        info = await loop.run_in_executor(
            None, self._do_download, source, output_dir, audio_only, hook
        )

        file_path = _resolved_filepath(info, output_dir)
        metadata = _metadata_from_info(info, source)

        return DownloadResult(
            file_path=file_path,
            metadata=metadata,
            is_audio_only=audio_only,
        )

    # ---------------- helpers ----------------

    def _base_opts(self) -> dict[str, Any]:
        """Opts comuns a extract e download; inclui defesas anti-bloqueio do YouTube."""
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "http_headers": {"User-Agent": _YT_UA},
            "extractor_args": {
                # Ordem de fallback dos clients internos do YouTube.
                # 'android' e 'ios' costumam funcionar quando 'web' retorna
                # "Video unavailable".
                "youtube": {"player_client": ["android", "ios", "web"]}
            },
        }
        cookies_browser = get_settings().ytdlp_cookies_from_browser.strip()
        if cookies_browser:
            opts["cookiesfrombrowser"] = (cookies_browser,)
        return opts

    def _extract_info(self, url: str) -> dict[str, Any]:
        from yt_dlp import YoutubeDL

        opts = {**self._base_opts(), "skip_download": True}
        with YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _do_download(
        self,
        url: str,
        output_dir: Path,
        audio_only: bool,
        hook: Any,
    ) -> dict[str, Any]:
        from yt_dlp import YoutubeDL

        outtmpl = str(output_dir / "%(title).120s.%(ext)s")
        opts: dict[str, Any] = {
            **self._base_opts(),
            "outtmpl": outtmpl,
            "noprogress": True,
            "progress_hooks": [hook],
            "restrictfilenames": True,
        }

        if audio_only:
            opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "m4a",
                        }
                    ],
                }
            )
        else:
            opts.update(
                {
                    "format": "bestvideo*+bestaudio/best",
                    "merge_output_format": "mp4",
                }
            )

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info


def _resolved_filepath(info: dict[str, Any], output_dir: Path) -> Path:
    """yt-dlp guarda o path final em 'requested_downloads' ou 'filepath'."""
    requested = info.get("requested_downloads") or []
    if requested:
        p = requested[0].get("filepath")
        if p:
            return Path(p)
    fp = info.get("filepath") or info.get("_filename")
    if fp:
        return Path(fp)
    # Fallback: pega o arquivo mais recente na pasta
    files = sorted(output_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    if files:
        return files[0]
    raise UnsupportedSourceError("Não foi possível resolver o arquivo baixado")


def _metadata_from_info(info: dict[str, Any], original_url: str) -> MediaMetadata:
    return MediaMetadata(
        title=info.get("title"),
        duration_seconds=info.get("duration"),
        platform=identify_platform(original_url),
        uploader=info.get("uploader") or info.get("channel"),
        thumbnail_url=info.get("thumbnail"),
        original_url=original_url,
        extra={
            "extractor": str(info.get("extractor") or ""),
            "id": str(info.get("id") or ""),
        },
    )
