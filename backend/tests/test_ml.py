from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.ml import FireRiskPredictionRequest, PredictionSource
from app.services import simulation_engine
from app.services.ml.fire_predictor import FireRiskPredictor
from app.services.ml.model_loader import FireRiskModelLoader
from app.simulation.models import SimulationStartRequest

client = TestClient(app)


def setup_function() -> None:
    client.post("/api/digital-twin/reset")


def _payload(**overrides: float | int) -> dict[str, float | int]:
    payload = {
        "temperature": 74.0,
        "temperature_rate": 1.5,
        "smoke_level": 0.62,
        "co_level": 35.0,
        "co2_level": 1200.0,
        "humidity": 34.0,
        "electrical_load": 88.0,
        "occupancy": 58,
        "hvac_running": 1,
        "sprinkler_active": 0,
    }
    payload.update(overrides)
    return payload


def test_model_info_endpoint() -> None:
    response = client.get("/api/ml/fire-risk/model-info")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ONLINE"
    assert body["loaded"] is True
    assert body["prediction_source"] == "ML_MODEL"
    assert body["model_version"] == "fire-risk-v1"
    assert body["dataset_type"] == "synthetic"
    assert "synthetic" in body["synthetic_dataset_disclaimer"].lower()


def test_metrics_endpoint() -> None:
    response = client.get("/api/ml/fire-risk/metrics")
    assert response.status_code == 200
    body = response.json()
    for key in ["accuracy", "macro_f1", "critical_recall", "roc_auc"]:
        assert body[key] is not None
        assert 0 <= body[key] <= 1


def test_prediction_endpoint_accepts_valid_payload() -> None:
    response = client.post("/api/ml/fire-risk/predict", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "fire-risk-v1"
    assert body["predicted_class"] in {"NORMAL", "WARNING", "CRITICAL"}
    assert body["prediction_source"] in {"ML_MODEL", "RULE_BASED_FALLBACK"}


def test_prediction_endpoint_rejects_invalid_payload() -> None:
    response = client.post("/api/ml/fire-risk/predict", json=_payload(humidity=120))
    assert response.status_code == 422


def test_prediction_probabilities_sum_to_one() -> None:
    response = client.post("/api/ml/fire-risk/predict", json=_payload())
    body = response.json()
    total = sum(body["probabilities"].values())
    assert abs(total - 1.0) < 1e-6


def test_sanity_normal_pattern_prefers_normal() -> None:
    response = client.post(
        "/api/ml/fire-risk/predict",
        json=_payload(
            temperature=24.0,
            temperature_rate=0.04,
            smoke_level=0.02,
            co_level=4.2,
            co2_level=520.0,
            humidity=56.0,
            electrical_load=42.0,
            occupancy=64,
            hvac_running=1,
            sprinkler_active=0,
        ),
    )
    body = response.json()
    probs = body["probabilities"]
    assert probs["NORMAL"] >= probs["WARNING"]
    assert probs["NORMAL"] >= probs["CRITICAL"]


def test_sanity_warning_pattern_prefers_warning_or_critical() -> None:
    response = client.post(
        "/api/ml/fire-risk/predict",
        json=_payload(
            temperature=49.0,
            temperature_rate=0.74,
            smoke_level=0.24,
            co_level=16.0,
            co2_level=880.0,
            humidity=42.0,
            electrical_load=72.0,
            occupancy=84,
            hvac_running=1,
            sprinkler_active=0,
        ),
    )
    body = response.json()
    probs = body["probabilities"]
    assert max(probs["WARNING"], probs["CRITICAL"]) >= probs["NORMAL"]


def test_sanity_critical_pattern_prefers_critical() -> None:
    response = client.post(
        "/api/ml/fire-risk/predict",
        json=_payload(
            temperature=92.0,
            temperature_rate=2.4,
            smoke_level=0.82,
            co_level=56.0,
            co2_level=1900.0,
            humidity=29.0,
            electrical_load=94.0,
            occupancy=96,
            hvac_running=0,
            sprinkler_active=0,
        ),
    )
    body = response.json()
    probs = body["probabilities"]
    assert probs["CRITICAL"] >= probs["WARNING"]
    assert probs["CRITICAL"] >= probs["NORMAL"]


def test_fallback_when_model_is_unavailable() -> None:
    missing = Path("/tmp/nonexistent-fire-risk-model.joblib")
    missing_meta = Path("/tmp/nonexistent-fire-risk-model-metadata.json")
    predictor = FireRiskPredictor(loader=FireRiskModelLoader(model_path=missing, metadata_path=missing_meta))
    result = predictor.predict(FireRiskPredictionRequest.model_validate(_payload()))
    assert result.prediction_source == PredictionSource.RULE_BASED_FALLBACK


def test_fire_twin_receives_ml_prediction_source() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=True), run_in_background=False)
    simulation_engine.advance_seconds(20)
    fire_twin = client.get("/api/twins/fire").json()
    assert fire_twin["prediction_source"] in {"ML_MODEL", "RULE_BASED_FALLBACK"}
    assert "CRITICAL" in fire_twin["risk_probabilities"]


