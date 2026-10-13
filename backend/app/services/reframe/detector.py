"""Detector de rosto via MediaPipe Tasks API (v1.0+)."""
from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models"
    "/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
)
_MODEL_NAME = "blaze_face_short_range.tflite"


def _ensure_model(models_dir: Path | None = None) -> Path:
    base = models_dir or Path.home() / ".cache" / "mediapipe"
    base.mkdir(parents=True, exist_ok=True)
    dst = base / _MODEL_NAME
    if not dst.exists():
        logger.info("Baixando modelo MediaPipe → %s", dst)
        urllib.request.urlretrieve(_MODEL_URL, dst)
    return dst


class FaceDetector:
    """Wrapper sobre MediaPipe Tasks FaceDetector.

    Com múltiplos rostos: score = área×0.6 + consistência_temporal×0.4
    """

    def __init__(self, min_confidence: float = 0.5, models_dir: Path | None = None) -> None:
        try:
            from mediapipe.tasks import python as _mp  # noqa: F401
            from mediapipe.tasks.python import vision as _v  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "mediapipe não instalado. Instale com `pip install mediapipe`."
            ) from exc

        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision

        model_path = _ensure_model(models_dir)
        opts = vision.FaceDetectorOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(model_path)),
            min_detection_confidence=min_confidence,
        )
        self._detector = vision.FaceDetector.create_from_options(opts)
        self._last_center: tuple[int, int] | None = None

    def detect_center(self, frame_bgr) -> tuple[int, int] | None:
        """Recebe frame BGR (OpenCV) e devolve (cx, cy) em pixels, ou None."""
        import cv2
        import mediapipe as mp

        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._detector.detect(mp_image)

        if not result.detections:
            return None

        max_diag = (w * w + h * h) ** 0.5

        def _score(d) -> float:
            bb = d.bounding_box
            area = (bb.width * bb.height) / (w * h)
            if self._last_center is not None:
                cx_ = bb.origin_x + bb.width / 2
                cy_ = bb.origin_y + bb.height / 2
                dist = ((cx_ - self._last_center[0]) ** 2 + (cy_ - self._last_center[1]) ** 2) ** 0.5
                temporal = 1.0 - dist / max_diag
            else:
                temporal = 0.0
            return area * 0.6 + temporal * 0.4

        best = max(result.detections, key=_score)
        bb = best.bounding_box
        cx = int(bb.origin_x + bb.width / 2)
        cy = int(bb.origin_y + bb.height / 2)
        cx = max(0, min(w - 1, cx))
        cy = max(0, min(h - 1, cy))
        self._last_center = (cx, cy)
        return cx, cy

    def close(self) -> None:
        try:
            self._detector.close()
        except Exception:  # noqa: BLE001
            pass
