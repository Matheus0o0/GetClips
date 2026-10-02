"""Detecta o melhor device (CUDA vs CPU) para faster-whisper."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def detect_device(preferred: str = "auto") -> tuple[str, str]:
    """Retorna (device, compute_type).

    preferred: 'auto' | 'cuda' | 'cpu'
    """
    if preferred not in {"auto", "cuda", "cpu"}:
        preferred = "auto"

    cuda_available = _cuda_available()

    if preferred == "cuda":
        if not cuda_available:
            logger.warning("CUDA solicitado mas não disponível — usando CPU.")
            return "cpu", "int8"
        return "cuda", "float16"

    if preferred == "cpu":
        return "cpu", "int8"

    # auto
    if cuda_available:
        return "cuda", "float16"
    return "cpu", "int8"


def _cuda_available() -> bool:
    """Best-effort: verifica se CTranslate2 vê alguma GPU."""
    try:
        import ctranslate2  # type: ignore[import-not-found]

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        pass
    try:
        import torch  # type: ignore[import-not-found]

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def resolve_compute_type(configured: str, device: str) -> str:
    if configured != "auto":
        return configured
    return "float16" if device == "cuda" else "int8"
