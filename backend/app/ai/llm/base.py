"""Contrato do provedor de LLM local."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class LLMMessage:
    role: str   # "system" | "user" | "assistant"
    content: str


@runtime_checkable
class LocalLLMProvider(Protocol):
    """Interface mínima para qualquer runtime de LLM local."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> str:
        """Retorna o texto da resposta."""
        ...

    async def is_available(self) -> bool:
        """True se o runtime/modelo estiver acessível."""
        ...
