from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.events import DigitalTwinEvent
from app.services import event_bus

router = APIRouter(prefix="/api")


@router.get("/events", response_model=list[DigitalTwinEvent])
def get_events(source_twin: str | None = Query(default=None)) -> list[DigitalTwinEvent]:
    if source_twin:
        return event_bus.get_events_by_twin(source_twin)
    return event_bus.get_recent_events()


@router.delete("/events")
def clear_events() -> dict[str, str]:
    event_bus.clear_events()
    return {"status": "cleared"}