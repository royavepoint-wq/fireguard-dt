from __future__ import annotations

from app.services.evacuation.cost_model import BASE_WALKING_SPEED_MPS


def estimate_time_seconds(distance_meters: float, congestion_factor: float) -> float:
    effective_speed = max(0.35, BASE_WALKING_SPEED_MPS / max(1.0, congestion_factor))
    return distance_meters / effective_speed
