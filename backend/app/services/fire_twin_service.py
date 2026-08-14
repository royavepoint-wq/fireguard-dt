from __future__ import annotations

from app.models.common import EventSeverity, RiskLevel, utc_now
from app.models.events import DigitalTwinEvent, EventType
from app.models.fire_environment import (
    FireEnvironmentTwinState,
    FireEnvironmentTwinUpdate,
    build_default_fire_environment_state,
)
from app.services.event_bus import InMemoryEventBus


class FireTwinService:
    def __init__(self, event_bus: InMemoryEventBus) -> None:
        self._event_bus = event_bus
        self._state = build_default_fire_environment_state()

    def get_state(self) -> FireEnvironmentTwinState:
        return self._state.model_copy(deep=True)

    def replace_state(
        self,
        state: FireEnvironmentTwinState,
        *,
        publish_event: bool = False,
        event_type: EventType = EventType.TWIN_STATE_UPDATED,
        message: str = "Fire & Environment twin state updated.",
        severity: EventSeverity | None = None,
        payload: dict[str, object] | None = None,
    ) -> FireEnvironmentTwinState:
        self._state = state
        if publish_event:
            resolved_severity = severity
            if resolved_severity is None:
                if self._state.risk_level == RiskLevel.CRITICAL:
                    resolved_severity = EventSeverity.CRITICAL
                elif self._state.risk_level == RiskLevel.WARNING:
                    resolved_severity = EventSeverity.WARNING
                else:
                    resolved_severity = EventSeverity.INFO
            self._event_bus.publish(
                DigitalTwinEvent(
                    event_type=event_type,
                    source_twin=self._state.twin_id,
                    target_twins=["orchestrator"],
                    severity=resolved_severity,
                    building_id=self._state.building_id,
                    floor_id=self._state.floor_id,
                    zone_id=self._state.zone_id,
                    message=message,
                    payload=payload or {},
                )
            )
        return self.get_state()

    def update_state(self, update: FireEnvironmentTwinUpdate) -> FireEnvironmentTwinState:
        payload = update.model_dump(exclude_unset=True)
        merged_state = FireEnvironmentTwinState.model_validate(
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
            message="Fire & Environment twin state updated.",
            payload={"updated_fields": sorted(payload.keys())},
        )

    def reset_state(self) -> FireEnvironmentTwinState:
        return self.replace_state(
            build_default_fire_environment_state(),
            publish_event=True,
            event_type=EventType.SYSTEM_INITIALIZED,
            message="Fire & Environment twin reset to baseline demo state.",
            severity=EventSeverity.INFO,
        )