"""Divide segmentos de transcrição em blocos de N palavras com timing proporcional.

Sem word timestamps do Whisper, o tempo de cada palavra é estimado proporcionalmente
dentro do segmento. Quando word_timestamps=True for habilitado (fase futura),
esta função pode ser atualizada para usar timing exato.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.entities.segment import Segment


@dataclass(slots=True)
class CaptionBlock:
    text: str          # texto em MAIÚSCULAS, N palavras
    start_ms: int      # relativo ao início do clip
    end_ms: int
    is_emphasis: bool  # palavra importante (destaque visual)


def chunk_segments(
    segments: list[Segment],
    clip_start_ms: int,
    clip_end_ms: int,
    words_per_block: int = 3,
    max_chars: int = 25,
    emphasis_texts: frozenset[str] | None = None,
) -> list[CaptionBlock]:
    """
    Retorna lista de CaptionBlock com timestamps relativos ao início do clip.

    Regras:
    - Blocos de até `words_per_block` palavras
    - Nunca ultrapassa `max_chars` caracteres (quebra antes se necessário)
    - Tempo proporcional à contagem de palavras no segmento
    - Segmentos fora de [clip_start_ms, clip_end_ms] são ignorados
    """
    blocks: list[CaptionBlock] = []
    emphasis = emphasis_texts or frozenset()
    offset = clip_start_ms

    for seg in segments:
        if seg.end_ms <= clip_start_ms or seg.start_ms >= clip_end_ms:
            continue

        words = seg.text.strip().split()
        if not words:
            continue

        seg_dur = max(1, seg.end_ms - seg.start_ms)
        total = len(words)
        i = 0

        while i < total:
            group: list[str] = []
            chars = 0

            j = i
            while j < total and len(group) < words_per_block:
                w = words[j]
                sep = 1 if group else 0
                if chars + sep + len(w) > max_chars and group:
                    break
                group.append(w)
                chars += sep + len(w)
                j += 1

            if not group:
                i += 1
                continue

            # Timing proporcional ao número de palavras no segmento
            t0 = seg.start_ms + int((i / total) * seg_dur)
            t1 = seg.start_ms + int((j / total) * seg_dur)

            # Offset relativo ao clip; garante mínimo de 300ms de exibição
            t0 = max(0, t0 - offset)
            t1 = max(0, t1 - offset)
            if t1 - t0 < 300:
                t1 = t0 + 300

            is_em = any(w.lower().strip(".,!?;:") in emphasis for w in group)
            blocks.append(CaptionBlock(
                text=" ".join(group).upper(),
                start_ms=t0,
                end_ms=t1,
                is_emphasis=is_em,
            ))
            i = j

    return blocks
