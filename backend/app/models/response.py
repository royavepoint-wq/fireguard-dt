from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.common import APIModel, EventSeverity, ResourceStatus, TwinStatus, utc_now


class ResponseCrew(APIModel):
    crew_id: str
    name: str
    status: ResourceStatus = ResourceStatus.AVAILABLE
    current_zone_id: str | None = None
    eta_minutes: float = 0.0

    @field_validator("eta_minutes")
    @classmethod
    def validate_eta(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("eta_minutes must be non-negative")
        return value


class InspectionDrone(APIModel):
    drone_id: str
    name: str
    status: ResourceStatus = ResourceStatus.AVAILABLE
    current_zone_id: str | None = None
    battery_level: float = 100.0
    eta_minutes: float = 0.0

    @field_validator("battery_level")
    @classmethod
    def validate_battery(cls, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            raise ValueError("battery_level must be between 0 and 100")
        return value

    @field_validator("eta_minutes")
    @classmethod
    def validate_eta(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("eta_minutes must be non-negative")
        return value


class DispatchTask(APIModel):
    task_id: str
    resource_id: str
    resource_type: str
    status: ResourceStatus = ResourceStatus.ASSIGNED
    target_zone_id: str | None = None
    description: str


class Incident(APIModel):
    incident_id: str
    incident_type: str
    severity: EventSeverity
    status: str
    zone_id: str | None = None
    description: str


class EmergencyResponseTwinState(APIModel):
    twin_id: str = "emergency_response"
    name: str = "Emergency Response Twin"
    status: TwinStatus = TwinStatus.ONLINE
    last_updated: datetime = Field(default_factory=utc_now)

    crews: list[ResponseCrew] = Field(default_factory=list)
    drones: list[InspectionDrone] = Field(default_factory=list)
    active_incidents: list[Incident] = Field(default_factory=list)
    dispatch_queue: list[DispatchTask] = Field(default_factory=list)
    average_response_eta: float = 0.0

    @field_validator("average_response_eta")
    @classmethod
    def validate_average_response_eta(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("average_response_eta must be non-negative")
        return value


class EmergencyResponseTwinUpdate(APIModel):
    name: str | None = None
    status: TwinStatus | None = None
    crews: list[ResponseCrew] | None = None
    drones: list[InspectionDrone] | None = None
    active_incidents: list[Incident] | None = None
    dispatch_queue: list[DispatchTask] | None = None
    average_response_eta: float | None = None


def build_default_response_state() -> EmergencyResponseTwinState:
    return EmergencyResponseTwinState(
        crews=[
            ResponseCrew(crew_id="crew-1", name="Crew 1"),
            ResponseCrew(crew_id="crew-2", name="Crew 2"),
        ],
        drones=[
            InspectionDrone(drone_id="drone-1", name="Drone 1"),
            InspectionDrone(drone_id="drone-2", name="Drone 2"),
        ],
        active_incidents=[],
        dispatch_queue=[],
        average_response_eta=0.0,
    )