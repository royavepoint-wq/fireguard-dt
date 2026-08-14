from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import Field

from app.models.common import APIModel, EventSeverity, SpatialReference, utc_now


class EventType(StrEnum):
    SYSTEM_INITIALIZED = "SYSTEM_INITIALIZED"
    SIMULATION_STARTED = "SIMULATION_STARTED"
    SIMULATION_PAUSED = "SIMULATION_PAUSED"
    SIMULATION_RESUMED = "SIMULATION_RESUMED"
    SIMULATION_STOPPED = "SIMULATION_STOPPED"
    SIMULATION_PHASE_CHANGED = "SIMULATION_PHASE_CHANGED"
    SIMULATION_COMPLETED = "SIMULATION_COMPLETED"
    TWIN_STATE_UPDATED = "TWIN_STATE_UPDATED"
    SENSOR_UPDATE = "SENSOR_UPDATE"
    RISK_LEVEL_CHANGED = "RISK_LEVEL_CHANGED"
    INFRASTRUCTURE_STATUS_CHANGED = "INFRASTRUCTURE_STATUS_CHANGED"
    OCCUPANCY_UPDATED = "OCCUPANCY_UPDATED"
    ROUTE_UPDATED = "ROUTE_UPDATED"
    ROUTE_RECALCULATION_REQUESTED = "ROUTE_RECALCULATION_REQUESTED"
    ROUTE_BLOCKED = "ROUTE_BLOCKED"
    NO_SAFE_ROUTE = "NO_SAFE_ROUTE"
    RESOURCE_STATUS_CHANGED = "RESOURCE_STATUS_CHANGED"
    DISPATCH_CREATED = "DISPATCH_CREATED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"


class DigitalTwinEvent(SpatialReference):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    source_twin: str
    target_twins: list[str] = Field(default_factory=list)
    severity: EventSeverity = EventSeverity.INFO
    timestamp: datetime = Field(default_factory=utc_now)
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)