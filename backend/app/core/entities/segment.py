"""Entidade Segment."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Segment:
    index: int
    start_ms: int
    end_ms: int
    text: str
    confidence: float = 0.0
    speaker_id: str | None = None

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
