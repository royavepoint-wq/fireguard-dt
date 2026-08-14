from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.models.common import RiskLevel
from app.models.ml import (
    FireRiskModelInfoResponse,
    FireRiskMetricsResponse,
    FireRiskPredictionRequest,
    FireRiskPredictionResponse,
    PredictionSource,
)
from app.services.ml.model_loader import FireRiskModelLoader


@dataclass
class PredictionThresholds:
    warning_confidence_threshold: float = 0.50
    critical_confidence_threshold: float = 0.60


class FireRiskPredictor:
    def __init__(self, loader: FireRiskModelLoader | None = None) -> None:
        self._loader = loader or FireRiskModelLoader()
        self._thresholds = PredictionThresholds()

    def _to_frame(self, request: FireRiskPredictionRequest) -> pd.DataFrame:
        return pd.DataFrame([request.model_dump()])

    def _rule_based_fallback(self, request: FireRiskPredictionRequest) -> tuple[dict[RiskLevel, float], RiskLevel]:
        score = (
            0.22 * min(1.0, request.temperature / 95.0)
            + 0.18 * min(1.0, request.temperature_rate / 2.5)
            + 0.20 * min(1.0, request.smoke_level / 0.8)
            + 0.16 * min(1.0, request.co_level / 45.0)
            + 0.08 * min(1.0, request.co2_level / 1800.0)
            + 0.06 * min(1.0, request.electrical_load / 95.0)
            + 0.05 * (1.0 if request.hvac_running == 0 else 0.0)
            + 0.05 * (1.0 if request.sprinkler_active == 0 else 0.0)
        )

        critical = float(np.clip(score, 0.0, 1.0))
        warning = float(np.clip(0.15 + 0.7 * critical * (1.0 - critical), 0.0, 1.0))
        normal = max(0.0, 1.0 - critical - 0.55 * warning)

        total = normal + warning + critical
        probs = {
            RiskLevel.NORMAL: normal / total,
            RiskLevel.WARNING: warning / total,
            RiskLevel.CRITICAL: critical / total,
        }

        predicted = max(probs, key=probs.get)
        return probs, predicted

    def predict(self, request: FireRiskPredictionRequest) -> FireRiskPredictionResponse:
        bundle = self._loader.load()

        if not bundle.available or bundle.model is None:
            fallback_probs, fallback_class = self._rule_based_fallback(request)
            confidence = float(fallback_probs[fallback_class])
            return FireRiskPredictionResponse(
                model_name="RuleBasedFallback",
                model_version=str(bundle.metadata.get("model_version", "fire-risk-v1")),
                predicted_class=fallback_class,
                confidence=confidence,
                probabilities=fallback_probs,
                input_features=request,
                prediction_source=PredictionSource.RULE_BASED_FALLBACK,
            )

        frame = self._to_frame(request)
        classes: list[str] = list(bundle.model.classes_)
        probabilities = bundle.model.predict_proba(frame)[0]
        class_probability = {RiskLevel(label): float(prob) for label, prob in zip(classes, probabilities)}

        predicted_label = max(class_probability, key=class_probability.get)
        confidence = float(class_probability[predicted_label])

        if predicted_label == RiskLevel.CRITICAL and confidence < self._thresholds.critical_confidence_threshold:
            predicted_label = RiskLevel.WARNING
            confidence = float(class_probability[RiskLevel.WARNING])
        elif predicted_label == RiskLevel.WARNING and confidence < self._thresholds.warning_confidence_threshold:
            predicted_label = RiskLevel.NORMAL
            confidence = float(class_probability[RiskLevel.NORMAL])

        return FireRiskPredictionResponse(
            model_name=str(bundle.metadata.get("model_name", "UnknownModel")),
            model_version=str(bundle.metadata.get("model_version", "fire-risk-v1")),
            predicted_class=predicted_label,
            confidence=confidence,
            probabilities=class_probability,
            input_features=request,
            prediction_source=PredictionSource.ML_MODEL,
        )

    def model_info(self) -> FireRiskModelInfoResponse:
        bundle = self._loader.load()
        source = PredictionSource.ML_MODEL if bundle.available else PredictionSource.RULE_BASED_FALLBACK
        metrics = bundle.metadata.get("metrics") or bundle.metadata.get("test_metrics", {})
        status = "ONLINE" if bundle.available else "FALLBACK"
        error = None if bundle.available else bundle.message
        return FireRiskModelInfoResponse(
            status=status,
            model_version=str(bundle.metadata.get("model_version", "fire-risk-v1")),
            model_name=str(bundle.metadata.get("model_name", "RuleBasedFallback")),
            loaded_successfully=bundle.available,
            loaded=bundle.available,
            prediction_source=source,
            features=list(bundle.metadata.get("features", [])),
            classes=list(bundle.metadata.get("classes", ["NORMAL", "WARNING", "CRITICAL"])),
            random_state=int(bundle.metadata.get("random_state", 42)),
            dataset_type=str(bundle.metadata.get("dataset_type", "synthetic")),
            synthetic_dataset_disclaimer=str(bundle.metadata.get("synthetic_dataset_disclaimer", "Synthetic Training Dataset")),
            error=error,
            evaluation_metrics={
                metric: float(value)
                for metric, value in dict(metrics).items()
                if isinstance(value, (int, float))
            },
            model_comparison=bundle.model_comparison,
            confusion_matrix=bundle.confusion_matrix,
        )

    def metrics(self) -> FireRiskMetricsResponse:
        info = self.model_info()
        metrics = info.evaluation_metrics
        return FireRiskMetricsResponse(
            selected_model=info.model_name,
            model_version=info.model_version,
            accuracy=float(metrics.get("accuracy", 0.0)) if metrics else 0.0,
            macro_precision=float(metrics.get("macro_precision", 0.0)) if metrics else 0.0,
            macro_recall=float(metrics.get("macro_recall", 0.0)) if metrics else 0.0,
            macro_f1=float(metrics.get("macro_f1", 0.0)) if metrics else 0.0,
            weighted_f1=float(metrics.get("weighted_f1", 0.0)) if metrics else 0.0,
            roc_auc=float(metrics.get("roc_auc", 0.0)) if metrics else 0.0,
            critical_precision=float(metrics.get("critical_precision", 0.0)) if metrics else 0.0,
            critical_recall=float(metrics.get("critical_recall", 0.0)) if metrics else 0.0,
            critical_f1=float(metrics.get("critical_f1", 0.0)) if metrics else 0.0,
        )
