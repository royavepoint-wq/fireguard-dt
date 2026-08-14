from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class APIModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False)


class TwinStatus(StrEnum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class RiskLevel(StrEnum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class SensorHealth(StrEnum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    FAULT = "FAULT"


class ResourceStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE = "EN_ROUTE"
    ON_SCENE = "ON_SCENE"
    UNAVAILABLE = "UNAVAILABLE"


class EventSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class SpatialReference(APIModel):
    building_id: str | None = None
    floor_id: str | None = None
    zone_id: str | None = None
    room_id: str | None = None
    corridor_id: str | None = None
    exit_id: str | None = None