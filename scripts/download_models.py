"""Pré-baixa modelos Whisper para uso offline.

Uso: python scripts/download_models.py distil-large-v3 base
"""
from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Uso: python scripts/download_models.py <modelo> [modelo ...]")
        print("Modelos: tiny, base, small, medium, large-v3, distil-large-v3")
        return 1

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper não instalado. Rode: pip install -e backend/")
        return 1

    models_dir = Path(__file__).resolve().parent.parent / "storage" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    for model_name in argv[1:]:
        print(f"==> Baixando modelo: {model_name}")
        WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            download_root=str(models_dir),
        )
        print(f"    OK: {model_name}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
