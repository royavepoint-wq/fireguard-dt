from __future__ import annotations

from pydantic import Field, field_validator

from app.models.common import APIModel
from app.models.occupancy import RouteCoordinate, RouteStrategy, RouteStatus


class EvacuationRouteRequest(APIModel):
    start_zone_id: str
    strategy: RouteStrategy = RouteStrategy.TWIN_OPTIMIZED
    target_exit_id: str | None = None


class EvacuationRouteResponse(APIModel):
    strategy: RouteStrategy
    algorithm: str
    start_zone_id: str
    selected_exit: str | None
    path_nodes: list[str] = Field(default_factory=list)
    path_coordinates: list[RouteCoordinate] = Field(default_factory=list)
    distance_meters: float = 0.0
    total_cost: float = 0.0
    fire_risk_cost: float = 0.0
    smoke_risk_cost: float = 0.0
    congestion_cost: float = 0.0
    hazard_exposure_score: float = 0.0
    peak_route_congestion: float = 0.0
    unsafe_segments: int = 0
    estimated_time_seconds: float = 0.0
    status: RouteStatus
    recalculation_trigger: str | None = None

    @field_validator(
        "distance_meters",
        "total_cost",
        "fire_risk_cost",
        "smoke_risk_cost",
        "congestion_cost",
        "hazard_exposure_score",
        "peak_route_congestion",
        "estimated_time_seconds",
    )
    @classmethod
    def validate_non_negative(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("metric values must be non-negative")
        return value


class EvacuationComparisonResponse(APIModel):
    start_zone_id: str
    target_exit_id: str | None = None
    results: list[EvacuationRouteResponse] = Field(default_factory=list)
