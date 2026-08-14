from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from app.models.common import APIModel, TwinStatus, utc_now


class EvacuationStatus(StrEnum):
    STABLE = "STABLE"
    EVACUATING = "EVACUATING"
    EVACUATED = "EVACUATED"


class CongestionLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class RouteStatus(StrEnum):
    OPEN = "OPEN"
    CONGESTED = "CONGESTED"
    BLOCKED = "BLOCKED"
    NO_SAFE_ROUTE = "NO_SAFE_ROUTE"


class RouteStrategy(StrEnum):
    STATIC_PLAN = "STATIC_PLAN"
    SHORTEST_PATH = "SHORTEST_PATH"
    TWIN_OPTIMIZED = "TWIN_OPTIMIZED"


class RouteCoordinate(APIModel):
    node_id: str
    x: float
    y: float
    z: float
    floor_id: str


class OccupancyZone(APIModel):
    zone_id: str
    occupancy_count: int
    density: float
    vulnerable_count: int = 0
    evacuation_status: EvacuationStatus = EvacuationStatus.STABLE

    @field_validator("occupancy_count", "vulnerable_count")
    @classmethod
    def validate_counts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("counts must be non-negative")
        return value

    @field_validator("density")
    @classmethod
    def validate_density(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("density must be non-negative")
        return value


class EvacuationRoute(APIModel):
    route_id: str
    from_zone_id: str
    to_exit_id: str
    status: RouteStatus = RouteStatus.OPEN
    estimated_capacity: int
    strategy: RouteStrategy = RouteStrategy.STATIC_PLAN
    path_nodes: list[str] = Field(default_factory=list)
    path_coordinates: list[RouteCoordinate] = Field(default_factory=list)
    distance_meters: float = 0.0
    estimated_time_seconds: float = 0.0
    total_cost: float = 0.0
    fire_risk_cost: float = 0.0
    smoke_risk_cost: float = 0.0
    congestion_cost: float = 0.0
    hazard_exposure_score: float = 0.0
    peak_route_congestion: float = 0.0
    unsafe_segments: int = 0

    @field_validator("estimated_capacity")
    @classmethod
    def validate_capacity(cls, value: int) -> int:
        if value < 0:
            raise ValueError("estimated_capacity must be non-negative")
        return value

    @field_validator(
        "distance_meters",
        "estimated_time_seconds",
        "total_cost",
        "fire_risk_cost",
        "smoke_risk_cost",
        "congestion_cost",
        "hazard_exposure_score",
        "peak_route_congestion",
    )
    @classmethod
    def validate_non_negative(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("route metric values must be non-negative")
        return value

    @field_validator("unsafe_segments")
    @classmethod
    def validate_unsafe_segments(cls, value: int) -> int:
        if value < 0:
            raise ValueError("unsafe_segments must be non-negative")
        return value


class OccupancyEvacuationTwinState(APIModel):
    twin_id: str = "occupancy_evacuation"
    name: str = "Occupancy & Evacuation Twin"
    status: TwinStatus = TwinStatus.ONLINE
    last_updated: datetime = Field(default_factory=utc_now)

    building_id: str = "FG-BLDG-01"
    total_occupancy: int = 243
    zones: list[OccupancyZone] = Field(default_factory=list)
    evacuating_count: int = 0
    evacuated_count: int = 0
    congestion_level: CongestionLevel = CongestionLevel.LOW
    active_routes: list[EvacuationRoute] = Field(default_factory=list)

    @field_validator("total_occupancy", "evacuating_count", "evacuated_count")
    @classmethod
    def validate_non_negative_counts(cls, value: int) -> int:
        if value < 0:
            raise ValueError("occupancy counts must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_totals(self) -> "OccupancyEvacuationTwinState":
        if self.evacuating_count + self.evacuated_count > self.total_occupancy:
            raise ValueError("evacuating_count and evacuated_count cannot exceed total_occupancy")
        return self


class OccupancyEvacuationTwinUpdate(APIModel):
    name: str | None = None
    status: TwinStatus | None = None
    building_id: str | None = None
    total_occupancy: int | None = None
    zones: list[OccupancyZone] | None = None
    evacuating_count: int | None = None
    evacuated_count: int | None = None
    congestion_level: CongestionLevel | None = None
    active_routes: list[EvacuationRoute] | None = None


def build_default_occupancy_state() -> OccupancyEvacuationTwinState:
    zones = [
        OccupancyZone(zone_id="zone-1a", occupancy_count=43, density=0.41, vulnerable_count=2),
        OccupancyZone(zone_id="zone-1b", occupancy_count=38, density=0.37, vulnerable_count=3),
        OccupancyZone(zone_id="zone-2a", occupancy_count=58, density=0.51, vulnerable_count=4),
        OccupancyZone(zone_id="zone-2b", occupancy_count=39, density=0.35, vulnerable_count=2),
        OccupancyZone(zone_id="zone-3a", occupancy_count=65, density=0.57, vulnerable_count=5),
    ]
    return OccupancyEvacuationTwinState(
        total_occupancy=sum(zone.occupancy_count for zone in zones),
        zones=zones,
        active_routes=[
            EvacuationRoute(route_id="route-a", from_zone_id="zone-1a", to_exit_id="exit-a", estimated_capacity=80),
            EvacuationRoute(route_id="route-b", from_zone_id="zone-1a", to_exit_id="exit-b", status=RouteStatus.CONGESTED, estimated_capacity=65),
        ],
    )