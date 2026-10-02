"""Checa disponibilidade de GPU CUDA para faster-whisper."""
from __future__ import annotations

import sys


def main() -> int:
    try:
        import torch  # type: ignore[import-not-found]
    except ImportError:
        print("[info] PyTorch não instalado — GPU não pode ser verificada por esse método.")
        print("[info] faster-whisper usa CTranslate2, que detecta CUDA independentemente.")
        return 0

    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA disponível: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Dispositivo: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"VRAM total: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
