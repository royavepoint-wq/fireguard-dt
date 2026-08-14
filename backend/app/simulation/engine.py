from __future__ import annotations

from collections import deque
from datetime import datetime
import logging
from threading import Event, RLock, Thread
from time import sleep
from uuid import uuid4

from app.models.building import BuildingInfrastructureTwinState, BuildingInfrastructureTwinUpdate
from app.models.common import EventSeverity, ResourceStatus, RiskLevel, SensorHealth, TwinStatus, utc_now
from app.models.evacuation import EvacuationRouteResponse
from app.models.events import DigitalTwinEvent, EventType
from app.models.fire_environment import FireEnvironmentTwinState
from app.models.ml import FireRiskPredictionRequest, PredictionSource
from app.models.occupancy import CongestionLevel, EvacuationRoute, EvacuationStatus, OccupancyEvacuationTwinState, OccupancyZone, RouteStatus, RouteStrategy
from app.models.response import DispatchTask, EmergencyResponseTwinState, Incident, InspectionDrone, ResponseCrew
from app.services.building_twin_service import BuildingTwinService
from app.services.evacuation.route_optimizer import EvacuationRouteOptimizer
from app.services.event_bus import InMemoryEventBus
from app.services.fire_twin_service import FireTwinService
from app.services.ml.fire_predictor import FireRiskPredictor
from app.services.occupancy_twin_service import OccupancyTwinService
from app.services.response_twin_service import ResponseTwinService
from app.simulation.models import (
    ApprovalState,
    ApprovalStatus,
    GovernanceDecision,
    OutcomeQuality,
    ScenarioDefinition,
    SimulationPhase,
    SimulationPauseReason,
    SimulationRunSummary,
    SimulationStartRequest,
    SimulationState,
    SimulationStatus,
)
from app.simulation.scenarios import get_scenario, list_scenarios
from app.simulation.sensor_profiles import build_sensor_profile
from app.simulation.state_machine import compute_rule_based_simulation_risk, phase_for_elapsed, risk_level_from_score
from app.simulation.timeline import get_stage_label, get_step_index


class SimulationConflictError(RuntimeError):
    pass


