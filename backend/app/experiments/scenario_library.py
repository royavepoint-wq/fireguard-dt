from __future__ import annotations

from app.experiments.models import ExperimentScenarioDefinition, ScenarioReadiness

SCENARIO_LIBRARY: dict[str, ExperimentScenarioDefinition] = {
    "standard-electrical-fire": ExperimentScenarioDefinition(
        scenario_id="standard-electrical-fire",
        simulation_scenario_id="electrical-room-fire",
        name="Standard Electrical Fire",
        description="Baseline deterministic electrical-room fire scenario.",
        fire_origin="Electrical Room",
        fire_severity="High",
        occupancy=243,
        blocked_exits=[],
        hvac_state="Running",
        sprinkler_state="Ready",
        scenario_seed=101,
        readiness=ScenarioReadiness.READY,
    ),
    "blocked-exit": ExperimentScenarioDefinition(
        scenario_id="blocked-exit",
        simulation_scenario_id="blocked-exit",
        name="Blocked Exit",
        description="Electrical-room fire with exit-b unavailable from scenario start.",
        fire_origin="Electrical Room",
        fire_severity="High",
        occupancy=243,
        blocked_exits=["exit-b"],
        hvac_state="Running",
        sprinkler_state="Ready",
        scenario_seed=102,
        readiness=ScenarioReadiness.READY,
    ),
    "peak-occupancy": ExperimentScenarioDefinition(
        scenario_id="peak-occupancy",
        simulation_scenario_id="peak-occupancy",
        name="Peak Occupancy",
        description="Higher crowd density with deterministic occupancy surge.",
        fire_origin="Electrical Room",
        fire_severity="High",
        occupancy=312,
        blocked_exits=[],
        hvac_state="Running",
        sprinkler_state="Ready",
        scenario_seed=103,
        readiness=ScenarioReadiness.READY,
    ),
    "hvac-smoke": ExperimentScenarioDefinition(
        scenario_id="hvac-smoke",
        simulation_scenario_id="hvac-smoke-propagation",
        name="HVAC Smoke Propagation",
        description="Smoke escalation increases before HVAC isolation decision.",
        fire_origin="Electrical Room",
        fire_severity="High",
        occupancy=243,
        blocked_exits=[],
        hvac_state="Running",
        sprinkler_state="Ready",
        scenario_seed=104,
        readiness=ScenarioReadiness.READY,
    ),
    "sprinkler-failure": ExperimentScenarioDefinition(
        scenario_id="sprinkler-failure",
        simulation_scenario_id="sprinkler-failure",
        name="Sprinkler Failure",
        description="Suppression remains unavailable through containment window.",
        fire_origin="Electrical Room",
        fire_severity="High",
        occupancy=243,
        blocked_exits=[],
        hvac_state="Running",
        sprinkler_state="Failed",
        scenario_seed=105,
        readiness=ScenarioReadiness.READY,
    ),
    "sensor-anomaly": ExperimentScenarioDefinition(
        scenario_id="sensor-anomaly",
        simulation_scenario_id="sensor-anomaly",
        name="Sensor Anomaly",
        description="Deterministic anomaly path with limited critical-fire progression.",
        fire_origin="Electrical Room",
        fire_severity="Low",
        occupancy=243,
        blocked_exits=[],
        hvac_state="Running",
        sprinkler_state="Ready",
        scenario_seed=106,
        sensor_anomaly=True,
        readiness=ScenarioReadiness.LIMITED,
    ),
}


def get_scenario(scenario_id: str) -> ExperimentScenarioDefinition:
    return SCENARIO_LIBRARY[scenario_id]


def list_scenarios() -> list[ExperimentScenarioDefinition]:
    return list(SCENARIO_LIBRARY.values())
