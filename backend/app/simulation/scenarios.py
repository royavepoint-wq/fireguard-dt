from __future__ import annotations

from app.simulation.models import ScenarioDefinition, ScenarioSupportLevel

SCENARIOS: dict[str, ScenarioDefinition] = {
    "electrical-room-fire": ScenarioDefinition(
        scenario_id="electrical-room-fire",
        name="Electrical Room Fire",
        description="Deterministic end-to-end emergency scenario for the Electrical Room on Floor 1.",
        support_level=ScenarioSupportLevel.FULL,
        implementation_note="Fully implemented Step 4 deterministic timeline.",
    ),
    "blocked-exit": ScenarioDefinition(
        scenario_id="blocked-exit",
        name="Blocked Exit",
        description="Electrical room fire with Exit B blocked from the beginning.",
        support_level=ScenarioSupportLevel.PARAMETERIZED,
        initial_exit_b_blocked=True,
        implementation_note="Uses the fully implemented electrical-room-fire timeline with an initial blocked exit.",
    ),
    "peak-occupancy": ScenarioDefinition(
        scenario_id="peak-occupancy",
        name="Peak Occupancy",
        description="Electrical room fire with elevated occupancy and a larger affected zone.",
        support_level=ScenarioSupportLevel.PARAMETERIZED,
        initial_occupancy=312,
        affected_zone_occupancy=58,
        peak_occupancy=True,
        implementation_note="Uses the electrical-room-fire timeline with deterministic high-occupancy assumptions.",
    ),
    "hvac-smoke-propagation": ScenarioDefinition(
        scenario_id="hvac-smoke-propagation",
        name="HVAC Smoke Propagation",
        description="Electrical room fire with stronger smoke escalation before HVAC isolation.",
        support_level=ScenarioSupportLevel.PARAMETERIZED,
        hvac_smoke_propagation=True,
        implementation_note="Uses the electrical-room-fire timeline with deterministic smoke amplification.",
    ),
    "sprinkler-failure": ScenarioDefinition(
        scenario_id="sprinkler-failure",
        name="Sprinkler Failure",
        description="Electrical room fire where the sprinkler remains unavailable during containment.",
        support_level=ScenarioSupportLevel.PARAMETERIZED,
        sprinkler_failure=True,
        implementation_note="Uses the electrical-room-fire timeline with sprinkler activation disabled.",
    ),
    "sensor-anomaly": ScenarioDefinition(
        scenario_id="sensor-anomaly",
        name="Sensor Anomaly",
        description="Deterministic inconsistent sensor sequence that should raise an anomaly without escalating to a critical fire.",
        support_level=ScenarioSupportLevel.LIMITED,
        duration_seconds=60,
        sensor_anomaly_mode=True,
        implementation_note="Implements an anomaly-only deterministic sequence without a critical fire transition.",
    ),
}


def list_scenarios() -> list[ScenarioDefinition]:
    return list(SCENARIOS.values())


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    return SCENARIOS[scenario_id]