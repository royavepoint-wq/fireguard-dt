from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from app.models.common import APIModel, RiskLevel, utc_now
from app.models.ml import PredictionSource


class SimulationStatus(StrEnum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class SimulationPhase(StrEnum):
    NORMAL = "NORMAL"
    ANOMALY = "ANOMALY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EVACUATION = "EVACUATION"
    RESPONSE = "RESPONSE"
    CONTAINMENT = "CONTAINMENT"
    RESOLVED = "RESOLVED"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SimulationPauseReason(StrEnum):
    MANUAL = "MANUAL"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"


class GovernanceDecision(StrEnum):
    PENDING = "PENDING"
    HVAC_ISOLATION_APPROVED = "HVAC_ISOLATION_APPROVED"
    HVAC_ISOLATION_REJECTED = "HVAC_ISOLATION_REJECTED"


class OutcomeQuality(StrEnum):
    OPTIMAL = "OPTIMAL"
    DEGRADED = "DEGRADED"


class ScenarioSupportLevel(StrEnum):
    FULL = "FULL"
    PARAMETERIZED = "PARAMETERIZED"
    LIMITED = "LIMITED"


class ScenarioDefinition(APIModel):
    scenario_id: str
    name: str
    description: str
    building_id: str = "FG-BLDG-01"
    floor_id: str = "floor-1"
    origin_zone_id: str = "room-electrical-01"
    affected_corridor_id: str = "corridor-c"
    duration_seconds: int = 120
    initial_occupancy: int = 243
    affected_zone_occupancy: int = 43
    support_level: ScenarioSupportLevel = ScenarioSupportLevel.FULL
    initial_exit_b_blocked: bool = False
    peak_occupancy: bool = False
    hvac_smoke_propagation: bool = False
    sprinkler_failure: bool = False
    sensor_anomaly_mode: bool = False
    implementation_note: str = "Fully implemented deterministic scenario."


class ApprovalState(APIModel):
    approval_id: str
    action_type: str
    action_description: str
    risk_level: RiskLevel
    requested_simulation_time: int
    status: ApprovalStatus
    requested_at: datetime = Field(default_factory=utc_now)
    decision: ApprovalStatus | None = None
    decided_at: datetime | None = None
    decision_source: str | None = None
    auto_approve: bool = True
    message: str


class SimulationState(APIModel):
    simulation_id: str = "sim-fireguard-dt"
    scenario_id: str | None = None
    scenario_name: str | None = None
    status: SimulationStatus = SimulationStatus.STOPPED
    phase: SimulationPhase = SimulationPhase.NORMAL
    elapsed_seconds: int = 0
    speed_multiplier: int = 1
    is_paused: bool = False
    pause_reason: SimulationPauseReason | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_step: int = 1
    total_steps: int = 8
    progress: float = 0.0
    auto_approve: bool = True
    current_stage_label: str = "Monitoring"
    presentation_mode: bool = False
    run_id: str | None = None
    pending_approval: ApprovalState | None = None
    approved_actions: list[str] = Field(default_factory=list)
    rejected_actions: list[str] = Field(default_factory=list)
    governance_decision: GovernanceDecision = GovernanceDecision.PENDING
    outcome_quality: OutcomeQuality | None = None
    last_error: str | None = None
    latest_run_summary: dict[str, Any] | None = None


class SimulationStartRequest(APIModel):
    scenario_id: str = "electrical-room-fire"
    speed_multiplier: int = 1
    auto_approve: bool = True
    presentation_mode: bool = False

    @field_validator("speed_multiplier")
    @classmethod
    def validate_speed_multiplier(cls, value: int) -> int:
        if value not in {1, 2, 5, 10}:
            raise ValueError("speed_multiplier must be one of 1, 2, 5, or 10")
        return value


class SimulationSpeedRequest(APIModel):
    speed_multiplier: int

    @field_validator("speed_multiplier")
    @classmethod
    def validate_speed_multiplier(cls, value: int) -> int:
        if value not in {1, 2, 5, 10}:
            raise ValueError("speed_multiplier must be one of 1, 2, 5, or 10")
        return value


class SensorProfile(APIModel):
    temperature: float
    smoke_level: float
    co_level: float
    co2_level: float
    humidity: float
    electrical_load: float
    hvac_effect: float
    sensor_health: str


class SimulationRunSummary(APIModel):
    run_id: str
    scenario: str
    started_at: datetime
    completed_at: datetime | None = None
    duration: int = 0
    max_risk: str = "NORMAL"
    occupants_at_risk: int = 0
    evacuated: int = 0
    response_dispatch_time: int | None = None
    containment_time: int | None = None
    status: SimulationStatus = SimulationStatus.STOPPED
    time_to_warning: int | None = None
    time_to_critical: int | None = None
    time_to_evacuation: int | None = None
    time_to_first_dispatch: int | None = None
    time_to_first_response: int | None = None
    time_to_containment: int | None = None
    time_to_resolution: int | None = None
    evacuation_completion_time: int | None = None
    peak_congestion: str | None = None
    resources_dispatched: int = 0
    unsafe_zone_duration: int = 0
    risk_exposure_score: float = 0.0
    governance_decision: GovernanceDecision = GovernanceDecision.PENDING
    outcome_quality: OutcomeQuality | None = None
    decision_impact_summary: str | None = None
    model_version: str | None = None
    prediction_source: PredictionSource = PredictionSource.NOT_AVAILABLE
    max_critical_probability: float = 0.0
    first_warning_prediction_time: int | None = None
    first_critical_prediction_time: int | None = None
    static_plan_metrics: dict[str, Any] | None = None
    shortest_path_metrics: dict[str, Any] | None = None
    twin_optimized_metrics: dict[str, Any] | None = None