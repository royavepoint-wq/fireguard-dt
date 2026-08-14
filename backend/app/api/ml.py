from __future__ import annotations

from fastapi import APIRouter

from app.models.ml import (
    FireRiskExplanationResponse,
    FireRiskFeatureImportanceResponse,
    FireRiskMetricsResponse,
    FireRiskModelInfoResponse,
    FireRiskPredictionRequest,
    FireRiskPredictionResponse,
)
from app.services import (
    building_twin_service,
    fire_risk_explainer,
    fire_risk_predictor,
    fire_twin_service,
    occupancy_twin_service,
)

router = APIRouter(prefix="/api/ml")


def _current_fire_risk_request() -> FireRiskPredictionRequest:
    fire = fire_twin_service.get_state()
    building = building_twin_service.get_state()
    occupancy = occupancy_twin_service.get_state()
    hvac_zone_3 = next((zone for zone in building.hvac_zones if zone.hvac_zone_id == "hvac-zone-3"), None)
    sprinkler_active = 1 if any(item.is_active for item in building.sprinklers) else 0
    return FireRiskPredictionRequest(
        temperature=fire.temperature,
        temperature_rate=fire.temperature_rate,
        smoke_level=fire.smoke_level,
        co_level=fire.co_level,
        co2_level=fire.co2_level,
        humidity=fire.humidity,
        electrical_load=fire.electrical_load,
        occupancy=float(occupancy.total_occupancy),
        hvac_running=0 if hvac_zone_3 is not None and hvac_zone_3.status == "ISOLATED" else 1,
        sprinkler_active=sprinkler_active,
    )


@router.post("/fire-risk/predict", response_model=FireRiskPredictionResponse)
def predict_fire_risk(request: FireRiskPredictionRequest) -> FireRiskPredictionResponse:
    return fire_risk_predictor.predict(request)


@router.get("/fire-risk/model-info", response_model=FireRiskModelInfoResponse)
def get_fire_risk_model_info() -> FireRiskModelInfoResponse:
    return fire_risk_predictor.model_info()


@router.get("/fire-risk/metrics", response_model=FireRiskMetricsResponse)
def get_fire_risk_metrics() -> FireRiskMetricsResponse:
    return fire_risk_predictor.metrics()


@router.get("/fire-risk/explanation", response_model=FireRiskExplanationResponse)
def get_fire_risk_explanation() -> FireRiskExplanationResponse:
    return fire_risk_explainer.explain(_current_fire_risk_request())


@router.post("/fire-risk/explain", response_model=FireRiskExplanationResponse)
def explain_fire_risk_request(request: FireRiskPredictionRequest) -> FireRiskExplanationResponse:
    return fire_risk_explainer.explain(request)


@router.get("/fire-risk/feature-importance", response_model=FireRiskFeatureImportanceResponse)
def get_fire_risk_feature_importance() -> FireRiskFeatureImportanceResponse:
    return fire_risk_explainer.feature_importance()
