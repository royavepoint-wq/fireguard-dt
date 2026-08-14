# Predictive Intelligence (Step 5)

## Scope

Step 5 introduces a real trained machine learning pipeline and live inference integration for FireGuard DT.

Primary prediction task:
- Fire Risk Classification
- Classes: `NORMAL`, `WARNING`, `CRITICAL`

Outputs:
- predicted class
- class probabilities
- confidence
- prediction source (`ML_MODEL`, `RULE_BASED_FALLBACK`, `NOT_AVAILABLE`)

## End-to-End Flow

```text
Synthetic Sensor Dataset
        ↓
Preprocessing
        ↓
Candidate Models
        ↓
Validation / Selection
        ↓
Selected Model Artifact
        ↓
FastAPI ML Service
        ↓
Fire Twin
        ↓
Orchestrator
        ↓
3D / Command Center
```

## Synthetic Training Dataset

Dataset type:
- Synthetic Training Dataset

Location:
- `data/ml/fire_sensor_dataset.csv`

Generation characteristics:
- physically plausible multi-sensor patterns
- overlapping feature distributions
- sensor noise and inconsistencies
- occasional elevated temperature without fire
- smoke noise and electrical-load spikes

Feature columns:
- `temperature`
- `temperature_rate`
- `smoke_level`
- `co_level`
- `co2_level`
- `humidity`
- `electrical_load`
- `occupancy`
- `hvac_running`
- `sprinkler_active`

Target column:
- `risk_class` (`NORMAL`, `WARNING`, `CRITICAL`)

Reproducibility:
- fixed random seed: `42`

Train/validation/test:
- stratified `70 / 15 / 15`

## Candidate Models

Implemented:
- Logistic Regression
- Random Forest Classifier
- Gradient Boosting Classifier

Preprocessing:
- scikit-learn `Pipeline`
- `ColumnTransformer`
- imputation for all models
- scaling for Logistic Regression

Model selection priority:
1. Critical Recall
2. Critical F1
3. Macro F1
4. ROC-AUC
5. Accuracy

## Evaluation Artifacts

Generated files:
- `data/ml/model_comparison.csv`
- `data/ml/confusion_matrix.csv`
- `data/ml/classification_report.csv`
- `data/ml/feature_importance.csv`
- `data/ml/slide_metrics.json`

Model artifacts:
- `backend/models/fire_risk_model.joblib`
- `backend/models/fire_risk_model_metadata.json`

Metadata includes:
- model name/version
- classes and features
- random seed
- split sizes
- test metrics
- critical metrics
- class distribution
- dataset type/disclaimer

## Backend ML Service

API endpoints:
- `POST /api/ml/fire-risk/predict`
- `GET /api/ml/fire-risk/model-info`
- `GET /api/ml/fire-risk/metrics`

Service modules:
- `backend/app/services/ml/model_loader.py`
- `backend/app/services/ml/fire_predictor.py`

Behavior:
- model loaded once via singleton loader
- if model unavailable, fallback to deterministic rule-based scoring
- fallback state is explicit (not hidden)

## Twin + Simulation Integration

Simulation sensor profiles remain deterministic for scenario control.

Risk determination path:
- sensor values
- ML predictor
- Fire Twin risk state
- orchestrator alerts
- 3D hazard overlays / command center panels

Stored Fire Twin fields:
- `fire_risk_probability` (critical probability)
- `risk_probabilities`
- `risk_level`
- `prediction_source`
- `model_version`
- `prediction_confidence`

Stored Simulation run summary fields:
- `model_version`
- `prediction_source`
- `max_critical_probability`
- `first_warning_prediction_time`
- `first_critical_prediction_time`

## Safety Layer Separation

Step 5 keeps a separation between:
- simulation phase timeline (deterministic scenario lifecycle)
- ML risk prediction (sensor-driven classifier output)

ML prediction informs orchestration but does not directly perform safety-critical autonomous actions.

## Limitations

- Synthetic dataset only
- Not safety-certified
- Simplified assumptions
- No real sensor calibration
- No real building fire-validation dataset
- Academic prototype only
