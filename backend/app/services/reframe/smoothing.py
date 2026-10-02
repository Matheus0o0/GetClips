"""Suavização de posições de centro ao longo do tempo.

O crop dinâmico "treme" a cada micro-movimento sem isso.
Dois smoothers disponíveis:
  - MovingAverageSmoother: simples, sem dependências extras
  - KalmanSmoother: modela velocidade — melhor em movimentos bruscos e gaps de detecção
"""
from __future__ import annotations

from collections import deque


class MovingAverageSmoother:
    """Média móvel simples sobre as últimas N amostras (x, y)."""

    def __init__(self, window: int = 15) -> None:
        self._xs: deque[float] = deque(maxlen=window)
        self._ys: deque[float] = deque(maxlen=window)
        self._last: tuple[float, float] | None = None

    def update(self, point: tuple[float, float] | None) -> tuple[float, float] | None:
        if point is None:
            return self._last
        x, y = point
        self._xs.append(x)
        self._ys.append(y)
        sx = sum(self._xs) / len(self._xs)
        sy = sum(self._ys) / len(self._ys)
        self._last = (sx, sy)
        return self._last


class KalmanSmoother:
    """Filtro de Kalman 2D — estado [cx, cy, vx, vy], observação [cx, cy].

    Vantagens sobre moving average:
    - Mantém a estimativa de velocidade, recupera melhor após gaps de detecção
    - Não depende de janela de tamanho fixo
    - Parâmetros intuitivos: process_noise (quão rápido o alvo se move) e
      measurement_noise (quão "ruidosa" é a detecção)

    ponytail: measurement_noise assume detecção mediapipe com ~±10px de jitter.
    Aumentar process_noise se o alvo se mover muito rapidamente.
    """

    def __init__(
        self,
        process_noise: float = 0.05,
        measurement_noise: float = 15.0,
    ) -> None:
        import numpy as np

        # Transição: posição += velocidade (modelo de velocidade constante)
        self.F = np.eye(4, dtype=float)
        self.F[0, 2] = 1.0
        self.F[1, 3] = 1.0

        # Observação: mede apenas posição
        self.H = np.zeros((2, 4), dtype=float)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0

        self.Q = np.eye(4, dtype=float) * process_noise
        self.R = np.eye(2, dtype=float) * measurement_noise

        self._x: "np.ndarray | None" = None
        self._P = np.eye(4, dtype=float) * 500.0
        self._last: tuple[float, float] | None = None

    def update(self, point: tuple[float, float] | None) -> tuple[float, float] | None:
        import numpy as np

        if self._x is None:
            if point is None:
                return None
            self._x = np.array([point[0], point[1], 0.0, 0.0], dtype=float)
            self._last = (float(point[0]), float(point[1]))
            return self._last

        # Predição
        x_pred = self.F @ self._x
        P_pred = self.F @ self._P @ self.F.T + self.Q

        if point is not None:
            # Correção com medição
            z = np.array([point[0], point[1]], dtype=float)
            S = self.H @ P_pred @ self.H.T + self.R
            K = P_pred @ self.H.T @ np.linalg.inv(S)
            self._x = x_pred + K @ (z - self.H @ x_pred)
            self._P = (np.eye(4) - K @ self.H) @ P_pred
        else:
            # Sem detecção: só predição (mantém trajetória estimada)
            self._x = x_pred
            self._P = P_pred

        self._last = (float(self._x[0]), float(self._x[1]))
        return self._last


def build_smoother(kind: str = "kalman") -> KalmanSmoother | MovingAverageSmoother:
    if kind == "moving_average":
        return MovingAverageSmoother()
    # "kalman" ou qualquer valor desconhecido → Kalman (mais robusto)
    return KalmanSmoother()
