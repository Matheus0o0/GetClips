"""Gerador de legendas e transcrições em múltiplos formatos."""
from __future__ import annotations

from pathlib import Path

from app.core.entities.segment import Segment
from app.core.entities.transcription import Transcription

_FORMATS = ("srt", "vtt", "ass", "txt", "md")


def _ms_to_srt(ms: int) -> str:
    total_s, milli = divmod(int(ms), 1000)
    h, r = divmod(total_s, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def _ms_to_vtt(ms: int) -> str:
    total_s, milli = divmod(int(ms), 1000)
    h, r = divmod(total_s, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{milli:03d}"


def _ms_to_ass(ms: int) -> str:
    total_cs, _ = divmod(int(ms), 10)
    total_s, cs = divmod(total_cs, 100)
    h, r = divmod(total_s, 3600)
    m, s = divmod(r, 60)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


class SubtitleGenerator:
    def supported_formats(self) -> tuple[str, ...]:
        return _FORMATS

    async def generate(
        self,
        transcription: Transcription,
        target_dir: Path,
        base_name: str,
        formats: tuple[str, ...],
    ) -> dict[str, Path]:
        target_dir.mkdir(parents=True, exist_ok=True)
        outputs: dict[str, Path] = {}

        for fmt in formats:
            fmt = fmt.lower()
            if fmt not in _FORMATS:
                continue
            path = target_dir / f"{base_name}.{fmt}"
            content = self._render(fmt, transcription)
            path.write_text(content, encoding="utf-8")
            outputs[fmt] = path

        return outputs

    def _render(self, fmt: str, tr: Transcription) -> str:
        if fmt == "srt":
            return _render_srt(tr.segments)
        if fmt == "vtt":
            return _render_vtt(tr.segments)
        if fmt == "ass":
            return _render_ass(tr.segments)
        if fmt == "txt":
            return _render_txt(tr.segments)
        if fmt == "md":
            return _render_markdown(tr)
        raise ValueError(f"Formato não suportado: {fmt}")


def _render_srt(segments: list[Segment]) -> str:
    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_ms_to_srt(seg.start_ms)} --> {_ms_to_srt(seg.end_ms)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def _render_vtt(segments: list[Segment]) -> str:
    lines = ["WEBVTT", ""]
    for seg in segments:
        lines.append(f"{_ms_to_vtt(seg.start_ms)} --> {_ms_to_vtt(seg.end_ms)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def _render_ass(segments: list[Segment]) -> str:
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "Collisions: Normal\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,1,1,2,10,10,20,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for seg in segments:
        text = seg.text.strip().replace("\n", "\\N")
        lines.append(
            f"Dialogue: 0,{_ms_to_ass(seg.start_ms)},{_ms_to_ass(seg.end_ms)},Default,,0,0,0,,{text}"
        )
    return "\n".join(lines)


def _render_txt(segments: list[Segment]) -> str:
    return "\n".join(seg.text.strip() for seg in segments if seg.text.strip())


def _render_markdown(tr: Transcription) -> str:
    lines = [
        "# Transcrição",
        "",
        f"- **Idioma detectado:** {tr.language_detected} ({tr.language_probability:.0%})",
        f"- **Modelo:** {tr.model_used}",
        f"- **Duração:** {tr.duration_seconds:.1f}s",
        "",
        "## Segmentos",
        "",
    ]
    for seg in tr.segments:
        ts = f"[{_ms_to_srt(seg.start_ms)} → {_ms_to_srt(seg.end_ms)}]"
        lines.append(f"**{ts}** {seg.text.strip()}")
        lines.append("")
    return "\n".join(lines)
