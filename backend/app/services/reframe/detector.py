"""Detector de rosto (primário) via MediaPipe.

Devolve o centro (x, y) do rosto principal em coordenadas de pixel do frame.
Se nada é detectado, retorna None e o chamador cai para crop central.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class FaceDetector:
    """Wrapper leve em torno do MediaPipe Face Detection.

    Import tardio: mediapipe é pesado e opcional para testes.
    """

    def __init__(self, min_confidence: float = 0.5) -> None:
        try:
            import mediapipe as mp  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "mediapipe não instalado. Instale com `pip install mediapipe`."
            ) from exc
        import mediapipe as mp

        self._mp = mp
        self._detector = mp.solutions.face_detection.FaceDetection(
            model_selection=1,  # long-range, funciona bem em quadro aberto
            min_detection_confidence=min_confidence,
        )
        self._last_center: tuple[int, int] | None = None

    def detect_center(self, frame_bgr) -> tuple[int, int] | None:
        """Recebe frame BGR (do OpenCV) e devolve (cx, cy) em pixels, ou None.

        Quando há múltiplos rostos, seleciona pelo score composto:
          área relativa × 0.6 + consistência temporal × 0.4
        """
        import cv2

        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self._detector.process(rgb)
        if not res.detections:
            return None

        if len(res.detections) == 1:
            best = res.detections[0]
        else:
            max_diag = (w * w + h * h) ** 0.5

            def _score(d) -> float:
                bb = d.location_data.relative_bounding_box
                area = bb.width * bb.height
                if self._last_center is not None:
                    cx_ = (bb.xmin + bb.width / 2) * w
                    cy_ = (bb.ymin + bb.height / 2) * h
                    dist = ((cx_ - self._last_center[0]) ** 2 + (cy_ - self._last_center[1]) ** 2) ** 0.5
                    temporal = 1.0 - dist / max_diag
                else:
                    temporal = 0.0
                return area * 0.6 + temporal * 0.4

            best = max(res.detections, key=_score)

        bbox = best.location_data.relative_bounding_box
        cx = int((bbox.xmin + bbox.width / 2) * w)
        cy = int((bbox.ymin + bbox.height / 2) * h)
        cx = max(0, min(w - 1, cx))
        cy = max(0, min(h - 1, cy))
        self._last_center = (cx, cy)
        return cx, cy

    def close(self) -> None:
        try:
            self._detector.close()
        except Exception:  # noqa: BLE001
            pass
