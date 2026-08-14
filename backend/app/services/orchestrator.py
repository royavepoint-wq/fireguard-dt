from __future__ import annotations

from app.models.common import RiskLevel, TwinStatus, utc_now
from app.models.ml import FireRiskPredictionRequest
from app.models.orchestrator import CombinedDigitalTwinState, OrchestratorSnapshot, OrchestratorSystemStatus
from app.services.building_twin_service import BuildingTwinService
from app.services.fire_twin_service import FireTwinService
from app.services.ml.fire_predictor import FireRiskPredictor
from app.services.occupancy_twin_service import OccupancyTwinService
from app.services.response_twin_service import ResponseTwinService


class DecisionOrchestratorService:
    WARNING_CONFIDENCE_THRESHOLD = 0.55
    CRITICAL_CONFIDENCE_THRESHOLD = 0.65

    def __init__(
        self,
        fire_twin_service: FireTwinService,
        building_twin_service: BuildingTwinService,
        occupancy_twin_service: OccupancyTwinService,
        response_twin_service: ResponseTwinService,
        fire_risk_predictor: FireRiskPredictor,
        human_oversight: bool = True,
    ) -> None:
        self._fire_twin_service = fire_twin_service
        self._building_twin_service = building_twin_service
        self._occupancy_twin_service = occupancy_twin_service
        self._response_twin_service = response_twin_service
        self._fire_risk_predictor = fire_risk_predictor
        self._human_oversight = human_oversight

    def _build_live_fire_prediction_request(self) -> FireRiskPredictionRequest:
        fire_twin = self._fire_twin_service.get_state()
        building_twin = self._building_twin_service.get_state()
        occupancy_twin = self._occupancy_twin_service.get_state()

        hvac_running = 1
        hvac_zone = next((zone for zone in building_twin.hvac_zones if zone.hvac_zone_id == "hvac-zone-3"), None)
        if hvac_zone is not None and hvac_zone.status == "ISOLATED":
            hvac_running = 0

        sprinkler_active = 1 if any(sprinkler.is_active for sprinkler in building_twin.sprinklers) else 0

        return FireRiskPredictionRequest(
            temperature=fire_twin.temperature,
            temperature_rate=fire_twin.temperature_rate,
            smoke_level=fire_twin.smoke_level,
            co_level=fire_twin.co_level,
            co2_level=fire_twin.co2_level,
            humidity=fire_twin.humidity,
            electrical_load=fire_twin.electrical_load,
            occupancy=float(occupancy_twin.total_occupancy),
            hvac_running=hvac_running,
            sprinkler_active=sprinkler_active,
        )

    def _refresh_fire_twin_prediction(self) -> None:
        prediction = self._fire_risk_predictor.predict(self._build_live_fire_prediction_request())
        current_state = self._fire_twin_service.get_state()
        self._fire_twin_service.replace_state(
            current_state.model_copy(
                update={
                    "fire_risk_probability": float(prediction.probabilities.get(RiskLevel.CRITICAL, 0.0)),
                    "risk_level": prediction.predicted_class,
                    "risk_probabilities": prediction.probabilities,
                    "prediction_source": prediction.prediction_source,
                    "model_version": prediction.model_version,
                    "prediction_confidence": prediction.confidence,
                    "last_updated": prediction.timestamp,
                }
            ),
            publish_event=False,
        )

    def get_snapshot(self) -> OrchestratorSnapshot:
        fire_twin = self._fire_twin_service.get_state()
        building_twin = self._building_twin_service.get_state()
        occupancy_twin = self._occupancy_twin_service.get_state()
        response_twin = self._response_twin_service.get_state()

        alerts: list[str] = []
        if fire_twin.risk_level == RiskLevel.WARNING and fire_twin.prediction_confidence >= self.WARNING_CONFIDENCE_THRESHOLD:
            alerts.append("Fire risk elevated in monitored zone.")
        if fire_twin.risk_level == RiskLevel.CRITICAL and fire_twin.prediction_confidence >= self.CRITICAL_CONFIDENCE_THRESHOLD:
            alerts.append("Critical fire risk detected in monitored zone.")
        blocked_exits = [exit_item.exit_id for exit_item in building_twin.exits if exit_item.is_blocked]
        if blocked_exits:
            alerts.append(f"Blocked exits detected: {', '.join(blocked_exits)}.")
        if occupancy_twin.evacuating_count > 0:
            alerts.append("Occupants currently marked as evacuating.")
        if occupancy_twin.congestion_level != "LOW":
            alerts.append(f"Occupancy congestion is {occupancy_twin.congestion_level}.")
        if response_twin.active_incidents:
            alerts.append("Emergency response incidents are active.")

        twin_statuses = [
            fire_twin.status,
            building_twin.status,
            occupancy_twin.status,
            response_twin.status,
        ]
        if fire_twin.risk_level == RiskLevel.CRITICAL or response_twin.active_incidents:
            status = OrchestratorSystemStatus.CRITICAL
        elif any(twin_status == TwinStatus.OFFLINE for twin_status in twin_statuses):
            status = OrchestratorSystemStatus.DEGRADED
        elif any(twin_status == TwinStatus.DEGRADED for twin_status in twin_statuses):
            status = OrchestratorSystemStatus.DEGRADED
        elif alerts:
            status = OrchestratorSystemStatus.WARNING
        else:
            status = OrchestratorSystemStatus.NORMAL

        return OrchestratorSnapshot(
            status=status,
            human_oversight=self._human_oversight,
            active_alerts=alerts,
            twins_online=sum(1 for twin_status in twin_statuses if twin_status == TwinStatus.ONLINE),
            cross_twin_state={
                "building_id": fire_twin.building_id,
                "fire_risk_probability": fire_twin.fire_risk_probability,
                "risk_level": fire_twin.risk_level,
                "prediction_confidence": fire_twin.prediction_confidence,
                "prediction_source": fire_twin.prediction_source,
                "model_version": fire_twin.model_version,
                "blocked_exits": blocked_exits,
                "total_occupancy": occupancy_twin.total_occupancy,
                "evacuating_count": occupancy_twin.evacuating_count,
                "active_response_incidents": len(response_twin.active_incidents),
                "dispatch_queue_size": len(response_twin.dispatch_queue),
            },
            last_updated=utc_now(),
        )

    def get_combined_state(self) -> CombinedDigitalTwinState:
        self._refresh_fire_twin_prediction()
        return CombinedDigitalTwinState(
            fire_twin=self._fire_twin_service.get_state(),
            building_twin=self._building_twin_service.get_state(),
            occupancy_twin=self._occupancy_twin_service.get_state(),
            response_twin=self._response_twin_service.get_state(),
            orchestrator=self.get_snapshot(),
        )