from __future__ import annotations

from app.models.ml import FireRiskPredictionRequest, PhysicalConsistencyResult, PhysicalConsistencyStatus


def evaluate_physical_consistency(request: FireRiskPredictionRequest) -> PhysicalConsistencyResult:
    high_temperature = request.temperature >= 75.0
    rising_temperature = request.temperature_rate >= 0.9
    smoke_elevated = request.smoke_level >= 0.22
    co_elevated = request.co_level >= 18.0
    co2_elevated = request.co2_level >= 900.0
    electrical_only = request.electrical_load >= 85.0 and not smoke_elevated and not co_elevated and not high_temperature

    checks = {
        "high_temperature": high_temperature,
        "rising_temperature": rising_temperature,
        "smoke_elevated": smoke_elevated,
        "co_elevated": co_elevated,
        "co2_elevated": co2_elevated,
    }

    evidence_count = sum(1 for value in (high_temperature, rising_temperature, smoke_elevated, co_elevated, co2_elevated) if value)

    if high_temperature and not smoke_elevated and not co_elevated and not rising_temperature:
        return PhysicalConsistencyResult(
            status=PhysicalConsistencyStatus.SENSOR_CONFLICT,
            message="High temperature is not supported by smoke or CO signals. Manual verification recommended.",
            checks=checks,
        )

    if electrical_only or evidence_count <= 1:
        return PhysicalConsistencyResult(
            status=PhysicalConsistencyStatus.INSUFFICIENT_MULTI_SENSOR_SUPPORT,
            message="Risk signal has limited multi-sensor support. Treat as early warning and validate nearby sensors.",
            checks=checks,
        )

    return PhysicalConsistencyResult(
        status=PhysicalConsistencyStatus.PHYSICALLY_CONSISTENT,
        message="Multi-sensor evidence is physically consistent with the predicted fire-risk state.",
        checks=checks,
    )
