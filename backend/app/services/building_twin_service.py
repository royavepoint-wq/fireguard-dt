from __future__ import annotations

from app.models.building import (
    BuildingInfrastructureTwinState,
    BuildingInfrastructureTwinUpdate,
    build_default_building_state,
)
from app.models.common import EventSeverity, utc_now
from app.models.events import DigitalTwinEvent, EventType
from app.services.event_bus import InMemoryEventBus


class BuildingTwinService:
    def __init__(self, event_bus: InMemoryEventBus) -> None:
        self._event_bus = event_bus
        self._state = build_default_building_state()

    def get_state(self) -> BuildingInfrastructureTwinState:
        return self._state.model_copy(deep=True)

    def replace_state(
        self,
        state: BuildingInfrastructureTwinState,
        *,
        publish_event: bool = False,
        event_type: EventType = EventType.TWIN_STATE_UPDATED,
        message: str = "Building Infrastructure twin state updated.",
        severity: EventSeverity | None = None,
        payload: dict[str, object] | None = None,
    ) -> BuildingInfrastructureTwinState:
        self._state = state
        if publish_event:
            blocked_exit = any(exit_item.is_blocked for exit_item in self._state.exits)
            resolved_severity = severity or (EventSeverity.WARNING if blocked_exit else EventSeverity.INFO)
            self._event_bus.publish(
                DigitalTwinEvent(
                    event_type=event_type,
                    source_twin=self._state.twin_id,
                    target_twins=["orchestrator", "occupancy_evacuation"],
                    severity=resolved_severity,
                    building_id=self._state.building_id,
                    message=message,
                    payload=payload or {},
                )
            )
        return self.get_state()

    def update_state(self, update: BuildingInfrastructureTwinUpdate) -> BuildingInfrastructureTwinState:
        payload = update.model_dump(exclude_unset=True)
        merged_state = BuildingInfrastructureTwinState.model_validate(
            {
                **self._state.model_dump(),
                **payload,
                "last_updated": utc_now(),
            }
        )
        return self.replace_state(
            merged_state,
            publish_event=True,
            event_type=EventType.TWIN_STATE_UPDATED,
            message="Building Infrastructure twin state updated.",
            payload={"updated_fields": sorted(payload.keys())},
        )

    def reset_state(self) -> BuildingInfrastructureTwinState:
        return self.replace_state(
            build_default_building_state(),
            publish_event=True,
            event_type=EventType.SYSTEM_INITIALIZED,
            message="Building Infrastructure twin reset to baseline demo state.",
            severity=EventSeverity.INFO,
        )