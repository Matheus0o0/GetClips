"""Contrato de processador de áudio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class AudioSpec:
    sample_rate: int = 16000
    channels: int = 1
    codec: str = "pcm_s16le"
    format: str = "wav"


@runtime_checkable
class IAudioProcessor(Protocol):
    async def extract_audio(
        self,
        source: Path,
        target_dir: Path,
        spec: AudioSpec | None = None,
    ) -> Path: ...

    async def probe_duration(self, source: Path) -> float: ...
