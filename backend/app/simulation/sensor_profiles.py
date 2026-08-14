from __future__ import annotations

from app.models.common import SensorHealth
from app.simulation.models import ScenarioDefinition, SensorProfile


def _interpolate(elapsed_seconds: int, points: list[tuple[int, float]]) -> float:
    if elapsed_seconds <= points[0][0]:
        return points[0][1]
    if elapsed_seconds >= points[-1][0]:
        return points[-1][1]

    for index in range(len(points) - 1):
        left_time, left_value = points[index]
        right_time, right_value = points[index + 1]
        if left_time <= elapsed_seconds <= right_time:
            span = right_time - left_time
            ratio = (elapsed_seconds - left_time) / span if span else 0.0
            return left_value + (right_value - left_value) * ratio
    return points[-1][1]


def build_sensor_profile(elapsed_seconds: int, scenario: ScenarioDefinition) -> SensorProfile:
    if scenario.sensor_anomaly_mode:
        return SensorProfile(
            temperature=_interpolate(elapsed_seconds, [(0, 24.6), (10, 25.1), (15, 26.0), (20, 27.0), (35, 28.0), (60, 25.2)]),
            smoke_level=_interpolate(elapsed_seconds, [(0, 0.02), (15, 0.02), (35, 0.03), (60, 0.02)]),
            co_level=_interpolate(elapsed_seconds, [(0, 4.0), (20, 4.2), (60, 4.0)]),
            co2_level=_interpolate(elapsed_seconds, [(0, 450), (60, 470)]),
            humidity=_interpolate(elapsed_seconds, [(0, 55), (60, 53)]),
            electrical_load=_interpolate(elapsed_seconds, [(0, 42), (10, 69), (25, 74), (60, 48)]),
            hvac_effect=0.1,
            sensor_health=SensorHealth.WARNING,
        )

    smoke_peak = 0.74 if not scenario.hvac_smoke_propagation else 0.88
    humidity_floor = 38 if not scenario.hvac_smoke_propagation else 34

    return SensorProfile(
        temperature=_interpolate(
            elapsed_seconds,
            [(0, 24.6), (10, 25.0), (20, 31.0), (35, 46.0), (50, 68.0), (70, 79.0), (85, 60.0), (105, 38.0), (120, 27.0)],
        ),
        smoke_level=_interpolate(
            elapsed_seconds,
            [(0, 0.02), (10, 0.04), (20, 0.08), (35, 0.24), (50, 0.52), (70, smoke_peak), (85, 0.42), (105, 0.12), (120, 0.03)],
        ),
        co_level=_interpolate(
            elapsed_seconds,
            [(0, 4.0), (10, 4.8), (20, 7.6), (35, 14.5), (50, 25.0), (70, 33.0), (85, 22.0), (105, 9.0), (120, 4.5)],
        ),
        co2_level=_interpolate(
            elapsed_seconds,
            [(0, 450), (20, 520), (35, 680), (50, 890), (70, 1100), (85, 900), (105, 600), (120, 470)],
        ),
        humidity=_interpolate(
            elapsed_seconds,
            [(0, 55), (20, 52), (35, 47), (50, 42), (70, humidity_floor), (85, 40), (105, 48), (120, 54)],
        ),
        electrical_load=_interpolate(
            elapsed_seconds,
            [(0, 42), (10, 54), (20, 69), (35, 84), (50, 92), (70, 95), (85, 78), (105, 56), (120, 44)],
        ),
        hvac_effect=_interpolate(
            elapsed_seconds,
            [(0, 0.15), (35, 0.08), (50, -0.05), (70, -0.18), (85, -0.24), (105, -0.05), (120, 0.12)],
        ),
        sensor_health=SensorHealth.HEALTHY,
    )