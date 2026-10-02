"""Modelos Whisper suportados."""
from __future__ import annotations

from enum import StrEnum


class ModelType(StrEnum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V3 = "large-v3"
    DISTIL_LARGE_V3 = "distil-large-v3"

    @classmethod
    def list_all(cls) -> list[str]:
        return [m.value for m in cls]
