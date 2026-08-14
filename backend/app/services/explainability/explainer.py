from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from app.ml_pipeline.training import FEATURE_COLUMNS
from app.models.common import RiskLevel
from app.models.ml import (
    ContributionDirection,
    ExplanationMethod,
    FeatureContribution,
    FeatureImportanceItem,
    FireRiskFeatureImportanceResponse,
    FireRiskPredictionRequest,
    FireRiskExplanationResponse,
    PredictionSource,
)
from app.services.explainability.feature_names import feature_label
from app.services.explainability.physical_consistency import evaluate_physical_consistency
from app.services.ml.fire_predictor import FireRiskPredictor
from app.services.ml.model_loader import FireRiskModelLoader

try:
    import shap  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    shap = None


@dataclass
class _ModelArtifacts:
    pipeline: Any
    model: Any
    preprocess: Any


class FireRiskExplainer:
    _PERTURBATION_DELTA: dict[str, float] = {
        "temperature": 5.0,
        "temperature_rate": 0.4,
        "smoke_level": 0.05,
        "co_level": 4.0,
        "co2_level": 120.0,
        "humidity": 6.0,
        "electrical_load": 5.0,
        "occupancy": 8.0,
        "hvac_running": 1.0,
        "sprinkler_active": 1.0,
    }

    def __init__(self, *, loader: FireRiskModelLoader | None = None, predictor: FireRiskPredictor | None = None) -> None:
        self._loader = loader or FireRiskModelLoader()
        self._predictor = predictor or FireRiskPredictor(loader=self._loader)
        self._tree_explainer: Any | None = None
        self._tree_explainer_model_name: str | None = None

    def _to_frame(self, request: FireRiskPredictionRequest) -> pd.DataFrame:
        return pd.DataFrame([request.model_dump()])[FEATURE_COLUMNS]

    def _build_contributors(self, request: FireRiskPredictionRequest, critical_contributions: dict[str, float]) -> tuple[list[FeatureContribution], list[FeatureContribution]]:
        positive: list[FeatureContribution] = []
        negative: list[FeatureContribution] = []

        for feature in FEATURE_COLUMNS:
            contribution = float(critical_contributions.get(feature, 0.0))
            value = float(getattr(request, feature))
            if abs(contribution) < 1e-9:
                direction = ContributionDirection.NEUTRAL
            elif contribution > 0:
                direction = ContributionDirection.INCREASES_RISK
            else:
                direction = ContributionDirection.DECREASES_RISK

            row = FeatureContribution(
                feature=feature,
                feature_label=feature_label(feature),
                value=value,
                contribution=round(contribution, 6),
                direction=direction,
            )
            if contribution > 0:
                positive.append(row)
            elif contribution < 0:
                negative.append(row)

        positive.sort(key=lambda item: item.contribution, reverse=True)
        negative.sort(key=lambda item: item.contribution)
        return positive[:6], negative[:6]

    def _model_artifacts(self) -> _ModelArtifacts | None:
        bundle = self._loader.load()
        if not bundle.available or bundle.model is None:
            return None
        pipeline = bundle.model
        model = pipeline.named_steps.get("model")
        preprocess = pipeline.named_steps.get("preprocess")
        if model is None or preprocess is None:
            return None
        return _ModelArtifacts(pipeline=pipeline, model=model, preprocess=preprocess)

    def _logistic_contributions(self, request: FireRiskPredictionRequest, artifacts: _ModelArtifacts) -> dict[str, float]:
        transformed = artifacts.preprocess.transform(self._to_frame(request))
        classes = [str(label) for label in artifacts.model.classes_]
        if RiskLevel.CRITICAL.value not in classes:
            return {feature: 0.0 for feature in FEATURE_COLUMNS}
        critical_idx = classes.index(RiskLevel.CRITICAL.value)
        coeffs = artifacts.model.coef_[critical_idx]
        contributions = np.asarray(transformed[0]).astype(float) * np.asarray(coeffs).astype(float)
        return {feature: float(value) for feature, value in zip(FEATURE_COLUMNS, contributions)}

    def _tree_shap_contributions(self, request: FireRiskPredictionRequest, artifacts: _ModelArtifacts) -> dict[str, float] | None:
        if shap is None:
            return None

        model_name = type(artifacts.model).__name__
        if self._tree_explainer is None or self._tree_explainer_model_name != model_name:
            self._tree_explainer = shap.TreeExplainer(artifacts.model)
            self._tree_explainer_model_name = model_name

        transformed = artifacts.preprocess.transform(self._to_frame(request))
        shap_values = self._tree_explainer.shap_values(transformed)
        classes = [str(label) for label in artifacts.model.classes_]
        critical_idx = classes.index(RiskLevel.CRITICAL.value) if RiskLevel.CRITICAL.value in classes else 0

        if isinstance(shap_values, list):
            values = np.asarray(shap_values[critical_idx][0], dtype=float)
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            values = np.asarray(shap_values[0, :, critical_idx], dtype=float)
        else:
            values = np.asarray(shap_values[0], dtype=float)

        return {feature: float(value) for feature, value in zip(FEATURE_COLUMNS, values)}

    def _perturbation_contributions(self, request: FireRiskPredictionRequest) -> dict[str, float]:
        baseline = self._predictor.predict(request)
        base_critical = float(baseline.probabilities.get(RiskLevel.CRITICAL, 0.0))
        contributions: dict[str, float] = {}

        for feature in FEATURE_COLUMNS:
            delta = self._PERTURBATION_DELTA[feature]
            current = float(getattr(request, feature))
            if feature in {"hvac_running", "sprinkler_active"}:
                plus_value = 1.0 if current < 0.5 else 0.0
                minus_value = current
            else:
                plus_value = current + delta
                minus_value = max(0.0, current - delta)

            plus_request = request.model_copy(update={feature: plus_value})
            minus_request = request.model_copy(update={feature: minus_value})
            plus_critical = float(self._predictor.predict(plus_request).probabilities.get(RiskLevel.CRITICAL, 0.0))
            minus_critical = float(self._predictor.predict(minus_request).probabilities.get(RiskLevel.CRITICAL, 0.0))

            centered = (plus_critical - minus_critical) * 0.5
            anchored = base_critical - minus_critical
            contributions[feature] = float((centered + anchored) * 0.5)

        return contributions

    def explain(self, request: FireRiskPredictionRequest) -> FireRiskExplanationResponse:
        prediction = self._predictor.predict(request)
        artifacts = self._model_artifacts()

        method = ExplanationMethod.PERTURBATION_FALLBACK
        contribution_map = self._perturbation_contributions(request)

        if artifacts is not None and prediction.prediction_source == PredictionSource.ML_MODEL:
            model_name = type(artifacts.model).__name__
            if "LogisticRegression" in model_name:
                method = ExplanationMethod.LOGISTIC_CONTRIBUTION
                contribution_map = self._logistic_contributions(request, artifacts)
            else:
                shap_contributions = self._tree_shap_contributions(request, artifacts)
                if shap_contributions is not None:
                    method = ExplanationMethod.SHAP
                    contribution_map = shap_contributions
                else:
                    method = ExplanationMethod.PERTURBATION_FALLBACK
                    contribution_map = self._perturbation_contributions(request)

        top_positive, top_negative = self._build_contributors(request, contribution_map)

        return FireRiskExplanationResponse(
            predicted_class=prediction.predicted_class,
            confidence=prediction.confidence,
            critical_probability=float(prediction.probabilities.get(RiskLevel.CRITICAL, 0.0)),
            model_version=prediction.model_version,
            prediction_source=prediction.prediction_source,
            explanation_method=method,
            top_positive_contributors=top_positive,
            top_negative_contributors=top_negative,
            physical_consistency=evaluate_physical_consistency(request),
            input_features=request,
            timestamp=prediction.timestamp,
        )

    def _importance_items(self, values: dict[str, float]) -> list[FeatureImportanceItem]:
        magnitudes = {feature: max(0.0, float(abs(score))) for feature, score in values.items()}
        total = sum(magnitudes.values())
        if total <= 0.0:
            total = 1.0

        rows = [
            FeatureImportanceItem(
                feature=feature,
                feature_label=feature_label(feature),
                importance=round(value, 6),
                normalized_importance=round(value / total, 6),
            )
            for feature, value in sorted(magnitudes.items(), key=lambda item: item[1], reverse=True)
        ]
        return rows

    def feature_importance(self) -> FireRiskFeatureImportanceResponse:
        bundle = self._loader.load()
        artifacts = self._model_artifacts()

        if artifacts is None:
            return FireRiskFeatureImportanceResponse(
                model_version=str(bundle.metadata.get("model_version", "fire-risk-v1")),
                prediction_source=PredictionSource.RULE_BASED_FALLBACK,
                explanation_method=ExplanationMethod.PERTURBATION_FALLBACK,
                features=self._importance_items({feature: 0.0 for feature in FEATURE_COLUMNS}),
            )

        model_name = type(artifacts.model).__name__
        method = ExplanationMethod.PERTURBATION_FALLBACK
        scores: dict[str, float]

        if "LogisticRegression" in model_name:
            classes = [str(label) for label in artifacts.model.classes_]
            critical_idx = classes.index(RiskLevel.CRITICAL.value) if RiskLevel.CRITICAL.value in classes else 0
            coeffs = np.abs(np.asarray(artifacts.model.coef_[critical_idx], dtype=float))
            scores = {feature: float(value) for feature, value in zip(FEATURE_COLUMNS, coeffs)}
            method = ExplanationMethod.LOGISTIC_CONTRIBUTION
        elif hasattr(artifacts.model, "feature_importances_"):
            importances = np.asarray(artifacts.model.feature_importances_, dtype=float)
            scores = {feature: float(value) for feature, value in zip(FEATURE_COLUMNS, importances)}
            method = ExplanationMethod.SHAP if shap is not None else ExplanationMethod.PERTURBATION_FALLBACK
        else:
            scores = {feature: 0.0 for feature in FEATURE_COLUMNS}

        return FireRiskFeatureImportanceResponse(
            model_version=str(bundle.metadata.get("model_version", "fire-risk-v1")),
            prediction_source=PredictionSource.ML_MODEL if bundle.available else PredictionSource.RULE_BASED_FALLBACK,
            explanation_method=method,
            features=self._importance_items(scores),
        )
