from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import logging

from app.models.ml import PredictionSource


@dataclass
class LoadedModelBundle:
    available: bool
    model: Any | None
    metadata: dict[str, Any]
    model_comparison: list[dict[str, float | str]]
    confusion_matrix: list[dict[str, int | str]]
    message: str


class FireRiskModelLoader:
    _logger = logging.getLogger("fireguard.ml")

    def __init__(
        self,
        model_path: Path | None = None,
        metadata_path: Path | None = None,
        model_comparison_path: Path | None = None,
    ) -> None:
        backend_root = Path(__file__).resolve().parents[3]
        project_root = backend_root.parent
        self._model_path = model_path or backend_root / "models" / "fire_risk_model.joblib"
        self._metadata_path = metadata_path or backend_root / "models" / "fire_risk_model_metadata.json"
        self._comparison_path = model_comparison_path or project_root / "data" / "ml" / "model_comparison.csv"
        self._bundle: LoadedModelBundle | None = None

    def load(self) -> LoadedModelBundle:
        if self._bundle is not None:
            return self._bundle

        self._logger.info("[ML] Loading model from: %s", self._model_path)
        self._logger.info("[ML] Loading metadata from: %s", self._metadata_path)

        try:
            if not self._model_path.exists() or not self._metadata_path.exists():
                message = "ML model artifact not found. Using Rule-Based fallback."
                self._logger.error("[ML] Model load FAILED: %s", message)
                self._bundle = LoadedModelBundle(
                    available=False,
                    model=None,
                    metadata={
                        "model_name": "ML Model Unavailable",
                        "model_version": "fire-risk-v1",
                        "features": [],
                        "classes": ["NORMAL", "WARNING", "CRITICAL"],
                        "random_state": 42,
                        "dataset_type": "synthetic",
                        "metrics": {},
                        "synthetic_dataset_disclaimer": (
                            "Model trained on synthetic fire-sensor data generated for academic simulation. "
                            "Results demonstrate the prototype pipeline and are not certified for real building safety deployment."
                        ),
                    },
                    model_comparison=[],
                    confusion_matrix=[],
                    message=message,
                )
                return self._bundle

            metadata = json.loads(self._metadata_path.read_text(encoding="utf-8"))
            model = joblib.load(self._model_path)
        except Exception as error:  # pragma: no cover - defensive logging for startup failures
            message = f"{type(error).__name__}: {error}"
            self._logger.exception("[ML] Model load FAILED: %s", message)
            self._bundle = LoadedModelBundle(
                available=False,
                model=None,
                metadata={
                    "model_name": "ML Model Unavailable",
                    "model_version": "fire-risk-v1",
                    "features": [],
                    "classes": ["NORMAL", "WARNING", "CRITICAL"],
                    "random_state": 42,
                    "dataset_type": "synthetic",
                    "metrics": {},
                    "synthetic_dataset_disclaimer": (
                        "Model trained on synthetic fire-sensor data generated for academic simulation. "
                        "Results demonstrate the prototype pipeline and are not certified for real building safety deployment."
                    ),
                },
                model_comparison=[],
                confusion_matrix=[],
                message=message,
            )
            return self._bundle

        comparison: list[dict[str, float | str]] = []
        if self._comparison_path.exists():
            comparison_df = pd.read_csv(self._comparison_path)
            comparison = comparison_df.to_dict(orient="records")

        confusion = metadata.get("confusion_matrix", [])
        metrics = metadata.get("metrics") or metadata.get("test_metrics", {})
        metadata["metrics"] = metrics
        metadata.setdefault("test_metrics", metrics)

        self._bundle = LoadedModelBundle(
            available=True,
            model=model,
            metadata=metadata,
            model_comparison=comparison,
            confusion_matrix=confusion,
            message="ML model loaded successfully.",
        )
        self._logger.info("[ML] Model loaded successfully")
        return self._bundle

    def model_health(self) -> dict[str, str | bool]:
        bundle = self.load()
        return {
            "loaded_successfully": bundle.available,
            "prediction_source": PredictionSource.ML_MODEL.value if bundle.available else PredictionSource.RULE_BASED_FALLBACK.value,
            "message": bundle.message,
        }
