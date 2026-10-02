"""Entidade Transcription."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.entities.segment import Segment


@dataclass(slots=True)
class Transcription:
    segments: list[Segment] = field(default_factory=list)
    language_detected: str = "unknown"
    language_probability: float = 0.0
    model_used: str = ""
    duration_seconds: float = 0.0

    @property
    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())

    @property
    def average_confidence(self) -> float:
        if not self.segments:
            return 0.0
        return sum(s.confidence for s in self.segments) / len(self.segments)
