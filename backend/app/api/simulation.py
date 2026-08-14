from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import simulation_engine
from app.simulation.engine import SimulationConflictError
from app.simulation.models import SimulationSpeedRequest, SimulationStartRequest, SimulationState

router = APIRouter(prefix="/api/simulation")


@router.get("/status", response_model=SimulationState)
def get_simulation_status() -> SimulationState:
    return simulation_engine.get_status()


@router.get("/scenarios")
def get_simulation_scenarios():
    return simulation_engine.get_scenarios()


@router.get("/runs")
def get_simulation_runs():
    return simulation_engine.get_runs()


@router.post("/start", response_model=SimulationState)
def start_simulation(request: SimulationStartRequest) -> SimulationState:
    try:
        return simulation_engine.start(request)
    except SimulationConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/pause", response_model=SimulationState)
def pause_simulation() -> SimulationState:
    return simulation_engine.pause()


@router.post("/resume", response_model=SimulationState)
def resume_simulation() -> SimulationState:
    return simulation_engine.resume()


@router.post("/stop", response_model=SimulationState)
def stop_simulation() -> SimulationState:
    return simulation_engine.stop()


@router.post("/reset", response_model=SimulationState)
def reset_simulation() -> SimulationState:
    return simulation_engine.reset()


@router.post("/speed", response_model=SimulationState)
def set_simulation_speed(request: SimulationSpeedRequest) -> SimulationState:
    return simulation_engine.set_speed(request.speed_multiplier)


@router.post("/approve", response_model=SimulationState)
def approve_simulation_action() -> SimulationState:
    return simulation_engine.approve_pending_action()


@router.post("/reject", response_model=SimulationState)
def reject_simulation_action() -> SimulationState:
    return simulation_engine.reject_pending_action()


@router.post("/approval/{approval_id}/approve", response_model=SimulationState)
def approve_simulation_action_by_id(approval_id: str) -> SimulationState:
    try:
        return simulation_engine.approve_action_by_id(approval_id)
    except SimulationConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/approval/{approval_id}/reject", response_model=SimulationState)
def reject_simulation_action_by_id(approval_id: str) -> SimulationState:
    try:
        return simulation_engine.reject_action_by_id(approval_id)
    except SimulationConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error