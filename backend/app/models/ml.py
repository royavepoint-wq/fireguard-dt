from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator

from app.models.common import APIModel, RiskLevel, utc_now


class PredictionSource(StrEnum):
    ML_MODEL = "ML_MODEL"
    RULE_BASED_FALLBACK = "RULE_BASED_FALLBACK"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ExplanationMethod(StrEnum):
    SHAP = "SHAP"
    LOGISTIC_CONTRIBUTION = "LOGISTIC_CONTRIBUTION"
    PERTURBATION_FALLBACK = "PERTURBATION_FALLBACK"


class ContributionDirection(StrEnum):
    INCREASES_RISK = "increases_risk"
    DECREASES_RISK = "decreases_risk"
    NEUTRAL = "neutral"


class PhysicalConsistencyStatus(StrEnum):
    PHYSICALLY_CONSISTENT = "PHYSICALLY_CONSISTENT"
    SENSOR_CONFLICT = "SENSOR_CONFLICT"
    INSUFFICIENT_MULTI_SENSOR_SUPPORT = "INSUFFICIENT_MULTI_SENSOR_SUPPORT"


class FireRiskPredictionRequest(APIModel):
    temperature: float
    temperature_rate: float
    smoke_level: float
    co_level: float
    co2_level: float
    humidity: float
    electrical_load: float
    occupancy: float
    hvac_running: int
    sprinkler_active: int

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

    @field_validator("occupancy")
    @classmethod
    def validate_occupancy(cls, value: float) -> float:
        if value < 0:
            raise ValueError("occupancy must be non-negative")
        return value

    @field_validator("temperature_rate", "smoke_level", "co_level", "co2_level", "electrical_load")
    @classmethod
    def validate_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("sensor values must be non-negative")
        return value

    @field_validator("hvac_running", "sprinkler_active")
    @classmethod
    def validate_binary(cls, value: int) -> int:
        if value not in {0, 1}:
            raise ValueError("binary fields must be 0 or 1")
        return value


class FireRiskPredictionResponse(APIModel):
    model_name: str
    model_version: str
    predicted_class: RiskLevel
    confidence: float
    probabilities: dict[RiskLevel, float]
    input_features: FireRiskPredictionRequest
    prediction_source: PredictionSource
    timestamp: datetime = Field(default_factory=utc_now)


class FireRiskModelInfoResponse(APIModel):
    status: str
    model_version: str
    model_name: str
    loaded_successfully: bool
    loaded: bool
    prediction_source: PredictionSource
    features: list[str]
    classes: list[str]
    random_state: int
    dataset_type: str
    synthetic_dataset_disclaimer: str
    error: str | None = None
    evaluation_metrics: dict[str, float]
    model_comparison: list[dict[str, float | str]] = Field(default_factory=list)
    confusion_matrix: list[dict[str, int | str]] = Field(default_factory=list)


class FireRiskMetricsResponse(APIModel):
    selected_model: str
    model_version: str
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    roc_auc: float
    critical_precision: float
    critical_recall: float
    critical_f1: float


class FeatureContribution(APIModel):
    feature: str
    feature_label: str
    value: float
    contribution: float
    direction: ContributionDirection


class PhysicalConsistencyResult(APIModel):
    status: PhysicalConsistencyStatus
    message: str
    checks: dict[str, bool] = Field(default_factory=dict)


class FireRiskExplanationResponse(APIModel):
    predicted_class: RiskLevel
    confidence: float
    critical_probability: float
    model_version: str
    prediction_source: PredictionSource
    explanation_method: ExplanationMethod
    top_positive_contributors: list[FeatureContribution] = Field(default_factory=list)
    top_negative_contributors: list[FeatureContribution] = Field(default_factory=list)
    physical_consistency: PhysicalConsistencyResult
    input_features: FireRiskPredictionRequest
    timestamp: datetime = Field(default_factory=utc_now)


class FeatureImportanceItem(APIModel):
    feature: str
    feature_label: str
    importance: float
    normalized_importance: float


class FireRiskFeatureImportanceResponse(APIModel):
    model_version: str
    prediction_source: PredictionSource
    explanation_method: ExplanationMethod
    features: list[FeatureImportanceItem] = Field(default_factory=list)
