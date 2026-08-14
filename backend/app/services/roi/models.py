from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.models.common import APIModel


class RoiScenario(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    BASE = "BASE"
    OPTIMISTIC = "OPTIMISTIC"


class RoiAssumptions(APIModel):
    scenario: RoiScenario
    currency: str = "SGD"
    illustrative_label: str = "Illustrative Project Assumption"

    iot_sensor_integration: float
    edge_gateway_infrastructure: float
    twin_platform_development: float
    ml_model_development: float
    security_hardening: float
    training_and_drills: float

    annual_cloud_operations: float
    annual_maintenance: float

    avoided_downtime: float
    damage_risk_reduction: float
    maintenance_savings: float
    response_efficiency: float
    false_alarm_reduction: float
    compliance_preparedness_value: float


class RoiCalculationRequest(APIModel):
    scenario: RoiScenario = RoiScenario.BASE
    assumptions_override: RoiAssumptions | None = None


class RoiCalculationResult(APIModel):
    scenario: RoiScenario
    currency: str
    illustrative_label: str

    initial_investment: float
    annual_operating_cost: float
    annual_benefit: float
    annual_net_benefit: float
    payback_months: float | None = None
    payback_statement: str

    three_year_cost: float
    three_year_benefit: float
    three_year_roi_percent: float

    cost_breakdown: dict[str, float] = Field(default_factory=dict)
    benefit_breakdown: dict[str, float] = Field(default_factory=dict)
    technical_evidence: dict[str, float | str] = Field(default_factory=dict)
    assumption_disclosure: str


class RoiScenarioSetResponse(APIModel):
    scenarios: list[RoiAssumptions]
