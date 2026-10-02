"""Provedor sem LLM: retorna JSON vazio. Usado quando nenhum runtime está disponível."""
from __future__ import annotations

from app.ai.llm.base import LLMMessage


class NoOpLLMProvider:
    """Retorna lista vazia. O orquestrador cai para seleção heurística."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> str:
        return "[]"

    async def is_available(self) -> bool:
        return False