class SimulationEngine:
    HVAC_ISOLATION_ACTION = "HVAC Zone 3 Isolation"
    HVAC_ISOLATION_TYPE = "HVAC_ISOLATION"
    HVAC_ISOLATION_REASON = "Smoke-control containment action requested by the AI / Decision Orchestrator."
    APPROVED_BRANCH_RESOLUTION_TARGET = 105
    REJECTED_BRANCH_RESOLUTION_TARGET = 120

    _logger = logging.getLogger("fireguard.simulation")

    def __init__(
        self,
        *,
        event_bus: InMemoryEventBus,
        fire_twin_service: FireTwinService,
        building_twin_service: BuildingTwinService,
        occupancy_twin_service: OccupancyTwinService,
        response_twin_service: ResponseTwinService,
        fire_risk_predictor: FireRiskPredictor,
        evacuation_route_optimizer: EvacuationRouteOptimizer,
    ) -> None:
        self._event_bus = event_bus
        self._fire_twin_service = fire_twin_service
        self._building_twin_service = building_twin_service
        self._occupancy_twin_service = occupancy_twin_service
        self._response_twin_service = response_twin_service
        self._fire_risk_predictor = fire_risk_predictor
        self._evacuation_route_optimizer = evacuation_route_optimizer
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._state = SimulationState()
        self._runs: deque[SimulationRunSummary] = deque(maxlen=20)
        self._metrics: dict[str, int | float | str | None] = {}
        self._current_scenario: ScenarioDefinition | None = None
        self._last_phase_event: SimulationPhase | None = None
        self._last_risk_level: RiskLevel | None = None
        self._last_route_signature: tuple[str, str | None, tuple[str, ...]] | None = None
        self._anomaly_announced = False

    def get_status(self) -> SimulationState:
        with self._lock:
            return self._state.model_copy(deep=True)

    def get_scenarios(self) -> list[ScenarioDefinition]:
        return list_scenarios()

    def get_runs(self) -> list[SimulationRunSummary]:
        with self._lock:
            return list(self._runs)

    def start(self, request: SimulationStartRequest, *, run_in_background: bool = True) -> SimulationState:
        with self._lock:
            if self._state.status in {SimulationStatus.RUNNING, SimulationStatus.PAUSED, SimulationStatus.WAITING_FOR_APPROVAL}:
                raise SimulationConflictError("A simulation is already active.")
            scenario = get_scenario(request.scenario_id)
            self._prepare_start_state(scenario, request)
            self._publish_event(
                event_type=EventType.SIMULATION_STARTED,
                source_twin="system",
                severity=EventSeverity.INFO,
                message=f"Simulation started for {scenario.name}.",
            )
            if run_in_background:
                self._start_thread_locked()
            return self.get_status()

    def pause(self) -> SimulationState:
        with self._lock:
            if self._state.status != SimulationStatus.RUNNING:
                return self.get_status()
            self._state.status = SimulationStatus.PAUSED
            self._state.is_paused = True
            self._state.pause_reason = SimulationPauseReason.MANUAL
            self._publish_event(
                event_type=EventType.SIMULATION_PAUSED,
                source_twin="system",
                severity=EventSeverity.INFO,
                message="Simulation paused.",
            )
            return self.get_status()

    def resume(self) -> SimulationState:
        with self._lock:
            if self._state.status not in {SimulationStatus.PAUSED, SimulationStatus.WAITING_FOR_APPROVAL}:
                return self.get_status()
            if self._state.pending_approval and self._state.pending_approval.status == ApprovalStatus.PENDING:
                return self.get_status()
            self._state.status = SimulationStatus.RUNNING
            self._state.is_paused = False
            self._state.pause_reason = None
            self._publish_event(
                event_type=EventType.SIMULATION_RESUMED,
                source_twin="system",
                severity=EventSeverity.INFO,
                message="Simulation resumed.",
            )
            if self._thread is None or not self._thread.is_alive():
                self._start_thread_locked()
            return self.get_status()

    def stop(self) -> SimulationState:
        with self._lock:
            self._stop_event.set()
            if self._state.status not in {SimulationStatus.STOPPED, SimulationStatus.COMPLETED}:
                self._state.status = SimulationStatus.STOPPED
                self._state.is_paused = False
                self._state.pause_reason = None
                self._publish_event(
                    event_type=EventType.SIMULATION_STOPPED,
                    source_twin="system",
                    severity=EventSeverity.INFO,
                    message="Simulation stopped.",
                )
            return self.get_status()

    def reset(self) -> SimulationState:
        with self._lock:
            self._stop_event.set()
            self._thread = None
            self._current_scenario = None
            self._metrics = {}
            self._last_phase_event = None
            self._last_risk_level = None
            self._anomaly_announced = False
            self._event_bus.clear_events()
            self._fire_twin_service.reset_state()
            self._building_twin_service.reset_state()
            self._occupancy_twin_service.reset_state()
            self._response_twin_service.reset_state()
            self._state = SimulationState()
            self._publish_event(
                event_type=EventType.SYSTEM_INITIALIZED,
                source_twin="system",
                severity=EventSeverity.INFO,
                message="Simulation reset and all twins restored to baseline.",
            )
            return self.get_status()

    def set_speed(self, speed_multiplier: int) -> SimulationState:
        with self._lock:
            self._state.speed_multiplier = speed_multiplier
            return self.get_status()

    def approve_pending_action(self) -> SimulationState:
        with self._lock:
            approval = self._state.pending_approval
            if approval is None:
                return self.get_status()
            self._resolve_approval_by_id_locked(
                approval_id=approval.approval_id,
                approval_status=ApprovalStatus.APPROVED,
                decision_source="HUMAN",
            )
            return self.get_status()

    def reject_pending_action(self) -> SimulationState:
        with self._lock:
            approval = self._state.pending_approval
            if approval is None:
                return self.get_status()
            self._resolve_approval_by_id_locked(
                approval_id=approval.approval_id,
                approval_status=ApprovalStatus.REJECTED,
                decision_source="HUMAN",
            )
            return self.get_status()

    def approve_action_by_id(self, approval_id: str) -> SimulationState:
        with self._lock:
            self._resolve_approval_by_id_locked(
                approval_id=approval_id,
                approval_status=ApprovalStatus.APPROVED,
                decision_source="HUMAN",
            )
            return self.get_status()

    def reject_action_by_id(self, approval_id: str) -> SimulationState:
        with self._lock:
            self._resolve_approval_by_id_locked(
                approval_id=approval_id,
                approval_status=ApprovalStatus.REJECTED,
                decision_source="HUMAN",
            )
            return self.get_status()

    def advance_seconds(self, seconds: int = 1) -> SimulationState:
        with self._lock:
            for _index in range(seconds):
                if self._state.status != SimulationStatus.RUNNING or self._current_scenario is None:
                    break
                self._tick_locked()
            return self.get_status()

    def _prepare_start_state(self, scenario: ScenarioDefinition, request: SimulationStartRequest) -> None:
        self.reset()
        self._stop_event.clear()
        self._current_scenario = scenario
        now = utc_now()
        self._state = SimulationState(
            simulation_id=f"sim-{uuid4()}",
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            status=SimulationStatus.RUNNING,
            phase=SimulationPhase.NORMAL,
            elapsed_seconds=0,
            speed_multiplier=request.speed_multiplier,
            is_paused=False,
            started_at=now,
            completed_at=None,
            current_step=1,
            total_steps=8,
            progress=0.0,
            auto_approve=request.auto_approve,
            current_stage_label="Monitoring",
            presentation_mode=request.presentation_mode,
            run_id=f"run-{uuid4()}",
            governance_decision=GovernanceDecision.PENDING,
            outcome_quality=None,
        )
        self._metrics = {
            "max_risk": RiskLevel.NORMAL.value,
            "time_to_warning": None,
            "time_to_critical": None,
            "time_to_evacuation": None,
            "time_to_first_dispatch": None,
            "time_to_first_response": None,
            "time_to_containment": None,
            "time_to_resolution": None,
            "response_dispatch_time": None,
            "containment_time": None,
            "evacuation_completion_time": None,
            "peak_congestion": CongestionLevel.LOW.value,
            "resources_dispatched": 0,
            "unsafe_zone_duration": 0,
            "risk_exposure_score": 0.0,
            "model_version": None,
            "prediction_source": PredictionSource.NOT_AVAILABLE.value,
            "max_critical_probability": 0.0,
            "first_warning_prediction_time": None,
            "first_critical_prediction_time": None,
            "incident_trigger_time": None,
            "static_plan_metrics": None,
            "shortest_path_metrics": None,
            "twin_optimized_metrics": None,
        }
        self._last_phase_event = SimulationPhase.NORMAL
        self._last_risk_level = RiskLevel.NORMAL
        self._last_route_signature = None
        self._anomaly_announced = False
        self._apply_twin_state_locked(0)

    def _start_thread_locked(self) -> None:
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                if self._state.status == SimulationStatus.RUNNING and self._current_scenario is not None:
                    self._tick_locked()
                    interval = 1.0 / self._state.speed_multiplier
                elif self._state.status in {SimulationStatus.COMPLETED, SimulationStatus.STOPPED, SimulationStatus.ERROR}:
                    break
                else:
                    interval = 0.1
            sleep(interval)

    def _tick_locked(self) -> None:
        if self._current_scenario is None:
            return
        self._state.elapsed_seconds += 1
        self._apply_twin_state_locked(self._state.elapsed_seconds)
        if self._can_complete_scenario(self._state.elapsed_seconds):
            self._state.status = SimulationStatus.COMPLETED
            self._state.completed_at = utc_now()
            self._state.is_paused = False
            incident_trigger_time = self._metrics.get("incident_trigger_time")
            if isinstance(incident_trigger_time, int):
                self._metrics["time_to_resolution"] = max(0, self._state.elapsed_seconds - incident_trigger_time)
            else:
                self._metrics["time_to_resolution"] = self._state.elapsed_seconds
            self._state.outcome_quality = self._derive_outcome_quality()
            self._store_run_summary_locked(SimulationStatus.COMPLETED)
            self._publish_event(
                event_type=EventType.SIMULATION_COMPLETED,
                source_twin="system",
                severity=EventSeverity.INFO,
                message=f"Scenario resolved: {self._current_scenario.name} ({self._state.outcome_quality.value if self._state.outcome_quality else 'N/A'} outcome).",
                payload={
                    "governance_decision": self._state.governance_decision.value,
                    "outcome_quality": self._state.outcome_quality.value if self._state.outcome_quality else None,
                },
            )
            self._stop_event.set()

    def _apply_twin_state_locked(self, elapsed_seconds: int) -> None:
        scenario = self._current_scenario
        if scenario is None:
            return

        decision = self._state.governance_decision
        effective_elapsed = elapsed_seconds
        if decision == GovernanceDecision.HVAC_ISOLATION_APPROVED:
            effective_elapsed = min(scenario.duration_seconds, elapsed_seconds + 8)
        elif decision == GovernanceDecision.HVAC_ISOLATION_REJECTED:
            effective_elapsed = max(0, elapsed_seconds - 20)

        phase = phase_for_elapsed(effective_elapsed, scenario)
        if self._approval_decision_missing() and phase in {SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED}:
            phase = SimulationPhase.RESPONSE
        self._state.phase = phase
        self._state.current_step = get_step_index(phase)
        self._state.current_stage_label = get_stage_label(phase)
        self._state.progress = round(min(1.0, elapsed_seconds / scenario.duration_seconds), 2)

        sensor_profile = build_sensor_profile(elapsed_seconds, scenario)
        sensor_profile = self._apply_governance_branch_to_sensor_profile(sensor_profile, elapsed_seconds)
        rule_based_risk_score = compute_rule_based_simulation_risk(sensor_profile, elapsed_seconds, scenario)

        ml_request = self._build_prediction_request(elapsed_seconds, scenario, phase, sensor_profile)
        prediction = self._fire_risk_predictor.predict(ml_request)
        risk_level = prediction.predicted_class
        risk_score = float(prediction.probabilities.get(RiskLevel.CRITICAL, 0.0))
        prediction_source = prediction.prediction_source
        prediction_model_version = prediction.model_version
        prediction_confidence = prediction.confidence
        prediction_probabilities = prediction.probabilities

        if prediction_source != PredictionSource.ML_MODEL:
            risk_level = risk_level_from_score(rule_based_risk_score)
            risk_score = rule_based_risk_score
            warning_probability = min(1.0 - risk_score, max(0.05, (0.55 - abs(risk_score - 0.5)) * 0.6))
            normal_probability = max(0.0, 1.0 - risk_score - warning_probability)
            total_probability = max(1e-6, normal_probability + warning_probability + risk_score)
            prediction_probabilities = {
                RiskLevel.NORMAL: normal_probability / total_probability,
                RiskLevel.WARNING: warning_probability / total_probability,
                RiskLevel.CRITICAL: risk_score / total_probability,
            }
            prediction_confidence = max(prediction_probabilities.values())

        if scenario.sensor_anomaly_mode and risk_level == RiskLevel.CRITICAL:
            risk_level = RiskLevel.WARNING
            risk_score = 0.38

        self._metrics["model_version"] = prediction_model_version
        self._metrics["prediction_source"] = prediction_source.value
        self._metrics["max_critical_probability"] = max(float(self._metrics.get("max_critical_probability") or 0.0), float(risk_score))

        if self._last_phase_event != phase:
            self._publish_event(
                event_type=EventType.SIMULATION_PHASE_CHANGED,
                source_twin="system",
                severity=EventSeverity.INFO,
                message=f"Simulation phase changed to {phase.value}.",
            )
            self._last_phase_event = phase

        if not self._anomaly_announced and phase == SimulationPhase.ANOMALY:
            self._publish_event(
                event_type=EventType.ANOMALY_DETECTED,
                source_twin="fire_environment",
                severity=EventSeverity.WARNING,
                message="Abnormal electrical-room sensor behavior detected.",
            )
            self._anomaly_announced = True

        if self._last_risk_level != risk_level:
            risk_label = "ML Fire Risk" if prediction_source == PredictionSource.ML_MODEL else "Rule-Based Fallback Risk"
            self._publish_event(
                event_type=EventType.RISK_LEVEL_CHANGED,
                source_twin="fire_environment",
                severity=EventSeverity.CRITICAL if risk_level == RiskLevel.CRITICAL else EventSeverity.WARNING,
                message=f"{risk_label} moved to {risk_level.value}.",
                payload={
                    "fire_risk_probability": round(risk_score, 4),
                    "prediction_source": prediction_source.value,
                    "model_version": prediction_model_version,
                    "risk_probabilities": {label.value: round(value, 4) for label, value in prediction_probabilities.items()},
                },
            )
            self._last_risk_level = risk_level

        self._metrics["risk_exposure_score"] = float(self._metrics.get("risk_exposure_score") or 0.0) + float(risk_score)

        if elapsed_seconds in {12, 24, 38}:
            self._publish_event(
                event_type=EventType.SENSOR_UPDATE,
                source_twin="fire_environment",
                severity=EventSeverity.WARNING if risk_level != RiskLevel.NORMAL else EventSeverity.INFO,
                message="Electrical-room sensor profile updated.",
                payload={
                    "fire_risk_probability": round(risk_score, 4),
                    "prediction_source": prediction_source.value,
                },
            )

        self._handle_approval_gate_locked(elapsed_seconds, risk_level)

        fire_state = self._build_fire_state(
            elapsed_seconds,
            scenario,
            sensor_profile,
            risk_score,
            risk_level,
            prediction_source,
            prediction_model_version,
            prediction_confidence,
            prediction_probabilities,
        )
        building_state = self._build_building_state(elapsed_seconds, scenario, phase)
        occupancy_state = self._build_occupancy_state(elapsed_seconds, scenario, phase, fire_state, building_state)
        response_state = self._build_response_state(elapsed_seconds, scenario, phase)

        self._handle_route_events_locked(occupancy_state, elapsed_seconds)

        self._fire_twin_service.replace_state(fire_state, publish_event=False)
        self._building_twin_service.replace_state(building_state, publish_event=False)
        self._occupancy_twin_service.replace_state(occupancy_state, publish_event=False)
        self._response_twin_service.replace_state(response_state, publish_event=False)

        peak_congestion = self._metrics.get("peak_congestion") or CongestionLevel.LOW.value
        if peak_congestion == CongestionLevel.LOW.value and occupancy_state.congestion_level in {CongestionLevel.MODERATE, CongestionLevel.HIGH}:
            self._metrics["peak_congestion"] = occupancy_state.congestion_level.value
        elif peak_congestion == CongestionLevel.MODERATE.value and occupancy_state.congestion_level == CongestionLevel.HIGH:
            self._metrics["peak_congestion"] = occupancy_state.congestion_level.value

        if self._metrics.get("evacuation_completion_time") is None and occupancy_state.evacuating_count == 0 and occupancy_state.evacuated_count >= scenario.affected_zone_occupancy and elapsed_seconds >= 50:
            self._metrics["evacuation_completion_time"] = elapsed_seconds

        dispatched_resources = set()
        for task in response_state.dispatch_queue:
            dispatched_resources.add(task.resource_id)
        self._metrics["resources_dispatched"] = max(int(self._metrics.get("resources_dispatched") or 0), len(dispatched_resources))

        if phase == SimulationPhase.EVACUATION and self._metrics["time_to_evacuation"] is None:
            self._metrics["time_to_evacuation"] = elapsed_seconds
            self._publish_event(
                event_type=EventType.OCCUPANCY_UPDATED,
                source_twin="occupancy_evacuation",
                severity=EventSeverity.WARNING,
                message="Evacuation initiated for 43 occupants in affected zones.",
            )

        if phase == SimulationPhase.RESPONSE and self._metrics["response_dispatch_time"] is None:
            self._metrics["response_dispatch_time"] = elapsed_seconds

        if phase == SimulationPhase.CONTAINMENT and self._metrics["time_to_containment"] is None:
            incident_trigger_time = self._metrics.get("incident_trigger_time")
            if isinstance(incident_trigger_time, int):
                self._metrics["time_to_containment"] = max(0, elapsed_seconds - incident_trigger_time)
            else:
                self._metrics["time_to_containment"] = elapsed_seconds
            self._metrics["containment_time"] = elapsed_seconds
            containment_msg = "Fire containment measures active; sprinkler and HVAC isolation engaged."
            if decision == GovernanceDecision.HVAC_ISOLATION_REJECTED:
                containment_msg = "Containment reached on degraded path after extended smoke exposure."
            self._publish_event(
                event_type=EventType.INFRASTRUCTURE_STATUS_CHANGED,
                source_twin="building_infrastructure",
                severity=EventSeverity.WARNING,
                message=containment_msg,
            )

        if phase == SimulationPhase.RESOLVED and elapsed_seconds == min(scenario.duration_seconds, 110):
            self._publish_event(
                event_type=EventType.OCCUPANCY_UPDATED,
                source_twin="occupancy_evacuation",
                severity=EventSeverity.INFO,
                message="Evacuation completed for affected occupants.",
            )

        if elapsed_seconds == 42:
            self._publish_event(
                event_type=EventType.INFRASTRUCTURE_STATUS_CHANGED,
                source_twin="building_infrastructure",
                severity=EventSeverity.WARNING,
                message="Smoke risk detected in Corridor C.",
            )
        if elapsed_seconds == 60:
            self._publish_event(
                event_type=EventType.DISPATCH_CREATED,
                source_twin="emergency_response",
                severity=EventSeverity.WARNING,
                message="Drone 1 dispatched.",
            )
        if elapsed_seconds == 63:
            self._publish_event(
                event_type=EventType.DISPATCH_CREATED,
                source_twin="emergency_response",
                severity=EventSeverity.WARNING,
                message="Crew 1 dispatched.",
            )

        building_state_current = self._building_twin_service.get_state()
        corridor_c_state = next((corridor for corridor in building_state_current.corridors if corridor.corridor_id == "corridor-c"), None)
        if corridor_c_state and (corridor_c_state.status != "SAFE" or not corridor_c_state.is_accessible):
            self._metrics["unsafe_zone_duration"] = int(self._metrics.get("unsafe_zone_duration") or 0) + 1

        if self._metrics["time_to_warning"] is None and risk_level == RiskLevel.WARNING:
            self._metrics["time_to_warning"] = elapsed_seconds
            self._metrics["first_warning_prediction_time"] = elapsed_seconds
        if self._metrics["time_to_critical"] is None and risk_level == RiskLevel.CRITICAL:
            self._metrics["time_to_critical"] = elapsed_seconds
            self._metrics["first_critical_prediction_time"] = elapsed_seconds
        if self._metrics.get("incident_trigger_time") is None and phase == SimulationPhase.CRITICAL:
            self._metrics["incident_trigger_time"] = elapsed_seconds

        incident_trigger_time = self._metrics.get("incident_trigger_time")
        if isinstance(incident_trigger_time, int):
            if self._metrics.get("time_to_first_dispatch") is None:
                has_dispatch = any(task.status in {ResourceStatus.ASSIGNED, ResourceStatus.EN_ROUTE, ResourceStatus.ON_SCENE} for task in response_state.dispatch_queue)
                if has_dispatch:
                    self._metrics["time_to_first_dispatch"] = max(0, elapsed_seconds - incident_trigger_time)

            if self._metrics.get("time_to_first_response") is None:
                first_response_reached = any(crew.status == ResourceStatus.ON_SCENE for crew in response_state.crews) or any(
                    drone.status == ResourceStatus.ON_SCENE for drone in response_state.drones
                )
                if first_response_reached:
                    self._metrics["time_to_first_response"] = max(0, elapsed_seconds - incident_trigger_time)
        if RiskLevel[self._metrics["max_risk"]] if isinstance(self._metrics["max_risk"], str) else RiskLevel.NORMAL:
            pass
        current_max = self._metrics["max_risk"]
        if current_max == RiskLevel.NORMAL.value and risk_level != RiskLevel.NORMAL:
            self._metrics["max_risk"] = risk_level.value
        if current_max == RiskLevel.WARNING.value and risk_level == RiskLevel.CRITICAL:
            self._metrics["max_risk"] = risk_level.value

    def _build_fire_state(
        self,
        elapsed_seconds: int,
        scenario: ScenarioDefinition,
        sensor_profile,
        risk_score: float,
        risk_level: RiskLevel,
        prediction_source: PredictionSource,
        model_version: str,
        prediction_confidence: float,
        prediction_probabilities: dict[RiskLevel, float],
    ) -> FireEnvironmentTwinState:
        previous_state = self._fire_twin_service.get_state()
        temperature_rate = max(sensor_profile.temperature - previous_state.temperature, 0.0)
        sensor_health = sensor_profile.sensor_health if isinstance(sensor_profile.sensor_health, SensorHealth) else SensorHealth(sensor_profile.sensor_health)
        return FireEnvironmentTwinState(
            twin_id=previous_state.twin_id,
            name=previous_state.name,
            status=TwinStatus.DEGRADED if scenario.sensor_anomaly_mode and 10 <= elapsed_seconds <= 35 else TwinStatus.ONLINE,
            last_updated=utc_now(),
            building_id=scenario.building_id,
            floor_id=scenario.floor_id,
            zone_id=scenario.origin_zone_id,
            temperature=round(sensor_profile.temperature, 2),
            temperature_rate=round(temperature_rate, 2),
            smoke_level=round(sensor_profile.smoke_level, 3),
            co_level=round(sensor_profile.co_level, 2),
            co2_level=round(sensor_profile.co2_level, 2),
            humidity=round(sensor_profile.humidity, 2),
            electrical_load=round(sensor_profile.electrical_load, 2),
            fire_risk_probability=risk_score,
            risk_level=risk_level,
            risk_probabilities=prediction_probabilities,
            prediction_source=prediction_source,
            model_version=model_version,
            prediction_confidence=round(prediction_confidence, 4),
            sensor_health=sensor_health,
            hvac_effect=round(sensor_profile.hvac_effect, 2),
        )

    def _build_prediction_request(
        self,
        elapsed_seconds: int,
        scenario: ScenarioDefinition,
        phase: SimulationPhase,
        sensor_profile,
    ) -> FireRiskPredictionRequest:
        decision = self._state.governance_decision
        if elapsed_seconds < 50:
            occupancy = scenario.affected_zone_occupancy
        elif elapsed_seconds < 105:
            progress = min(1.0, (elapsed_seconds - 50) / 55)
            occupancy = max(0.0, scenario.affected_zone_occupancy * (1.0 - progress))
        else:
            occupancy = 0.0

        hvac_running = 1
        if decision == GovernanceDecision.HVAC_ISOLATION_APPROVED and phase in {SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED}:
            hvac_running = 0

        sprinkler_active = int(not scenario.sprinkler_failure and phase in {SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED})

        return FireRiskPredictionRequest(
            temperature=float(sensor_profile.temperature),
            temperature_rate=max(0.0, float(sensor_profile.temperature) - float(self._fire_twin_service.get_state().temperature)),
            smoke_level=float(sensor_profile.smoke_level),
            co_level=float(sensor_profile.co_level),
            co2_level=float(sensor_profile.co2_level),
            humidity=float(sensor_profile.humidity),
            electrical_load=float(sensor_profile.electrical_load),
            occupancy=float(occupancy),
            hvac_running=hvac_running,
            sprinkler_active=sprinkler_active,
        )

    def _build_building_state(
        self,
        elapsed_seconds: int,
        scenario: ScenarioDefinition,
        phase: SimulationPhase,
    ) -> BuildingInfrastructureTwinState:
        base_state = self._building_twin_service.get_state()
        decision = self._state.governance_decision
        exits = []
        for exit_item in base_state.exits:
            if exit_item.exit_id == "exit-b":
                blocked = scenario.initial_exit_b_blocked or False
            else:
                blocked = False
            exits.append(exit_item.model_copy(update={"is_blocked": blocked, "is_available": not blocked}))

        corridors = []
        for corridor in base_state.corridors:
            if corridor.corridor_id == scenario.affected_corridor_id and phase in {
                SimulationPhase.CRITICAL,
                SimulationPhase.EVACUATION,
                SimulationPhase.RESPONSE,
                SimulationPhase.CONTAINMENT,
            }:
                status = "UNSAFE" if phase != SimulationPhase.CRITICAL else "WARNING"
                is_accessible = phase == SimulationPhase.CRITICAL
                if decision == GovernanceDecision.HVAC_ISOLATION_APPROVED and phase == SimulationPhase.CONTAINMENT:
                    status = "SAFE"
                    is_accessible = True
                if decision == GovernanceDecision.HVAC_ISOLATION_REJECTED and elapsed_seconds < 112:
                    status = "UNSAFE"
                    is_accessible = False
                corridors.append(corridor.model_copy(update={"is_accessible": is_accessible, "status": status}))
            else:
                corridors.append(corridor.model_copy(update={"is_accessible": True, "status": "SAFE"}))

        hvac_zones = []
        for hvac_zone in base_state.hvac_zones:
            if hvac_zone.hvac_zone_id == "hvac-zone-3":
                if phase in {SimulationPhase.WARNING, SimulationPhase.CRITICAL}:
                    status = "MONITORING"
                elif phase in {SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED} and self.HVAC_ISOLATION_ACTION in self._state.rejected_actions:
                    status = "APPROVAL_BLOCKED"
                elif phase in {SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED, SimulationPhase.RESPONSE} and self._approval_effective():
                    status = "ISOLATED"
                elif decision == GovernanceDecision.HVAC_ISOLATION_REJECTED and phase in {SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED}:
                    status = "RUNNING"
                else:
                    status = "NORMAL"
                hvac_zones.append(hvac_zone.model_copy(update={"status": status}))
            else:
                hvac_zones.append(hvac_zone)

        sprinklers = []
        for sprinkler in base_state.sprinklers:
            if sprinkler.zone_id == "zone-1a":
                if scenario.sprinkler_failure:
                    sprinklers.append(sprinkler.model_copy(update={"status": "FAILED", "is_active": False}))
                elif phase in {SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED}:
                    sprinklers.append(sprinkler.model_copy(update={"status": "ACTIVE", "is_active": True}))
                else:
                    sprinklers.append(sprinkler.model_copy(update={"status": "READY", "is_active": False}))
            else:
                sprinklers.append(sprinkler)

        electrical_zones = []
        current_load = self._fire_twin_service.get_state().electrical_load
        for electrical_zone in base_state.electrical_zones:
            if electrical_zone.electrical_zone_id == "electrical-zone-1":
                status = "CRITICAL" if phase in {SimulationPhase.CRITICAL, SimulationPhase.EVACUATION} else "WARNING" if phase == SimulationPhase.WARNING else "NORMAL"
                electrical_zones.append(electrical_zone.model_copy(update={"load_percentage": current_load, "status": status}))
            else:
                electrical_zones.append(electrical_zone)

        twin_status = TwinStatus.DEGRADED if scenario.sensor_anomaly_mode and phase == SimulationPhase.ANOMALY else TwinStatus.ONLINE
        return base_state.model_copy(
            update={
                "status": twin_status,
                "last_updated": utc_now(),
                "corridors": corridors,
                "exits": exits,
                "hvac_zones": hvac_zones,
                "sprinklers": sprinklers,
                "electrical_zones": electrical_zones,
            },
            deep=True,
        )

    def _build_occupancy_state(
        self,
        elapsed_seconds: int,
        scenario: ScenarioDefinition,
        phase: SimulationPhase,
        fire_state: FireEnvironmentTwinState,
        building_state: BuildingInfrastructureTwinState,
    ) -> OccupancyEvacuationTwinState:
        base_state = self._occupancy_twin_service.get_state()
        total_occupancy = scenario.initial_occupancy
        affected_total = scenario.affected_zone_occupancy
        if elapsed_seconds < 50:
            evacuating = 0
            evacuated = 0
        elif elapsed_seconds < 105:
            evacuation_progress = min(1.0, (elapsed_seconds - 50) / 55)
            evacuated = int(round(affected_total * evacuation_progress))
            evacuating = max(0, affected_total - evacuated)
        else:
            evacuating = 0
            evacuated = affected_total

        zone_1a_remaining = max(0, affected_total - evacuated)
        zone_1b_safe_count = total_occupancy - zone_1a_remaining - 58 - 39 - 65
        zones: list[OccupancyZone] = []
        for zone in base_state.zones:
            if zone.zone_id == "zone-1a":
                if phase in {SimulationPhase.EVACUATION, SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT}:
                    evacuation_status = EvacuationStatus.EVACUATING if zone_1a_remaining > 0 else EvacuationStatus.EVACUATED
                elif phase == SimulationPhase.RESOLVED:
                    evacuation_status = EvacuationStatus.EVACUATED
                else:
                    evacuation_status = EvacuationStatus.STABLE
                zones.append(
                    zone.model_copy(
                        update={
                            "occupancy_count": zone_1a_remaining if phase != SimulationPhase.RESOLVED else 0,
                            "density": round((zone_1a_remaining / affected_total) * 0.41, 2) if zone_1a_remaining else 0.0,
                            "evacuation_status": evacuation_status,
                        }
                    )
                )
            elif zone.zone_id == "zone-1b":
                zones.append(
                    zone.model_copy(
                        update={
                            "occupancy_count": zone_1b_safe_count,
                            "density": round(min(0.78, 0.37 + evacuated / max(total_occupancy, 1)), 2),
                        }
                    )
                )
            else:
                zones.append(zone)

        congestion = CongestionLevel.MODERATE if phase in {SimulationPhase.WARNING, SimulationPhase.EVACUATION, SimulationPhase.RESPONSE} else CongestionLevel.LOW
        if scenario.peak_occupancy and phase in {SimulationPhase.WARNING, SimulationPhase.EVACUATION, SimulationPhase.RESPONSE}:
            congestion = CongestionLevel.HIGH

        occupancy_state = base_state.model_copy(
            update={
                "last_updated": utc_now(),
                "total_occupancy": total_occupancy,
                "zones": zones,
                "evacuating_count": evacuating,
                "evacuated_count": evacuated,
                "congestion_level": congestion,
            },
            deep=True,
        )

        if phase in {SimulationPhase.EVACUATION, SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED}:
            compare = self._evacuation_route_optimizer.compare(
                start_zone_id=scenario.origin_zone_id,
                fire_state=fire_state,
                building_state=building_state,
                occupancy_state=occupancy_state,
            )
            by_strategy = {result.strategy: result for result in compare.results}
            active_routes = [
                self._route_response_to_twin_route("route-static-plan", scenario.origin_zone_id, by_strategy.get(RouteStrategy.STATIC_PLAN), 80),
                self._route_response_to_twin_route("route-shortest-path", scenario.origin_zone_id, by_strategy.get(RouteStrategy.SHORTEST_PATH), 75),
                self._route_response_to_twin_route("route-twin-optimized", scenario.origin_zone_id, by_strategy.get(RouteStrategy.TWIN_OPTIMIZED), 70),
            ]

            self._metrics["static_plan_metrics"] = self._route_metrics_payload(by_strategy.get(RouteStrategy.STATIC_PLAN))
            self._metrics["shortest_path_metrics"] = self._route_metrics_payload(by_strategy.get(RouteStrategy.SHORTEST_PATH))
            self._metrics["twin_optimized_metrics"] = self._route_metrics_payload(by_strategy.get(RouteStrategy.TWIN_OPTIMIZED))
        else:
            active_routes = [
                EvacuationRoute(route_id="route-static-plan", from_zone_id="zone-1a", to_exit_id="exit-a", status=RouteStatus.OPEN, estimated_capacity=80, strategy=RouteStrategy.STATIC_PLAN),
                EvacuationRoute(route_id="route-shortest-path", from_zone_id="zone-1a", to_exit_id="exit-a", status=RouteStatus.CONGESTED, estimated_capacity=75, strategy=RouteStrategy.SHORTEST_PATH),
                EvacuationRoute(route_id="route-twin-optimized", from_zone_id="zone-1a", to_exit_id="exit-b", status=RouteStatus.OPEN, estimated_capacity=70, strategy=RouteStrategy.TWIN_OPTIMIZED),
            ]

        return occupancy_state.model_copy(
            update={
                "active_routes": active_routes,
            },
            deep=True,
        )

    def _route_response_to_twin_route(
        self,
        route_id: str,
        start_zone_id: str,
        route: EvacuationRouteResponse | None,
        estimated_capacity: int,
    ) -> EvacuationRoute:
        if route is None:
            return EvacuationRoute(
                route_id=route_id,
                from_zone_id=start_zone_id,
                to_exit_id="exit-a",
                status=RouteStatus.NO_SAFE_ROUTE,
                estimated_capacity=estimated_capacity,
            )
        return EvacuationRoute(
            route_id=route_id,
            from_zone_id=start_zone_id,
            to_exit_id=route.selected_exit or "exit-a",
            status=route.status,
            estimated_capacity=estimated_capacity,
            strategy=route.strategy,
            path_nodes=route.path_nodes,
            path_coordinates=route.path_coordinates,
            distance_meters=route.distance_meters,
            estimated_time_seconds=route.estimated_time_seconds,
            total_cost=route.total_cost,
            fire_risk_cost=route.fire_risk_cost,
            smoke_risk_cost=route.smoke_risk_cost,
            congestion_cost=route.congestion_cost,
            hazard_exposure_score=route.hazard_exposure_score,
            peak_route_congestion=route.peak_route_congestion,
            unsafe_segments=route.unsafe_segments,
        )

    def _route_metrics_payload(self, route: EvacuationRouteResponse | None) -> dict[str, object] | None:
        if route is None:
            return None
        return {
            "strategy": route.strategy.value,
            "selected_exit": route.selected_exit,
            "status": route.status.value,
            "distance_meters": route.distance_meters,
            "estimated_time_seconds": route.estimated_time_seconds,
            "hazard_exposure_score": route.hazard_exposure_score,
            "peak_route_congestion": route.peak_route_congestion,
            "total_cost": route.total_cost,
        }

    def _handle_route_events_locked(self, occupancy_state: OccupancyEvacuationTwinState, elapsed_seconds: int) -> None:
        optimized = next((route for route in occupancy_state.active_routes if route.strategy == RouteStrategy.TWIN_OPTIMIZED), None)
        if optimized is None:
            return

        signature = (optimized.status.value, optimized.to_exit_id, tuple(optimized.path_nodes))
        if self._last_route_signature is None:
            self._last_route_signature = signature
            self._publish_event(
                event_type=EventType.ROUTE_UPDATED,
                source_twin="orchestrator",
                severity=EventSeverity.INFO,
                message=f"Initial optimized evacuation route selected toward {optimized.to_exit_id}.",
                payload={"path_nodes": optimized.path_nodes, "strategy": optimized.strategy.value},
            )
            return

        if signature == self._last_route_signature:
            return

        self._publish_event(
            event_type=EventType.ROUTE_RECALCULATION_REQUESTED,
            source_twin="orchestrator",
            severity=EventSeverity.WARNING,
            message="Current evacuation route safety degraded. Dynamic recalculation triggered.",
            payload={"elapsed_seconds": elapsed_seconds},
        )

        if optimized.status == RouteStatus.NO_SAFE_ROUTE:
            self._publish_event(
                event_type=EventType.NO_SAFE_ROUTE,
                source_twin="orchestrator",
                severity=EventSeverity.CRITICAL,
                message="No safe evacuation route is currently available. Operator intervention required.",
            )
            self._publish_event(
                event_type=EventType.ROUTE_BLOCKED,
                source_twin="orchestrator",
                severity=EventSeverity.CRITICAL,
                message="Active evacuation route is blocked by hazard constraints.",
            )
        else:
            self._publish_event(
                event_type=EventType.ROUTE_UPDATED,
                source_twin="orchestrator",
                severity=EventSeverity.WARNING,
                message=f"Twin optimizer selected a new safest path via {optimized.to_exit_id}.",
                payload={
                    "path_nodes": optimized.path_nodes,
                    "selected_exit": optimized.to_exit_id,
                    "strategy": optimized.strategy.value,
                },
            )

        self._last_route_signature = signature

    def _build_response_state(
        self,
        elapsed_seconds: int,
        scenario: ScenarioDefinition,
        phase: SimulationPhase,
    ) -> EmergencyResponseTwinState:
        base_state = self._response_twin_service.get_state()
        incidents = []
        if phase in {SimulationPhase.CRITICAL, SimulationPhase.EVACUATION, SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED} and not scenario.sensor_anomaly_mode:
            incidents = [
                Incident(
                    incident_id="INC-DEMO-001",
                    incident_type="ELECTRICAL_FIRE",
                    severity=EventSeverity.CRITICAL if phase in {SimulationPhase.CRITICAL, SimulationPhase.EVACUATION, SimulationPhase.RESPONSE} else EventSeverity.WARNING,
                    status="RESOLVED" if phase == SimulationPhase.RESOLVED else "ACTIVE",
                    zone_id="room-electrical-01",
                    description="Electrical Room Fire",
                )
            ]

        crews: list[ResponseCrew] = []
        drones: list[InspectionDrone] = []
        dispatch_queue: list[DispatchTask] = []

        for crew in base_state.crews:
            if crew.crew_id == "crew-1" and phase in {SimulationPhase.CRITICAL, SimulationPhase.EVACUATION, SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED} and not scenario.sensor_anomaly_mode:
                if elapsed_seconds < 63:
                    status = ResourceStatus.ASSIGNED
                    eta_minutes = 3.0
                elif elapsed_seconds < 78:
                    status = ResourceStatus.EN_ROUTE
                    eta_minutes = max(0.2, (180 - (elapsed_seconds - 63) * 10) / 60)
                else:
                    status = ResourceStatus.ON_SCENE
                    eta_minutes = 0.0
                crews.append(crew.model_copy(update={"status": status, "current_zone_id": "room-electrical-01", "eta_minutes": eta_minutes}))
                if status != ResourceStatus.ON_SCENE:
                    dispatch_queue.append(
                        DispatchTask(
                            task_id="TASK-CREW-1",
                            resource_id="crew-1",
                            resource_type="crew",
                            status=status,
                            target_zone_id="room-electrical-01",
                            description="Electrical Room Fire response",
                        )
                    )
            else:
                crews.append(crew.model_copy(update={"status": ResourceStatus.AVAILABLE, "current_zone_id": None, "eta_minutes": 0.0}))

        for drone in base_state.drones:
            if drone.drone_id == "drone-1" and phase in {SimulationPhase.CRITICAL, SimulationPhase.EVACUATION, SimulationPhase.RESPONSE, SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED} and not scenario.sensor_anomaly_mode:
                if elapsed_seconds < 60:
                    status = ResourceStatus.ASSIGNED
                    eta_minutes = 2.0
                elif elapsed_seconds < 72:
                    status = ResourceStatus.EN_ROUTE
                    eta_minutes = max(0.1, (120 - (elapsed_seconds - 60) * 10) / 60)
                else:
                    status = ResourceStatus.ON_SCENE
                    eta_minutes = 0.0
                drones.append(drone.model_copy(update={"status": status, "current_zone_id": "corridor-c" if status == ResourceStatus.ON_SCENE else "room-electrical-01", "eta_minutes": eta_minutes}))
                if status != ResourceStatus.ON_SCENE:
                    dispatch_queue.append(
                        DispatchTask(
                            task_id="TASK-DRONE-1",
                            resource_id="drone-1",
                            resource_type="drone",
                            status=status,
                            target_zone_id="room-electrical-01",
                            description="Electrical Room Fire aerial inspection",
                        )
                    )
            else:
                drones.append(drone.model_copy(update={"status": ResourceStatus.AVAILABLE, "current_zone_id": None, "eta_minutes": 0.0}))

        if phase in {SimulationPhase.CONTAINMENT, SimulationPhase.RESOLVED}:
            average_eta = 0.0
        elif dispatch_queue:
            average_eta = round(sum(task.status == ResourceStatus.EN_ROUTE for task in dispatch_queue) * 1.5 + 1.5, 2)
        else:
            average_eta = 0.0

        return base_state.model_copy(
            update={
                "last_updated": utc_now(),
                "crews": crews,
                "drones": drones,
                "active_incidents": incidents,
                "dispatch_queue": dispatch_queue,
                "average_response_eta": average_eta,
            },
            deep=True,
        )

    def _handle_approval_gate_locked(self, elapsed_seconds: int, risk_level: RiskLevel) -> None:
        if self._current_scenario is None or self._current_scenario.sensor_anomaly_mode:
            return
        if elapsed_seconds < 70:
            return
        if self.HVAC_ISOLATION_ACTION in self._state.approved_actions or self.HVAC_ISOLATION_ACTION in self._state.rejected_actions:
            return
        if self._state.pending_approval is None:
            approval_id = f"APR-{self._state.run_id[-6:].upper()}-001" if self._state.run_id else "APR-001"
            self._state.pending_approval = ApprovalState(
                approval_id=approval_id,
                action_type=self.HVAC_ISOLATION_TYPE,
                action_description=self.HVAC_ISOLATION_ACTION,
                risk_level=risk_level,
                requested_simulation_time=elapsed_seconds,
                status=ApprovalStatus.PENDING,
                auto_approve=self._state.auto_approve,
                message=self.HVAC_ISOLATION_REASON,
            )
            self._logger.info("[SIM] Approval required for %s", self.HVAC_ISOLATION_TYPE)
            self._logger.info("[SIM] auto_approve=%s", self._state.auto_approve)
            self._publish_event(
                event_type=EventType.APPROVAL_REQUIRED,
                source_twin="orchestrator",
                severity=EventSeverity.WARNING,
                message="HVAC Zone 3 isolation approval requested.",
                payload={
                    "approval_id": approval_id,
                    "action_type": self.HVAC_ISOLATION_TYPE,
                    "action_description": self.HVAC_ISOLATION_ACTION,
                    "reason": self.HVAC_ISOLATION_REASON,
                    "risk": risk_level.value,
                },
            )
            if not self._state.auto_approve:
                self._state.status = SimulationStatus.WAITING_FOR_APPROVAL
                self._state.is_paused = True
                self._state.pause_reason = SimulationPauseReason.AWAITING_APPROVAL
                self._logger.info("[SIM] Entering WAITING_FOR_APPROVAL at t=%s", elapsed_seconds)
                self._publish_event(
                    event_type=EventType.SIMULATION_PAUSED,
                    source_twin="system",
                    severity=EventSeverity.WARNING,
                    message="Simulation paused awaiting human approval.",
                    payload={"pause_reason": SimulationPauseReason.AWAITING_APPROVAL.value},
                )
                self._store_run_summary_locked(SimulationStatus.WAITING_FOR_APPROVAL)
        elif self._state.auto_approve and self._state.pending_approval.status == ApprovalStatus.PENDING and elapsed_seconds >= self._state.pending_approval.requested_simulation_time + 3:
            self._resolve_approval_by_id_locked(
                approval_id=self._state.pending_approval.approval_id,
                approval_status=ApprovalStatus.APPROVED,
                decision_source="AUTO_APPROVED_DEMO_ACTION",
            )

    def _approval_effective(self) -> bool:
        return self.HVAC_ISOLATION_ACTION in self._state.approved_actions

    def _approval_decision_missing(self) -> bool:
        return self.HVAC_ISOLATION_ACTION not in self._state.approved_actions and self.HVAC_ISOLATION_ACTION not in self._state.rejected_actions

    def _can_complete_scenario(self, elapsed_seconds: int) -> bool:
        if self._current_scenario is None:
            return False
        if self._approval_decision_missing() and elapsed_seconds >= 70:
            return False

        min_resolution_time = self.REJECTED_BRANCH_RESOLUTION_TARGET
        if self._state.governance_decision == GovernanceDecision.HVAC_ISOLATION_APPROVED:
            min_resolution_time = self.APPROVED_BRANCH_RESOLUTION_TARGET

        if elapsed_seconds < min_resolution_time:
            return False
        return self._is_stable_resolution_condition()

    def _apply_governance_branch_to_sensor_profile(self, sensor_profile, elapsed_seconds: int):
        decision = self._state.governance_decision
        if decision == GovernanceDecision.HVAC_ISOLATION_APPROVED and elapsed_seconds >= 73:
            branch_elapsed = max(0, elapsed_seconds - 73)
            smoke_scale = max(0.45, 1.0 - branch_elapsed * 0.008)
            temperature_scale = max(0.75, 1.0 - branch_elapsed * 0.004)
            return sensor_profile.model_copy(
                update={
                    "smoke_level": round(sensor_profile.smoke_level * smoke_scale, 3),
                    "co_level": round(sensor_profile.co_level * max(0.55, 1.0 - branch_elapsed * 0.007), 2),
                    "temperature": round(sensor_profile.temperature * temperature_scale, 2),
                    "hvac_effect": round(sensor_profile.hvac_effect * 0.7, 2),
                }
            )

        if decision == GovernanceDecision.HVAC_ISOLATION_REJECTED and elapsed_seconds >= 73:
            branch_elapsed = max(0, elapsed_seconds - 73)
            smoke_scale = min(1.35, 1.0 + branch_elapsed * 0.004)
            return sensor_profile.model_copy(
                update={
                    "smoke_level": round(sensor_profile.smoke_level * smoke_scale, 3),
                    "co_level": round(sensor_profile.co_level * min(1.28, 1.0 + branch_elapsed * 0.003), 2),
                    "temperature": round(sensor_profile.temperature * min(1.1, 1.0 + branch_elapsed * 0.0015), 2),
                    "hvac_effect": round(sensor_profile.hvac_effect * 1.15, 2),
                }
            )

        return sensor_profile

    def _is_stable_resolution_condition(self) -> bool:
        if self._state.pending_approval is not None:
            return False

        fire_state = self._fire_twin_service.get_state()
        building_state = self._building_twin_service.get_state()
        occupancy_state = self._occupancy_twin_service.get_state()
        response_state = self._response_twin_service.get_state()

        hazard_controlled = fire_state.risk_level != RiskLevel.CRITICAL and fire_state.smoke_level <= 0.2
        containment_achieved = any(sprinkler.zone_id == "zone-1a" and sprinkler.is_active for sprinkler in building_state.sprinklers)
        evacuation_stable = occupancy_state.evacuating_count == 0 and occupancy_state.evacuated_count >= self._current_scenario.affected_zone_occupancy
        response_completed = all(task.status == ResourceStatus.ON_SCENE for task in response_state.dispatch_queue) or not response_state.dispatch_queue
        incidents_resolved = all(incident.status == "RESOLVED" for incident in response_state.active_incidents)

        return bool(hazard_controlled and containment_achieved and evacuation_stable and response_completed and incidents_resolved)

    def _derive_outcome_quality(self) -> OutcomeQuality:
        if self._state.governance_decision == GovernanceDecision.HVAC_ISOLATION_REJECTED:
            return OutcomeQuality.DEGRADED
        return OutcomeQuality.OPTIMAL

    def _decision_impact_summary(self) -> str:
        if self._state.governance_decision == GovernanceDecision.HVAC_ISOLATION_REJECTED:
            return "HVAC isolation was rejected. Smoke propagation continued longer and containment was delayed."
        if self._state.governance_decision == GovernanceDecision.HVAC_ISOLATION_APPROVED:
            return "HVAC isolation was approved. Smoke propagation reduced and containment was achieved earlier."
        return "No governance decision was required."

    def _resolve_approval_by_id_locked(self, *, approval_id: str, approval_status: ApprovalStatus, decision_source: str) -> None:
        approval = self._state.pending_approval
        if approval is None:
            raise SimulationConflictError("No pending approval request exists.")
        if approval.approval_id != approval_id:
            raise SimulationConflictError(f"Approval request '{approval_id}' was not found.")
        if approval.status != ApprovalStatus.PENDING:
            raise SimulationConflictError(f"Approval request '{approval_id}' is no longer pending.")

        approval.status = approval_status
        approval.decision = approval_status
        approval.decided_at = utc_now()
        approval.decision_source = decision_source

        if approval_status == ApprovalStatus.APPROVED:
            if approval.action_description not in self._state.approved_actions:
                self._state.approved_actions.append(approval.action_description)
            self._state.governance_decision = GovernanceDecision.HVAC_ISOLATION_APPROVED
            self._publish_event(
                event_type=EventType.APPROVAL_GRANTED,
                source_twin="orchestrator",
                severity=EventSeverity.WARNING,
                message="HVAC Zone 3 isolation approved.",
                payload={"approval_id": approval.approval_id, "decision_source": decision_source},
            )
            self._publish_event(
                event_type=EventType.INFRASTRUCTURE_STATUS_CHANGED,
                source_twin="building_infrastructure",
                severity=EventSeverity.INFO,
                message="HVAC Zone 3 isolated. Smoke propagation reduction strategy active.",
            )
            self._logger.info("[SIM] Approval %s granted by %s", approval.approval_id, decision_source)
        elif approval_status == ApprovalStatus.REJECTED:
            if approval.action_description not in self._state.rejected_actions:
                self._state.rejected_actions.append(approval.action_description)
            self._state.governance_decision = GovernanceDecision.HVAC_ISOLATION_REJECTED
            self._publish_event(
                event_type=EventType.APPROVAL_REJECTED,
                source_twin="orchestrator",
                severity=EventSeverity.WARNING,
                message="HVAC Zone 3 isolation rejected; continuing alternate containment path.",
                payload={"approval_id": approval.approval_id, "decision_source": decision_source},
            )
            self._publish_event(
                event_type=EventType.INFRASTRUCTURE_STATUS_CHANGED,
                source_twin="building_infrastructure",
                severity=EventSeverity.WARNING,
                message="HVAC Zone 3 remains active. Smoke exposure period is extended.",
            )
            self._logger.info("[SIM] Approval %s rejected by %s", approval.approval_id, decision_source)

        self._state.pending_approval = None
        self._state.status = SimulationStatus.RUNNING
        self._state.is_paused = False
        self._state.pause_reason = None
        self._logger.info("[SIM] Resuming from t=%s", self._state.elapsed_seconds)
        if self._thread is None or not self._thread.is_alive():
            self._start_thread_locked()

    def _publish_event(
        self,
        *,
        event_type: EventType,
        source_twin: str,
        severity: EventSeverity,
        message: str,
        payload: dict[str, object] | None = None,
        building_id: str = "FG-BLDG-01",
        floor_id: str | None = "floor-1",
        zone_id: str | None = None,
        corridor_id: str | None = None,
    ) -> None:
        payload_with_time = {
            "elapsed_seconds": self._state.elapsed_seconds,
            "simulation_time": f"{self._state.elapsed_seconds // 60:02d}:{self._state.elapsed_seconds % 60:02d}",
            "scenario_id": self._state.scenario_id,
            "phase": self._state.phase.value,
            **(payload or {}),
        }
        self._event_bus.publish(
            DigitalTwinEvent(
                event_type=event_type,
                source_twin=source_twin,
                target_twins=["orchestrator"],
                severity=severity,
                building_id=building_id,
                floor_id=floor_id,
                zone_id=zone_id,
                corridor_id=corridor_id,
                message=message,
                payload=payload_with_time,
            )
        )

    def _store_run_summary_locked(self, status: SimulationStatus) -> None:
        if self._state.run_id is None or self._state.started_at is None or self._current_scenario is None:
            return
        summary = SimulationRunSummary(
            run_id=self._state.run_id,
            scenario=self._current_scenario.name,
            started_at=self._state.started_at,
            completed_at=self._state.completed_at,
            duration=self._state.elapsed_seconds,
            max_risk=str(self._metrics.get("max_risk") or RiskLevel.NORMAL.value),
            occupants_at_risk=self._current_scenario.affected_zone_occupancy,
            evacuated=self._occupancy_twin_service.get_state().evacuated_count,
            response_dispatch_time=self._metrics.get("response_dispatch_time"),
            containment_time=self._metrics.get("containment_time"),
            status=status,
            time_to_warning=self._metrics.get("time_to_warning"),
            time_to_critical=self._metrics.get("time_to_critical"),
            time_to_evacuation=self._metrics.get("time_to_evacuation"),
            time_to_first_dispatch=self._metrics.get("time_to_first_dispatch"),
            time_to_first_response=self._metrics.get("time_to_first_response"),
            time_to_containment=self._metrics.get("time_to_containment"),
            time_to_resolution=self._metrics.get("time_to_resolution"),
            evacuation_completion_time=self._metrics.get("evacuation_completion_time"),
            peak_congestion=str(self._metrics.get("peak_congestion") or CongestionLevel.LOW.value),
            resources_dispatched=int(self._metrics.get("resources_dispatched") or 0),
            unsafe_zone_duration=int(self._metrics.get("unsafe_zone_duration") or 0),
            risk_exposure_score=round(float(self._metrics.get("risk_exposure_score") or 0.0), 3),
            governance_decision=self._state.governance_decision,
            outcome_quality=self._state.outcome_quality,
            decision_impact_summary=self._decision_impact_summary(),
            model_version=str(self._metrics.get("model_version")) if self._metrics.get("model_version") else None,
            prediction_source=PredictionSource(str(self._metrics.get("prediction_source") or PredictionSource.NOT_AVAILABLE.value)),
            max_critical_probability=round(float(self._metrics.get("max_critical_probability") or 0.0), 6),
            first_warning_prediction_time=self._metrics.get("first_warning_prediction_time"),
            first_critical_prediction_time=self._metrics.get("first_critical_prediction_time"),
            static_plan_metrics=self._metrics.get("static_plan_metrics"),
            shortest_path_metrics=self._metrics.get("shortest_path_metrics"),
            twin_optimized_metrics=self._metrics.get("twin_optimized_metrics"),
        )
        self._state.latest_run_summary = summary.model_dump(mode="json")
        if self._runs and self._runs[-1].run_id == summary.run_id:
            self._runs[-1] = summary
        elif not self._runs or self._runs[-1].run_id != summary.run_id:
            self._runs.append(summary)