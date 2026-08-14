# Explainable AI Architecture (Step 6)

Step 6 adds an explicit trust layer above the Step 5 fire-risk classifier.

## Objectives

- Explain each live risk prediction in human-readable terms.
- Provide both local (per-incident) and global (model-level) explanations.
- Add deterministic physical consistency checks to reduce blind trust in model outputs.
- Keep explainability in the service layer, not embedded in API handlers.

## Components

- `backend/app/services/explainability/explainer.py`
- `backend/app/services/explainability/physical_consistency.py`
- `backend/app/services/explainability/feature_names.py`
- `backend/app/api/ml.py` Step 6 endpoints

## Endpoint Surface

- `GET /api/ml/fire-risk/explanation`
- `POST /api/ml/fire-risk/explain`
- `GET /api/ml/fire-risk/feature-importance`

## Local Explanation Flow

1. Build current feature vector from Fire, Building, and Occupancy twins.
2. Run prediction through the Step 5 predictor.
3. Select explanation method:
   - Logistic contribution for logistic models.
   - SHAP for tree-based models when available.
   - Perturbation fallback otherwise.
4. Return top positive and negative contributors to critical-risk probability.
5. Attach physical consistency result.

## Physical Consistency Rules

Rules are deterministic and intentionally conservative.

- `SENSOR_CONFLICT`: high temperature without supporting smoke/CO/rise evidence.
- `INSUFFICIENT_MULTI_SENSOR_SUPPORT`: weak multi-sensor evidence or electrical-only signal.
- `PHYSICALLY_CONSISTENT`: two or more corroborating indicators.

This check does not replace prediction; it annotates trustworthiness.

## Global Importance

Global importance returns ranked feature importances normalized to sum to 1.0.

- Logistic models use absolute critical-class coefficients.
- Tree models use model feature importances and expose SHAP method label when available.
- Fallback mode returns zeroed importances with transparent method metadata.

## Frontend Consumption

`frontend/app/explainability/page.tsx` polls live explanation and importance data and renders:

- predicted class, confidence, and critical probability
- local contributor bars with direction
- physical consistency status and checks
- global feature ranking
- live input trace

## Boundaries

Still excluded from Step 6:

- deep learning explainers
- LLM-generated narratives
- external explanation stores or governance databases
- certified safety interpretation for real deployment
