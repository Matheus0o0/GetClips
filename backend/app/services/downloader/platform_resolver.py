"""Identifica a plataforma a partir de uma URL."""
from __future__ import annotations

from urllib.parse import urlparse

PLATFORMS: dict[str, tuple[str, ...]] = {
    "youtube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "tiktok": ("tiktok.com", "vm.tiktok.com"),
    "instagram": ("instagram.com",),
    "facebook": ("facebook.com", "fb.watch"),
    "twitter": ("twitter.com", "x.com"),
    "vimeo": ("vimeo.com",),
}


def identify_platform(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return "unknown"
    host = host.removeprefix("www.").removeprefix("m.")
    for name, domains in PLATFORMS.items():
        if any(host.endswith(d) for d in domains):
            return name
    return "direct" if host else "unknown"
