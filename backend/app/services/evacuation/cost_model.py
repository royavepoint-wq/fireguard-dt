from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteCostWeights:
    distance: float = 1.0
    fire: float = 8.0
    smoke: float = 6.0
    crowd: float = 2.5


BASE_WALKING_SPEED_MPS = 1.2
