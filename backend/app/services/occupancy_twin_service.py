from __future__ import annotations

from app.models.common import EventSeverity, utc_now
from app.models.events import DigitalTwinEvent, EventType
from app.models.occupancy import (
    CongestionLevel,
    OccupancyEvacuationTwinState,
    OccupancyEvacuationTwinUpdate,
    build_default_occupancy_state,
)
from app.services.event_bus import InMemoryEventBus


class OccupancyTwinService:
    def __init__(self, event_bus: InMemoryEventBus) -> None:
        self._event_bus = event_bus
        self._state = build_default_occupancy_state()

    def get_state(self) -> OccupancyEvacuationTwinState:
        return self._state.model_copy(deep=True)

    def replace_state(
        self,
        state: OccupancyEvacuationTwinState,
        *,
        publish_event: bool = False,
        event_type: EventType = EventType.TWIN_STATE_UPDATED,
        message: str = "Occupancy & Evacuation twin state updated.",
        severity: EventSeverity | None = None,
        payload: dict[str, object] | None = None,
    ) -> OccupancyEvacuationTwinState:
        self._state = state
        if publish_event:
            resolved_severity = severity or (
                EventSeverity.WARNING if self._state.congestion_level != CongestionLevel.LOW else EventSeverity.INFO
            )
            self._event_bus.publish(
                DigitalTwinEvent(
                    event_type=event_type,
                    source_twin=self._state.twin_id,
                    target_twins=["orchestrator", "response"],
                    severity=resolved_severity,
                    building_id=self._state.building_id,
                    message=message,
                    payload=payload or {},
                )
            )
        return self.get_state()

    def update_state(self, update: OccupancyEvacuationTwinUpdate) -> OccupancyEvacuationTwinState:
        payload = update.model_dump(exclude_unset=True)
        merged_payload = {**self._state.model_dump(), **payload, "last_updated": utc_now()}
        if "zones" in payload and "total_occupancy" not in payload:
            merged_payload["total_occupancy"] = sum(zone["occupancy_count"] for zone in payload["zones"])
        merged_state = OccupancyEvacuationTwinState.model_validate(merged_payload)
        return self.replace_state(
            merged_state,
            publish_event=True,
            event_type=EventType.TWIN_STATE_UPDATED,
            message="Occupancy & Evacuation twin state updated.",
            payload={"updated_fields": sorted(payload.keys())},
        )

    def reset_state(self) -> OccupancyEvacuationTwinState:
        return self.replace_state(
            build_default_occupancy_state(),
            publish_event=True,
            event_type=EventType.SYSTEM_INITIALIZED,
            message="Occupancy & Evacuation twin reset to baseline demo state.",
            severity=EventSeverity.INFO,
        )