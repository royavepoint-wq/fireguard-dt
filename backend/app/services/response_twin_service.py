from __future__ import annotations

from app.models.common import EventSeverity, utc_now
from app.models.events import DigitalTwinEvent, EventType
from app.models.response import (
    EmergencyResponseTwinState,
    EmergencyResponseTwinUpdate,
    build_default_response_state,
)
from app.services.event_bus import InMemoryEventBus


class ResponseTwinService:
    def __init__(self, event_bus: InMemoryEventBus) -> None:
        self._event_bus = event_bus
        self._state = build_default_response_state()

    def get_state(self) -> EmergencyResponseTwinState:
        return self._state.model_copy(deep=True)

    def replace_state(
        self,
        state: EmergencyResponseTwinState,
        *,
        publish_event: bool = False,
        event_type: EventType = EventType.TWIN_STATE_UPDATED,
        message: str = "Emergency Response twin state updated.",
        severity: EventSeverity | None = None,
        payload: dict[str, object] | None = None,
    ) -> EmergencyResponseTwinState:
        self._state = state
        if publish_event:
            is_busy = any(crew.status != "AVAILABLE" for crew in self._state.crews) or bool(self._state.dispatch_queue)
            resolved_severity = severity or (EventSeverity.WARNING if is_busy else EventSeverity.INFO)
            self._event_bus.publish(
                DigitalTwinEvent(
                    event_type=event_type,
                    source_twin=self._state.twin_id,
                    target_twins=["orchestrator"],
                    severity=resolved_severity,
                    message=message,
                    payload=payload or {},
                )
            )
        return self.get_state()

    def update_state(self, update: EmergencyResponseTwinUpdate) -> EmergencyResponseTwinState:
        payload = update.model_dump(exclude_unset=True)
        merged_state = EmergencyResponseTwinState.model_validate(
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
            message="Emergency Response twin state updated.",
            payload={"updated_fields": sorted(payload.keys())},
        )

    def reset_state(self) -> EmergencyResponseTwinState:
        return self.replace_state(
            build_default_response_state(),
            publish_event=True,
            event_type=EventType.SYSTEM_INITIALIZED,
            message="Emergency Response twin reset to baseline demo state.",
            severity=EventSeverity.INFO,
        )