def test_simulation_predictions_change_over_time() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=True), run_in_background=False)
    simulation_engine.advance_seconds(10)
    early = client.get("/api/twins/fire").json()
    simulation_engine.advance_seconds(70)
    later = client.get("/api/twins/fire").json()

    early_critical = early["risk_probabilities"]["CRITICAL"]
    later_critical = later["risk_probabilities"]["CRITICAL"]
    assert abs(later_critical - early_critical) > 0.05


def test_prediction_source_exposed_in_simulation_run_summary() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=True), run_in_background=False)
    simulation_engine.advance_seconds(140)
    runs = client.get("/api/simulation/runs").json()
    assert runs
    latest = runs[-1]
    assert latest["prediction_source"] in {"ML_MODEL", "RULE_BASED_FALLBACK", "NOT_AVAILABLE"}
    assert "max_critical_probability" in latest


def test_explanation_endpoint_returns_contributors_and_consistency() -> None:
    response = client.get("/api/ml/fire-risk/explanation")
    assert response.status_code == 200
    body = response.json()

    assert body["predicted_class"] in {"NORMAL", "WARNING", "CRITICAL"}
    assert body["explanation_method"] in {"SHAP", "LOGISTIC_CONTRIBUTION", "PERTURBATION_FALLBACK"}
    assert body["physical_consistency"]["status"] in {
        "PHYSICALLY_CONSISTENT",
        "SENSOR_CONFLICT",
        "INSUFFICIENT_MULTI_SENSOR_SUPPORT",
    }
    assert isinstance(body["top_positive_contributors"], list)
    assert isinstance(body["top_negative_contributors"], list)


def test_feature_importance_endpoint_returns_ranked_features() -> None:
    response = client.get("/api/ml/fire-risk/feature-importance")
    assert response.status_code == 200
    body = response.json()
    features = body["features"]

    assert body["explanation_method"] in {"SHAP", "LOGISTIC_CONTRIBUTION", "PERTURBATION_FALLBACK"}
    assert len(features) >= 5
    assert features[0]["normalized_importance"] >= features[-1]["normalized_importance"]


def test_explain_endpoint_detects_sensor_conflict_pattern() -> None:
    response = client.post(
        "/api/ml/fire-risk/explain",
        json=_payload(
            temperature=86.0,
            temperature_rate=0.1,
            smoke_level=0.03,
            co_level=3.0,
            co2_level=550.0,
            humidity=48.0,
            electrical_load=44.0,
            occupancy=40,
            hvac_running=1,
            sprinkler_active=0,
        ),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["physical_consistency"]["status"] == "SENSOR_CONFLICT"


def test_explain_endpoint_changes_critical_probability_for_higher_risk_input() -> None:
    low = client.post(
        "/api/ml/fire-risk/explain",
        json=_payload(
            temperature=26.0,
            temperature_rate=0.05,
            smoke_level=0.02,
            co_level=4.0,
            co2_level=520.0,
            humidity=54.0,
            electrical_load=40.0,
            occupancy=50,
            hvac_running=1,
            sprinkler_active=0,
        ),
    ).json()

    high = client.post(
        "/api/ml/fire-risk/explain",
        json=_payload(
            temperature=95.0,
            temperature_rate=2.6,
            smoke_level=0.86,
            co_level=58.0,
            co2_level=1900.0,
            humidity=30.0,
            electrical_load=95.0,
            occupancy=96,
            hvac_running=0,
            sprinkler_active=0,
        ),
    ).json()

    assert high["critical_probability"] > low["critical_probability"]
