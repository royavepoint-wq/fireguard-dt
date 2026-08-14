from __future__ import annotations

from fastapi import APIRouter

from app.services import roi_calculator
from app.services.roi.models import RoiCalculationRequest, RoiScenarioSetResponse

router = APIRouter(prefix="/api/roi")


@router.get("/assumptions", response_model=RoiScenarioSetResponse)
def get_roi_assumptions() -> RoiScenarioSetResponse:
    defaults = roi_calculator.assumptions()
    return RoiScenarioSetResponse(scenarios=list(defaults.values()))


@router.get("/scenarios", response_model=RoiScenarioSetResponse)
def get_roi_scenarios() -> RoiScenarioSetResponse:
    defaults = roi_calculator.assumptions()
    return RoiScenarioSetResponse(scenarios=list(defaults.values()))


@router.post("/calculate")
def calculate_roi(request: RoiCalculationRequest):
    return roi_calculator.calculate(request)
