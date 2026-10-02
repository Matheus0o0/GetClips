"""Seleção de trechos para cortes via LLM (local via Ollama ou externa).

Apenas o TEXTO da transcrição (com timestamps) trafega para a LLM.
Nenhum vídeo/áudio é enviado.
"""
from __future__ import annotations

import json
import logging
import re

import httpx

from app.ai.llm.base import LLMMessage
from app.config import Settings
from app.core.entities.transcription import Transcription
from app.core.exceptions import HighlightSelectionError, LLMNotConfiguredError
from app.core.interfaces.highlight_selector import HighlightCandidate, HighlightParams

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é um editor de vídeo. Analise a transcrição e escolha os melhores trechos para Reels/Shorts.

Responda SOMENTE com JSON válido neste formato exato:
{"clips": [{"inicio": 12.5, "fim": 48.0, "hook": "frase de abertura do trecho", "score": 0.9, "motivo": "por que é bom"}, {"inicio": 95.0, "fim": 130.0, "hook": "outra frase", "score": 0.7, "motivo": "motivo"}]}

Regras:
- inicio e fim são números em segundos (float)
- hook é a primeira frase do trecho (string)
- score é de 0.0 a 1.0 (float)
- motivo é uma frase curta (string)
- Sem markdown, sem texto fora do JSON\
"""


def _build_user_prompt(transcription: Transcription, params: HighlightParams) -> str:
    lines: list[str] = []
    for s in transcription.segments:
        lines.append(f"[{s.start_ms/1000:.1f}-{s.end_ms/1000:.1f}] {s.text.strip()}")
    body = "\n".join(lines)
    return (
        f"Duração total do vídeo: {transcription.duration_seconds:.1f}s\n"
        f"Quero até {params.max_clips} cortes, cada um com duração entre "
        f"{params.duration_min}s e {params.duration_max}s.\n\n"
        f"Transcrição:\n{body}\n\n"
        'Devolva o JSON: {"clips": [...]}'
    )


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        # tenta pescar o primeiro array ou objeto
        match = re.search(r"\[.*\]", text, re.DOTALL) or re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise HighlightSelectionError(f"LLM não devolveu JSON: {exc}") from exc
        data = json.loads(match.group(0))
    # aceita {"clips": [...]} ou diretamente [...]
    if isinstance(data, dict):
        for key in ("clips", "cortes", "results", "highlights"):
            if isinstance(data.get(key), list):
                return data[key]
        raise HighlightSelectionError(f"JSON não contém lista de clips. Chaves: {list(data.keys())}")
    if not isinstance(data, list):
        raise HighlightSelectionError("Resposta da LLM não é uma lista JSON")
    return data


def _validate_candidates(
    raw: list[dict],
    total_duration: float,
    params: HighlightParams,
) -> list[HighlightCandidate]:
    out: list[HighlightCandidate] = []
    for item in raw:
        try:
            inicio = float(item["inicio"])
            fim = float(item["fim"])
            hook = str(item.get("hook", "")).strip()
            score = float(item.get("score", 0.0))
            motivo = str(item.get("motivo", "")).strip()
        except (KeyError, TypeError, ValueError):
            logger.warning("candidato inválido descartado: %s", item)
            continue
        # Regras: fim > inicio, dentro da duração, duração razoável
        if not (0.0 <= inicio < fim <= total_duration + 0.5):
            logger.warning("timestamp fora da duração: %s", item)
            continue
        dur = fim - inicio
        # Tolerância: aceita 80% do min e 130% do max — LLM aproxima
        if dur < params.duration_min * 0.8 or dur > params.duration_max * 1.3:
            logger.info("duração fora da faixa: %.1fs", dur)
            continue
        out.append(HighlightCandidate(inicio=inicio, fim=fim, hook=hook, score=score, motivo=motivo))
    out.sort(key=lambda c: c.score, reverse=True)
    return out[: params.max_clips]


class LLMHighlightSelector:
    """Adaptador para IHighlightSelector. Provedor definido no Settings."""

    def __init__(self, settings: Settings) -> None:
        self._s = settings

    async def select(
        self,
        transcription: Transcription,
        params: HighlightParams,
    ) -> list[HighlightCandidate]:
        provider = self._s.highlight_provider.lower()
        if provider == "ollama":
            raw_text = await self._call_ollama(transcription, params)
        elif provider == "openai":
            raw_text = await self._call_openai(transcription, params)
        elif provider == "anthropic":
            raw_text = await self._call_anthropic(transcription, params)
        elif provider == "none":
            return []
        else:
            raise LLMNotConfiguredError(f"Provedor desconhecido: {provider}")

        raw = _extract_json_array(raw_text)
        return _validate_candidates(raw, transcription.duration_seconds, params)

    async def _call_ollama(self, tr: Transcription, params: HighlightParams) -> str:
        from app.ai.llm.ollama_provider import OllamaProvider

        provider = OllamaProvider(
            base_url=self._s.ollama_base_url,
            model=self._s.ollama_model,
            timeout=self._s.ollama_timeout,
        )
        messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=_build_user_prompt(tr, params)),
        ]
        try:
            return await provider.complete(messages, temperature=0.4, max_tokens=4096)
        except RuntimeError as exc:
            raise HighlightSelectionError(str(exc)) from exc

    async def _call_openai(self, tr: Transcription, params: HighlightParams) -> str:
        key = self._s.openai_api_key.strip()
        if not key:
            raise LLMNotConfiguredError("OPENAI_API_KEY não configurada")
        payload = {
            "model": self._s.openai_model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(tr, params)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
        }
        # ponytail: pedimos json_object; alguns modelos exigem "json" no prompt.
        payload["messages"][1]["content"] += "\nRetorne no formato: {\"clips\": [ ... ]}"
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
            )
        if r.status_code >= 400:
            raise HighlightSelectionError(f"OpenAI {r.status_code}: {r.text[:400]}")
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        # Se veio como {"clips": [...]}, extrai; senão devolve como está
        try:
            wrapped = json.loads(content)
            if isinstance(wrapped, dict) and "clips" in wrapped:
                return json.dumps(wrapped["clips"])
        except json.JSONDecodeError:
            pass
        return content

    async def _call_anthropic(self, tr: Transcription, params: HighlightParams) -> str:
        key = self._s.anthropic_api_key.strip()
        if not key:
            raise LLMNotConfiguredError("ANTHROPIC_API_KEY não configurada")
        payload = {
            "model": self._s.anthropic_model,
            "max_tokens": 2048,
            "system": _SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": _build_user_prompt(tr, params)},
            ],
        }
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
        if r.status_code >= 400:
            raise HighlightSelectionError(f"Anthropic {r.status_code}: {r.text[:400]}")
        data = r.json()
        return data["content"][0]["text"]
