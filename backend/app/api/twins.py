from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.models.building import BuildingInfrastructureTwinState, BuildingInfrastructureTwinUpdate
from app.models.fire_environment import FireEnvironmentTwinState, FireEnvironmentTwinUpdate
from app.models.occupancy import OccupancyEvacuationTwinState, OccupancyEvacuationTwinUpdate
from app.models.orchestrator import CombinedDigitalTwinState
from app.models.response import EmergencyResponseTwinState, EmergencyResponseTwinUpdate
from app.services import (
    building_twin_service,
    event_bus,
    fire_twin_service,
    occupancy_twin_service,
    orchestrator_service,
    response_twin_service,
    simulation_engine,
)

router = APIRouter(prefix="/api")


def _raise_validation_error(error: ValidationError) -> None:
    raise HTTPException(status_code=422, detail=json.loads(error.json())) from error


@router.get("/twins/fire", response_model=FireEnvironmentTwinState)
def get_fire_twin() -> FireEnvironmentTwinState:
    return fire_twin_service.get_state()


@router.patch("/twins/fire", response_model=FireEnvironmentTwinState)
def update_fire_twin(update: FireEnvironmentTwinUpdate) -> FireEnvironmentTwinState:
    try:
        return fire_twin_service.update_state(update)
    except ValidationError as error:
        _raise_validation_error(error)


@router.post("/twins/fire/reset", response_model=FireEnvironmentTwinState)
def reset_fire_twin() -> FireEnvironmentTwinState:
    return fire_twin_service.reset_state()


@router.get("/twins/building", response_model=BuildingInfrastructureTwinState)
def get_building_twin() -> BuildingInfrastructureTwinState:
    return building_twin_service.get_state()


@router.patch("/twins/building", response_model=BuildingInfrastructureTwinState)
def update_building_twin(update: BuildingInfrastructureTwinUpdate) -> BuildingInfrastructureTwinState:
    try:
        return building_twin_service.update_state(update)
    except ValidationError as error:
        _raise_validation_error(error)


@router.post("/twins/building/reset", response_model=BuildingInfrastructureTwinState)
def reset_building_twin() -> BuildingInfrastructureTwinState:
    return building_twin_service.reset_state()


@router.get("/twins/occupancy", response_model=OccupancyEvacuationTwinState)
def get_occupancy_twin() -> OccupancyEvacuationTwinState:
    return occupancy_twin_service.get_state()


@router.patch("/twins/occupancy", response_model=OccupancyEvacuationTwinState)
def update_occupancy_twin(update: OccupancyEvacuationTwinUpdate) -> OccupancyEvacuationTwinState:
    try:
        return occupancy_twin_service.update_state(update)
    except ValidationError as error:
        _raise_validation_error(error)


@router.post("/twins/occupancy/reset", response_model=OccupancyEvacuationTwinState)
def reset_occupancy_twin() -> OccupancyEvacuationTwinState:
    return occupancy_twin_service.reset_state()


@router.get("/twins/response", response_model=EmergencyResponseTwinState)
def get_response_twin() -> EmergencyResponseTwinState:
    return response_twin_service.get_state()


@router.patch("/twins/response", response_model=EmergencyResponseTwinState)
def update_response_twin(update: EmergencyResponseTwinUpdate) -> EmergencyResponseTwinState:
    try:
        return response_twin_service.update_state(update)
    except ValidationError as error:
        _raise_validation_error(error)


@router.post("/twins/response/reset", response_model=EmergencyResponseTwinState)
def reset_response_twin() -> EmergencyResponseTwinState:
    return response_twin_service.reset_state()


@router.get("/digital-twin/state", response_model=CombinedDigitalTwinState)
def get_digital_twin_state() -> CombinedDigitalTwinState:
    return orchestrator_service.get_combined_state()


@router.post("/digital-twin/reset", response_model=CombinedDigitalTwinState)
def reset_digital_twin() -> CombinedDigitalTwinState:
    simulation_engine.reset()
    return orchestrator_service.get_combined_state()