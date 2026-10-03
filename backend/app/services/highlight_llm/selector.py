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
You are a video editor. Select the best highlight clips from the transcript for Reels/Shorts.

IMPORTANT: Each clip must span MULTIPLE consecutive segments covering 30-60 seconds total.
Do NOT return individual segments — group them into longer clips.

Reply ONLY with valid JSON, no markdown, no extra text:
{"clips": [{"inicio": 45.0, "fim": 90.0, "hook": "opening phrase of the clip", "score": 0.9, "motivo": "why it is good"}, {"inicio": 310.0, "fim": 365.0, "hook": "another phrase", "score": 0.7, "motivo": "reason"}]}

Rules:
- inicio and fim are seconds (float), fim - inicio must be between 30 and 90 seconds
- hook is the first sentence spoken in the clip (string)
- score is 0.0 to 1.0 (float)
- motivo is a short reason (string)\
"""

# ponytail: amostra no máximo 120 segmentos distribuídos ao longo do vídeo —
# llama3.2 tem contexto de ~4k tokens; vídeos longos estouram e o modelo só regurgita
_MAX_SEGMENTS = 120


def _build_user_prompt(transcription: Transcription, params: HighlightParams) -> str:
    segs = transcription.segments
    if len(segs) > _MAX_SEGMENTS:
        step = len(segs) / _MAX_SEGMENTS
        segs = [segs[int(i * step)] for i in range(_MAX_SEGMENTS)]

    lines = [f"[{s.start_ms/1000:.1f}-{s.end_ms/1000:.1f}] {s.text.strip()}" for s in segs]
    body = "\n".join(lines)
    return (
        f"Video duration: {transcription.duration_seconds:.1f}s\n"
        f"Select up to {params.max_clips} clips, each {params.duration_min}-{params.duration_max}s long.\n\n"
        f"Transcript (sampled):\n{body}\n\n"
        'Return JSON: {"clips": [{"inicio": ..., "fim": ..., "hook": "...", "score": 0.9, "motivo": "..."}]}'
    )


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        match = re.search(r"\[.*\]", text, re.DOTALL) or re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise HighlightSelectionError(f"LLM não devolveu JSON: {exc}") from exc
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc2:
            raise HighlightSelectionError(f"LLM devolveu JSON inválido: {exc2}") from exc2
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
            # aceita variações de chave que modelos diferentes costumam usar
            raw_i = next((item[k] for k in ("inicio", "start_time", "start", "begin") if k in item), None)
            raw_f = next((item[k] for k in ("fim", "end_time", "end", "stop") if k in item), None)
            if raw_i is None or raw_f is None:
                raise KeyError("inicio/fim ausente")
            inicio = float(raw_i)
            fim = float(raw_f)
            hook = str(item.get("hook", item.get("text", ""))).strip()
            score = float(item.get("score", 0.5))
            motivo = str(item.get("motivo", item.get("reason", ""))).strip()
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


def _heuristic_clips(transcription: Transcription, params: HighlightParams) -> list[HighlightCandidate]:
    # ponytail: divide o vídeo em N clips igualmente espaçados — substitui LLM quando modelo é fraco
    dur = transcription.duration_seconds
    clip_len = (params.duration_min + params.duration_max) / 2
    n = min(params.max_clips, max(1, int(dur / clip_len)))
    step = dur / n
    clips = []
    for i in range(n):
        inicio = round(i * step, 1)
        fim = round(min(inicio + clip_len, dur), 1)
        if fim - inicio < params.duration_min:
            continue
        # pega o texto do primeiro segmento dentro do clip como hook
        hook = next(
            (s.text.strip() for s in transcription.segments if s.start_ms / 1000 >= inicio),
            "",
        )
        clips.append(HighlightCandidate(inicio=inicio, fim=fim, hook=hook, score=0.5, motivo="heurística"))
    return clips


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
        if provider == "none":
            return _heuristic_clips(transcription, params)
        if provider not in {"ollama", "openai", "anthropic"}:
            raise LLMNotConfiguredError(f"Provedor desconhecido: {provider}")

        try:
            if provider == "ollama":
                raw_text = await self._call_ollama(transcription, params)
            elif provider == "openai":
                raw_text = await self._call_openai(transcription, params)
            else:
                raw_text = await self._call_anthropic(transcription, params)

            logger.info("LLM raw response (primeiros 500 chars): %s", raw_text[:500])
            raw = _extract_json_array(raw_text)
            logger.info("candidatos parsed: %d", len(raw))
            candidates = _validate_candidates(raw, transcription.duration_seconds, params)
        except Exception as exc:
            logger.warning("LLM falhou (%s) — usando heurística de espaçamento igual", exc)
            candidates = []

        if not candidates:
            candidates = _heuristic_clips(transcription, params)
        return candidates

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
