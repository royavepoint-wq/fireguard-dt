from __future__ import annotations

from fastapi import APIRouter

from app.services import (
    building_twin_service,
    fire_twin_service,
    occupancy_twin_service,
    orchestrator_service,
    response_twin_service,
    simulation_engine,
)

router = APIRouter(prefix="/api")


@router.get("/system/status")
def system_status() -> dict[str, object]:
    orchestrator_snapshot = orchestrator_service.get_snapshot()
    return {
        "system_status": orchestrator_snapshot.status,
        "simulation_status": simulation_engine.get_status().status,
        "active_scenario": simulation_engine.get_status().scenario_id,
        "twins": {
            "fire_environment": fire_twin_service.get_state().status,
            "building_infrastructure": building_twin_service.get_state().status,
            "occupancy_evacuation": occupancy_twin_service.get_state().status,
            "emergency_response": response_twin_service.get_state().status,
        },
        "orchestrator": orchestrator_snapshot.status,
    }