from __future__ import annotations

from app.models.common import RiskLevel
from app.simulation.models import ScenarioDefinition, SensorProfile, SimulationPhase
from app.simulation.timeline import get_phase_for_elapsed


def compute_rule_based_simulation_risk(sensor_profile: SensorProfile, elapsed_seconds: int, scenario: ScenarioDefinition) -> float:
    if scenario.sensor_anomaly_mode:
        inconsistent_sensor_penalty = 0.22 if 10 <= elapsed_seconds <= 35 else 0.05
        return round(min(0.38, inconsistent_sensor_penalty + max(sensor_profile.electrical_load - 40, 0) / 200), 2)

    temperature_component = min(max(sensor_profile.temperature - 24, 0) / 56, 0.3)
    smoke_component = min(sensor_profile.smoke_level / 0.85, 1.0) * 0.24
    co_component = min(sensor_profile.co_level / 35, 1.0) * 0.16
    rate_component = min(max(sensor_profile.temperature - 24, 0) / 70, 1.0) * 0.12
    electrical_component = min(sensor_profile.electrical_load / 100, 1.0) * 0.18
    return round(min(1.0, temperature_component + smoke_component + co_component + rate_component + electrical_component), 2)


def risk_level_from_score(score: float) -> RiskLevel:
    if score >= 0.70:
        return RiskLevel.CRITICAL
    if score >= 0.40:
        return RiskLevel.WARNING
    return RiskLevel.NORMAL


def phase_for_elapsed(elapsed_seconds: int, scenario: ScenarioDefinition) -> SimulationPhase:
    if scenario.sensor_anomaly_mode:
      if elapsed_seconds < 10:
          return SimulationPhase.NORMAL
      if elapsed_seconds < 35:
          return SimulationPhase.ANOMALY
      if elapsed_seconds < 50:
          return SimulationPhase.WARNING
      return SimulationPhase.RESOLVED
    return get_phase_for_elapsed(elapsed_seconds)