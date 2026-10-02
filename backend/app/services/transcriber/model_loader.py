"""Cache de carregamento de modelos Whisper."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ModelLoader:
    """Mantém um único WhisperModel carregado por (nome, device, compute).

    Trocar de modelo em runtime libera o anterior.
    """

    def __init__(self, models_dir: Path) -> None:
        self._models_dir = models_dir
        self._lock = threading.Lock()
        self._current_key: tuple[str, str, str] | None = None
        self._current_model: Any | None = None

    def get(self, model_name: str, device: str, compute_type: str) -> Any:
        key = (model_name, device, compute_type)
        with self._lock:
            if self._current_key == key and self._current_model is not None:
                return self._current_model

            logger.info(
                "Carregando modelo Whisper", extra={"component": "model_loader"}
            )
            from faster_whisper import WhisperModel

            self._models_dir.mkdir(parents=True, exist_ok=True)
            try:
                model = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                    download_root=str(self._models_dir),
                )
                effective_key = key
            except Exception as exc:
                # Fallback resiliente: CUDA detectado mas libs ausentes → cai pra CPU
                if device == "cuda":
                    logger.warning(
                        "Falha ao carregar em CUDA (%s). Fazendo fallback para CPU.", exc
                    )
                    model = WhisperModel(
                        model_name,
                        device="cpu",
                        compute_type="int8",
                        download_root=str(self._models_dir),
                    )
                    effective_key = (model_name, "cpu", "int8")
                else:
                    raise

            self._current_key = effective_key
            self._current_model = model
            return model
