"""Provedor Ollama (API REST local compatível com OpenAI)."""
from __future__ import annotations

import logging

import httpx

from app.ai.llm.base import LLMMessage

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3.2"


class OllamaProvider:
    """Envia requisições ao Ollama local via endpoint /v1/chat/completions."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> str:
        # API nativa /api/chat com format:"json" — mais confiável que /v1/chat/completions
        # para modelos pequenos que às vezes retornam content vazio pelo endpoint OpenAI-compat.
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
        if r.status_code >= 400:
            raise RuntimeError(f"Ollama {r.status_code}: {r.text[:400]}")
        data = r.json()
        content = data.get("message", {}).get("content", "")
        if not content:
            logger.error("Ollama retornou content vazio. Resposta: %s", data)
            raise RuntimeError(
                f"Ollama retornou resposta vazia. Verifique se '{self._model}' "
                f"está baixado (`ollama pull {self._model}`)."
            )
        return content

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
            return r.status_code == 200
        except Exception:
            return False
