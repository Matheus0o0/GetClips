"""Contrato do serviço de reframe (crop dinâmico vertical)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Protocol, runtime_checkable

from app.core.entities.clip import CropMode


@dataclass(slots=True)
class ReframeParams:
    inicio: float
    fim: float
    output_path: Path
    detection_stride: int = 5
    smoothing: str = "moving_average"
    output_width: int = 1080
    output_height: int = 1920
    # Lista de (start_sec, end_sec, scale) relativos ao início do segmento extraído
    zoom_events: list[tuple[float, float, float]] = field(default_factory=list)
    tracking_enabled: bool = True
    dead_zone_px: int = 0


@dataclass(slots=True)
class ReframeResult:
    output_path: Path
    crop_mode: CropMode
    frames_processed: int


ReframeProgress = Callable[[float, str], Awaitable[None]]


@runtime_checkable
class IReframer(Protocol):
    async def reframe(
        self,
        source_video: Path,
        params: ReframeParams,
        on_progress: ReframeProgress | None = None,
    ) -> ReframeResult: ...
