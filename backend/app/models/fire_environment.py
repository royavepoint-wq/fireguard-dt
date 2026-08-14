from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.common import APIModel, RiskLevel, SensorHealth, TwinStatus, utc_now
from app.models.ml import PredictionSource


class FireEnvironmentTwinState(APIModel):
    twin_id: str = "fire_environment"
    name: str = "Fire & Environment Twin"
    status: TwinStatus = TwinStatus.ONLINE
    last_updated: datetime = Field(default_factory=utc_now)

    building_id: str = "FG-BLDG-01"
    floor_id: str = "floor-1"
    zone_id: str = "room-electrical-01"

    temperature: float = 24.6
    temperature_rate: float = 0.0
    smoke_level: float = 0.02
    co_level: float = 4.0
    co2_level: float = 450.0
    humidity: float = 55.0
    electrical_load: float = 42.0

    fire_risk_probability: float = 0.08
    risk_level: RiskLevel = RiskLevel.NORMAL
    risk_probabilities: dict[RiskLevel, float] = Field(
        default_factory=lambda: {
            RiskLevel.NORMAL: 0.88,
            RiskLevel.WARNING: 0.08,
            RiskLevel.CRITICAL: 0.04,
        }
    )
    prediction_source: PredictionSource = PredictionSource.NOT_AVAILABLE
    model_version: str | None = None
    prediction_confidence: float = 0.0

    sensor_health: SensorHealth = SensorHealth.HEALTHY
    hvac_effect: float = 0.15

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        if not -40.0 <= value <= 200.0:
            raise ValueError("temperature must be between -40 and 200")
        return value

    @field_validator("humidity")
    @classmethod
    def validate_humidity(cls, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            raise ValueError("humidity must be between 0 and 100")
        return value

    @field_validator(
        "temperature_rate",
        "smoke_level",
        "co_level",
        "co2_level",
        "electrical_load",
    )
    @classmethod
    def validate_non_negative_metrics(cls, value: float) -> float:
        if value < 0.0:
            raise ValueError("metric values must be non-negative")
        return value

    @field_validator("fire_risk_probability")
    @classmethod
    def validate_probability(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("fire_risk_probability must be between 0 and 1")
        return value

    @field_validator("prediction_confidence")
    @classmethod
    def validate_prediction_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("prediction_confidence must be between 0 and 1")
        return value

    @field_validator("risk_probabilities")
    @classmethod
    def validate_probabilities(cls, value: dict[RiskLevel, float]) -> dict[RiskLevel, float]:
        total = float(sum(value.values()))
        if total <= 0:
            raise ValueError("risk_probabilities must contain a positive total")
        if abs(total - 1.0) > 1e-3:
            raise ValueError("risk_probabilities must sum to 1")
        return value

    @field_validator("hvac_effect")
    @classmethod
    def validate_hvac_effect(cls, value: float) -> float:
        if not -1.0 <= value <= 1.0:
            raise ValueError("hvac_effect must be between -1 and 1")
        return value


class FireEnvironmentTwinUpdate(APIModel):
    name: str | None = None
    status: TwinStatus | None = None
    building_id: str | None = None
    floor_id: str | None = None
    zone_id: str | None = None
    temperature: float | None = None
    temperature_rate: float | None = None
    smoke_level: float | None = None
    co_level: float | None = None
    co2_level: float | None = None
    humidity: float | None = None
    electrical_load: float | None = None
    fire_risk_probability: float | None = None
    risk_level: RiskLevel | None = None
    risk_probabilities: dict[RiskLevel, float] | None = None
    prediction_source: PredictionSource | None = None
    model_version: str | None = None
    prediction_confidence: float | None = None
    sensor_health: SensorHealth | None = None
    hvac_effect: float | None = None


def build_default_fire_environment_state() -> FireEnvironmentTwinState:
    return FireEnvironmentTwinState()