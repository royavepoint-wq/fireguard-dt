from __future__ import annotations

from app.services.roi.models import RoiAssumptions, RoiScenario


def default_assumptions() -> dict[RoiScenario, RoiAssumptions]:
    return {
        RoiScenario.CONSERVATIVE: RoiAssumptions(
            scenario=RoiScenario.CONSERVATIVE,
            iot_sensor_integration=240000,
            edge_gateway_infrastructure=90000,
            twin_platform_development=260000,
            ml_model_development=120000,
            security_hardening=100000,
            training_and_drills=70000,
            annual_cloud_operations=110000,
            annual_maintenance=95000,
            avoided_downtime=140000,
            damage_risk_reduction=170000,
            maintenance_savings=60000,
            response_efficiency=75000,
            false_alarm_reduction=35000,
            compliance_preparedness_value=25000,
        ),
        RoiScenario.BASE: RoiAssumptions(
            scenario=RoiScenario.BASE,
            iot_sensor_integration=220000,
            edge_gateway_infrastructure=85000,
            twin_platform_development=245000,
            ml_model_development=110000,
            security_hardening=95000,
            training_and_drills=65000,
            annual_cloud_operations=100000,
            annual_maintenance=85000,
            avoided_downtime=210000,
            damage_risk_reduction=290000,
            maintenance_savings=95000,
            response_efficiency=115000,
            false_alarm_reduction=60000,
            compliance_preparedness_value=50000,
        ),
        RoiScenario.OPTIMISTIC: RoiAssumptions(
            scenario=RoiScenario.OPTIMISTIC,
            iot_sensor_integration=220000,
            edge_gateway_infrastructure=85000,
            twin_platform_development=245000,
            ml_model_development=110000,
            security_hardening=95000,
            training_and_drills=65000,
            annual_cloud_operations=95000,
            annual_maintenance=80000,
            avoided_downtime=290000,
            damage_risk_reduction=390000,
            maintenance_savings=120000,
            response_efficiency=165000,
            false_alarm_reduction=85000,
            compliance_preparedness_value=70000,
        ),
    }
