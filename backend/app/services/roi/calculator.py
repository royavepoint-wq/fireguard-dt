from __future__ import annotations

from pathlib import Path
import json

from app.services.roi.assumptions import default_assumptions
from app.services.roi.models import RoiAssumptions, RoiCalculationRequest, RoiCalculationResult, RoiScenario


class RoiCalculator:
    def __init__(self) -> None:
        self._defaults = default_assumptions()
        self._repo_root = Path(__file__).resolve().parents[4]

    def assumptions(self) -> dict[RoiScenario, RoiAssumptions]:
        return self._defaults

    def calculate(self, request: RoiCalculationRequest) -> RoiCalculationResult:
        assumptions = request.assumptions_override or self._defaults[request.scenario]

        cost_breakdown = {
            "iot": assumptions.iot_sensor_integration,
            "platform": assumptions.twin_platform_development + assumptions.edge_gateway_infrastructure,
            "ml": assumptions.ml_model_development,
            "security": assumptions.security_hardening,
            "training": assumptions.training_and_drills,
            "operations": assumptions.annual_cloud_operations + assumptions.annual_maintenance,
        }

        benefit_breakdown = {
            "downtime_reduction": assumptions.avoided_downtime,
            "damage_risk_reduction": assumptions.damage_risk_reduction,
            "maintenance_savings": assumptions.maintenance_savings,
            "response_efficiency": assumptions.response_efficiency,
            "false_alarm_reduction": assumptions.false_alarm_reduction,
            "compliance_value": assumptions.compliance_preparedness_value,
        }

        initial_investment = round(
            assumptions.iot_sensor_integration
            + assumptions.edge_gateway_infrastructure
            + assumptions.twin_platform_development
            + assumptions.ml_model_development
            + assumptions.security_hardening
            + assumptions.training_and_drills,
            2,
        )
        annual_operating_cost = round(assumptions.annual_cloud_operations + assumptions.annual_maintenance, 2)
        annual_benefit = round(sum(benefit_breakdown.values()), 2)
        annual_net_benefit = round(annual_benefit - annual_operating_cost, 2)

        payback_months = None
        payback_statement = "No Payback Within Model Horizon"
        if annual_net_benefit > 0:
            payback_months = round(initial_investment / (annual_net_benefit / 12.0), 2)
            payback_statement = f"{payback_months} months"

        three_year_cost = round(initial_investment + annual_operating_cost * 3.0, 2)
        three_year_benefit = round(annual_benefit * 3.0, 2)
        three_year_roi_percent = round(((three_year_benefit - three_year_cost) / three_year_cost) * 100.0, 2) if three_year_cost > 0 else 0.0

        technical_evidence = self._load_technical_evidence()

        return RoiCalculationResult(
            scenario=assumptions.scenario,
            currency=assumptions.currency,
            illustrative_label=assumptions.illustrative_label,
            initial_investment=initial_investment,
            annual_operating_cost=annual_operating_cost,
            annual_benefit=annual_benefit,
            annual_net_benefit=annual_net_benefit,
            payback_months=payback_months,
            payback_statement=payback_statement,
            three_year_cost=three_year_cost,
            three_year_benefit=three_year_benefit,
            three_year_roi_percent=three_year_roi_percent,
            cost_breakdown=cost_breakdown,
            benefit_breakdown=benefit_breakdown,
            technical_evidence=technical_evidence,
            assumption_disclosure="ROI values are illustrative project assumptions for academic feasibility analysis. They are not observed production financial results.",
        )

    def _load_technical_evidence(self) -> dict[str, float | str]:
        path = self._repo_root / "data" / "experiments" / "strategy_comparison.csv"
        if not path.exists():
            return {"status": "No experiment evidence available yet."}

        # Keep evidence and financial assumptions separate: this only reports measured experiment deltas.
        rows = path.read_text(encoding="utf-8").strip().splitlines()
        if len(rows) <= 1:
            return {"status": "No experiment evidence available yet."}

        headers = rows[0].split(",")
        values = [line.split(",") for line in rows[1:]]
        try:
            hazard_idx = headers.index("hazard_exposure_reduction_vs_static_pct")
            evac_idx = headers.index("evacuation_time_change_vs_static_pct")
            strategy_idx = headers.index("strategy")
        except ValueError:
            return {"status": "Experiment evidence file is missing expected columns."}

        twin_rows = [row for row in values if len(row) > strategy_idx and row[strategy_idx] == "TWIN_OPTIMIZED"]
        if not twin_rows:
            return {"status": "No twin-optimized comparison evidence available yet."}

        def _avg(index: int) -> float:
            vals = []
            for row in twin_rows:
                try:
                    vals.append(float(row[index]))
                except Exception:
                    continue
            return round(sum(vals) / len(vals), 3) if vals else 0.0

        return {
            "status": "Loaded from deterministic experiment outputs",
            "avg_hazard_exposure_reduction_vs_static_pct": _avg(hazard_idx),
            "avg_evacuation_time_change_vs_static_pct": _avg(evac_idx),
        }


def build_roi_results_payload(base_result: RoiCalculationResult) -> dict[str, object]:
    return {
        "base_3_year_roi": base_result.three_year_roi_percent,
        "assumption_disclosure": base_result.assumption_disclosure,
    }
