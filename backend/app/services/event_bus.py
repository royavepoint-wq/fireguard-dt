from __future__ import annotations

from collections import deque
from threading import Lock

from app.models.events import DigitalTwinEvent


class InMemoryEventBus:
    def __init__(self, max_events: int = 500) -> None:
        self._events: deque[DigitalTwinEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def publish(self, event: DigitalTwinEvent) -> DigitalTwinEvent:
        with self._lock:
            self._events.append(event)
        return event

    def get_recent_events(self, limit: int | None = None) -> list[DigitalTwinEvent]:
        with self._lock:
            events = list(self._events)
        if limit is None:
            return events
        return events[-limit:]

    def get_events_by_twin(self, source_twin: str) -> list[DigitalTwinEvent]:
        with self._lock:
            return [event for event in self._events if event.source_twin == source_twin]

    def clear_events(self) -> None:
        with self._lock:
            self._events.clear()