"""Idiomas suportados (ISO 639-1)."""
from __future__ import annotations

from enum import StrEnum


class Language(StrEnum):
    AUTO = "auto"
    PT = "pt"
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    JA = "ja"
    ZH = "zh"
    RU = "ru"

    @classmethod
    def is_valid(cls, code: str) -> bool:
        return code in cls._value2member_map_
