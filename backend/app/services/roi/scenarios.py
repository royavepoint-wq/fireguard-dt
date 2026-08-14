from __future__ import annotations

from app.services.roi.assumptions import default_assumptions
from app.services.roi.models import RoiAssumptions, RoiScenario


def get_roi_scenarios() -> list[RoiAssumptions]:
    mapping = default_assumptions()
    return [mapping[RoiScenario.CONSERVATIVE], mapping[RoiScenario.BASE], mapping[RoiScenario.OPTIMISTIC]]
