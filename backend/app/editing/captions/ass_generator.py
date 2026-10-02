"""Gera arquivo ASS (Advanced SubStation Alpha) a partir de CaptionBlocks.

ASS é renderizado pelo filtro `subtitles=` do FFmpeg (libass) e suporta:
  - Bold/weight via flag na style
  - Cores personalizadas
  - Posicionamento exato por pixel
  - Animações via \\t() — usadas para o efeito pop
  - Destaque de palavras via mudança de cor por evento
"""
from __future__ import annotations

import sys

from app.editing.captions.chunker import CaptionBlock
from app.editing.templates.model import CaptionConfig


def _rgb_to_ass(hex_color: str) -> str:
    """#RRGGBB → &H00BBGGRR (formato BGR do ASS)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _ass_time(ms: int) -> str:
    """Milliseconds → H:MM:SS.cc (centisegundos como no ASS)."""
    ms = max(0, ms)
    s, cs_rem = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}.{cs_rem // 10:02d}"


def _animation_tags(animation: str) -> str:
    match animation:
        case "pop":
            # Escala de 100→120→100 nos primeiros 300ms
            return r"\t(0,150,\fscx120\fscy120)\t(150,300,\fscx100\fscy100)"
        case "fade":
            return r"\fad(200,100)"
        case _:
            return ""


def ass_path_for_ffmpeg(p: "Path") -> str:  # noqa: F821
    """Converte Path para o formato aceito pelo filtro subtitles= do FFmpeg.

    No Windows, o separador e os dois-pontos do drive precisam de escape.
    """
    import sys
    from pathlib import Path as _Path

    s = str(p).replace("\\", "/")
    if sys.platform == "win32" and len(s) >= 2 and s[1] == ":":
        # C:/... → C\\:/...
        s = s[0] + "\\:" + s[2:]
    return s


def generate_ass(
    blocks: list[CaptionBlock],
    config: CaptionConfig,
    output_width: int = 1080,
    output_height: int = 1920,
) -> str:
    bold_flag = -1 if config.font_weight >= 700 else 0
    primary_color = _rgb_to_ass(config.color)
    outline_color = _rgb_to_ass(config.outline_color)
    highlight_color = _rgb_to_ass(config.highlight_color)
    bg_alpha = "&H80000000"  # semi-transparente; "transparent" = sem fundo

    # Posição em pixels (0,0 = canto sup. esq.)
    x = int(config.position_x * output_width)
    y = int(config.position_y * output_height)

    # Margem lateral para evitar texto colado nas bordas
    margin_lr = max(20, int(output_width * 0.04))

    header = (
        "[Script Info]\n"
        "Title: Shorts Captions\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {output_width}\n"
        f"PlayResY: {output_height}\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{config.font_family},{config.font_size},"
        f"{primary_color},&H000000FF,{outline_color},{bg_alpha},"
        f"{bold_flag},0,0,0,100,100,0,0,1,{config.outline_width},2,"
        f"2,{margin_lr},{margin_lr},40,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    anim = _animation_tags(config.animation)
    lines: list[str] = [header]

    for block in blocks:
        t0 = _ass_time(block.start_ms)
        t1 = _ass_time(block.end_ms)

        color_tag = (
            f"\\c{highlight_color}"
            if block.is_emphasis and config.highlight_emphasis
            else ""
        )

        # \an2 = alinhamento inferior-centro; \pos sobrescreve posição
        tags = f"\\an2\\pos({x},{y}){anim}{color_tag}"
        lines.append(f"Dialogue: 0,{t0},{t1},Default,,0,0,0,,{{{tags}}}{block.text}")

    return "\n".join(lines)
