from __future__ import annotations

from fastapi import APIRouter

from app.models.evacuation import EvacuationComparisonResponse, EvacuationRouteRequest, EvacuationRouteResponse
from app.services import building_twin_service, evacuation_route_optimizer, fire_twin_service, occupancy_twin_service

router = APIRouter(prefix="/api/evacuation")


@router.post("/route", response_model=EvacuationRouteResponse)
def compute_route(request: EvacuationRouteRequest) -> EvacuationRouteResponse:
    return evacuation_route_optimizer.route(
        start_zone_id=request.start_zone_id,
        strategy=request.strategy,
        target_exit_id=request.target_exit_id,
        fire_state=fire_twin_service.get_state(),
        building_state=building_twin_service.get_state(),
        occupancy_state=occupancy_twin_service.get_state(),
    )


@router.post("/compare", response_model=EvacuationComparisonResponse)
def compare_route_strategies(request: EvacuationRouteRequest) -> EvacuationComparisonResponse:
    return evacuation_route_optimizer.compare(
        start_zone_id=request.start_zone_id,
        target_exit_id=request.target_exit_id,
        fire_state=fire_twin_service.get_state(),
        building_state=building_twin_service.get_state(),
        occupancy_state=occupancy_twin_service.get_state(),
    )
