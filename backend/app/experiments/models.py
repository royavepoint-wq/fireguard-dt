from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator

from app.models.common import APIModel, utc_now
from app.models.occupancy import RouteStrategy


class ScenarioReadiness(StrEnum):
    READY = "READY"
    LIMITED = "LIMITED"


class ApprovalMode(StrEnum):
    AUTO_APPROVE = "AUTO_APPROVE"
    FORCE_APPROVE = "FORCE_APPROVE"
    FORCE_REJECT = "FORCE_REJECT"


class ExperimentScenarioDefinition(APIModel):
    scenario_id: str
    simulation_scenario_id: str
    name: str
    description: str
    fire_origin: str
    fire_severity: str
    occupancy: int
    blocked_exits: list[str] = Field(default_factory=list)
    hvac_state: str
    sprinkler_state: str
    scenario_seed: int
    sensor_anomaly: bool = False
    resource_constraints: str | None = None
    readiness: ScenarioReadiness = ScenarioReadiness.READY


class ExperimentRunRequest(APIModel):
    scenario_ids: list[str] = Field(default_factory=list)
    strategies: list[RouteStrategy] = Field(default_factory=lambda: [RouteStrategy.STATIC_PLAN, RouteStrategy.SHORTEST_PATH, RouteStrategy.TWIN_OPTIMIZED])
    runs_per_configuration: int = 1
    include_governance_branches: bool = True

    @field_validator("runs_per_configuration")
    @classmethod
    def validate_runs(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("runs_per_configuration must be between 1 and 5")
        return value


class ExperimentResultRecord(APIModel):
    run_id: str
    scenario_id: str
    scenario_name: str
    strategy: RouteStrategy
    approval_mode: ApprovalMode = ApprovalMode.AUTO_APPROVE
    evacuation_time: float | None = None
    hazard_exposure_score: float | None = None
    peak_congestion: float | None = None
    unsafe_segment_count: int | None = None
    distance_travelled: float | None = None
    selected_exit: str | None = None
    time_to_warning: int | None = None
    time_to_critical: int | None = None
    time_to_evacuation: int | None = None
    time_to_first_dispatch: int | None = None
    time_to_first_response: int | None = None
    time_to_containment: int | None = None
    time_to_resolution: int | None = None
    occupants_at_risk: int | None = None
    occupants_evacuated: int | None = None
    resources_dispatched: int | None = None
    outcome_quality: str | None = None
    unsafe_zone_duration: int | None = None
    status: str = "COMPLETED"
    generated_at: datetime = Field(default_factory=utc_now)


class StrategyComparisonRecord(APIModel):
    scenario_id: str
    scenario_name: str
    strategy: RouteStrategy
    evacuation_time: float | None = None
    hazard_exposure_score: float | None = None
    peak_congestion: float | None = None
    distance_travelled: float | None = None
    selected_exit: str | None = None
    evacuation_time_change_vs_static_pct: float | None = None
    hazard_exposure_reduction_vs_static_pct: float | None = None
    congestion_reduction_vs_static_pct: float | None = None
    recommendation_label: str | None = None


class GovernanceComparisonRecord(APIModel):
    scenario_id: str
    branch: ApprovalMode
    containment_time: int | None = None
    hazard_exposure_score: float | None = None
    evacuation_time: float | None = None
    unsafe_zone_duration: int | None = None
    response_resources_used: int | None = None
    outcome_quality: str | None = None


class ExperimentStatusResponse(APIModel):
    is_running: bool = False
    progress: float = 0.0
    total_configurations: int = 0
    completed_configurations: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str | None = None


class ExperimentResultsResponse(APIModel):
    status: ExperimentStatusResponse
    scenario_results: list[ExperimentResultRecord] = Field(default_factory=list)
    strategy_comparison: list[StrategyComparisonRecord] = Field(default_factory=list)
    governance_comparison: list[GovernanceComparisonRecord] = Field(default_factory=list)
