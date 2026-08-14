from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.models.building import BuildingInfrastructureTwinState
from app.models.common import APIModel, utc_now
from app.models.fire_environment import FireEnvironmentTwinState
from app.models.occupancy import OccupancyEvacuationTwinState
from app.models.response import EmergencyResponseTwinState


class OrchestratorSystemStatus(StrEnum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    DEGRADED = "DEGRADED"


class OrchestratorSnapshot(APIModel):
    status: OrchestratorSystemStatus
    human_oversight: bool = True
    active_alerts: list[str] = Field(default_factory=list)
    twins_online: int
    cross_twin_state: dict[str, Any]
    last_updated: datetime = Field(default_factory=utc_now)


class CombinedDigitalTwinState(APIModel):
    fire_twin: FireEnvironmentTwinState
    building_twin: BuildingInfrastructureTwinState
    occupancy_twin: OccupancyEvacuationTwinState
    response_twin: EmergencyResponseTwinState
    orchestrator: OrchestratorSnapshot