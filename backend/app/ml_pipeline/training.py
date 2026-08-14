from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelBinarizer, StandardScaler

from app.ml_pipeline.synthetic_data import RANDOM_STATE, TRAINING_ROWS, generate_synthetic_fire_dataset

FEATURE_COLUMNS = [
    "temperature",
    "temperature_rate",
    "smoke_level",
    "co_level",
    "co2_level",
    "humidity",
    "electrical_load",
    "occupancy",
    "hvac_running",
    "sprinkler_active",
]

CLASS_ORDER = ["NORMAL", "WARNING", "CRITICAL"]
MODEL_VERSION = "fire-risk-v1"

SYNTHETIC_DISCLAIMER = (
    "Model trained on synthetic fire-sensor data generated for academic simulation. "
    "Results demonstrate the prototype pipeline and are not certified for real building safety deployment."
)


@dataclass
class EvaluatedModel:
    model_name: str
    pipeline: Pipeline
    metrics: dict[str, float]
    confusion: np.ndarray
    classification_report_df: pd.DataFrame


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _build_logistic_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                FEATURE_COLUMNS,
            )
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                LogisticRegression(
                    max_iter=600,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                    solver="lbfgs",
                    C=0.6,
                ),
            ),
        ]
    )


def _build_rf_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                FEATURE_COLUMNS,
            )
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=320,
                    max_depth=14,
                    min_samples_split=6,
                    class_weight="balanced_subsample",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def _build_gb_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                FEATURE_COLUMNS,
            )
        ]
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                GradientBoostingClassifier(
                    n_estimators=240,
                    learning_rate=0.07,
                    max_depth=3,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _evaluate_model(model_name: str, pipeline: Pipeline, x_train: pd.DataFrame, y_train: pd.Series, x_test: pd.DataFrame, y_test: pd.Series) -> EvaluatedModel:
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)
    y_proba = pipeline.predict_proba(x_test)

    lb = LabelBinarizer()
    lb.fit(CLASS_ORDER)
    y_test_bin = lb.transform(y_test)

    accuracy = accuracy_score(y_test, y_pred)
    macro_precision = precision_score(y_test, y_pred, average="macro", zero_division=0)
    macro_recall = recall_score(y_test, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    critical_precision, critical_recall, critical_f1, _support = precision_recall_fscore_support(
        y_test,
        y_pred,
        labels=["CRITICAL"],
        zero_division=0,
    )

    roc_auc = roc_auc_score(y_test_bin, y_proba, multi_class="ovr", average="macro")

    report_df = pd.DataFrame(classification_report(y_test, y_pred, labels=CLASS_ORDER, output_dict=True, zero_division=0)).transpose()
    confusion = confusion_matrix(y_test, y_pred, labels=CLASS_ORDER)

    return EvaluatedModel(
        model_name=model_name,
        pipeline=pipeline,
        confusion=confusion,
        classification_report_df=report_df,
        metrics={
            "accuracy": float(accuracy),
            "macro_precision": float(macro_precision),
            "macro_recall": float(macro_recall),
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1),
            "roc_auc": float(roc_auc),
            "critical_precision": float(critical_precision[0]),
            "critical_recall": float(critical_recall[0]),
            "critical_f1": float(critical_f1[0]),
        },
    )


def _select_model(candidates: list[EvaluatedModel]) -> EvaluatedModel:
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.metrics["critical_recall"],
            candidate.metrics["critical_f1"],
            candidate.metrics["macro_f1"],
            candidate.metrics["roc_auc"],
            candidate.metrics["accuracy"],
        ),
        reverse=True,
    )[0]


def build_training_artifacts(output_root: Path | None = None, rows: int = TRAINING_ROWS) -> dict[str, Any]:
    root = output_root or _project_root()
    data_dir = root / "data" / "ml"
    model_dir = root / "backend" / "models"
    data_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    dataset = generate_synthetic_fire_dataset(rows=rows, random_state=RANDOM_STATE)
    dataset_path = data_dir / "fire_sensor_dataset.csv"
    dataset.to_csv(dataset_path, index=False)

    x = dataset[FEATURE_COLUMNS]
    y = dataset["risk_class"]

    x_train, x_temp, y_train, y_temp = train_test_split(
        x,
        y,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=y_temp,
    )

    candidates = [
        _evaluate_model("Logistic Regression", _build_logistic_pipeline(), x_train, y_train, x_test, y_test),
        _evaluate_model("Random Forest Classifier", _build_rf_pipeline(), x_train, y_train, x_test, y_test),
        _evaluate_model("Gradient Boosting Classifier", _build_gb_pipeline(), x_train, y_train, x_test, y_test),
    ]

    model_comparison = pd.DataFrame(
        [
            {
                "Model": candidate.model_name,
                "Accuracy": round(candidate.metrics["accuracy"], 6),
                "Macro Precision": round(candidate.metrics["macro_precision"], 6),
                "Macro Recall": round(candidate.metrics["macro_recall"], 6),
                "Macro F1": round(candidate.metrics["macro_f1"], 6),
                "Weighted F1": round(candidate.metrics["weighted_f1"], 6),
                "ROC-AUC": round(candidate.metrics["roc_auc"], 6),
                "Critical Precision": round(candidate.metrics["critical_precision"], 6),
                "Critical Recall": round(candidate.metrics["critical_recall"], 6),
                "Critical F1": round(candidate.metrics["critical_f1"], 6),
            }
            for candidate in candidates
        ]
    )

    model_comparison_path = data_dir / "model_comparison.csv"
    model_comparison.to_csv(model_comparison_path, index=False)

    selected = _select_model(candidates)
    selected_model_path = model_dir / "fire_risk_model.joblib"
    joblib.dump(selected.pipeline, selected_model_path)

    confusion_df = pd.DataFrame(selected.confusion, index=CLASS_ORDER, columns=CLASS_ORDER)
    confusion_path = data_dir / "confusion_matrix.csv"
    confusion_df.to_csv(confusion_path)

    report_path = data_dir / "classification_report.csv"
    selected.classification_report_df.to_csv(report_path)

    feature_importance_path = data_dir / "feature_importance.csv"
    estimator = selected.pipeline.named_steps["model"]
    if hasattr(estimator, "feature_importances_"):
        importances = pd.DataFrame(
            {
                "feature": FEATURE_COLUMNS,
                "importance": estimator.feature_importances_,
            }
        ).sort_values("importance", ascending=False)
    else:
        coefs = np.abs(estimator.coef_).mean(axis=0)
        importances = pd.DataFrame(
            {
                "feature": FEATURE_COLUMNS,
                "importance": coefs,
            }
        ).sort_values("importance", ascending=False)
    importances.to_csv(feature_importance_path, index=False)

    class_distribution = dataset["risk_class"].value_counts(normalize=True).sort_index()

    metadata = {
        "model_name": selected.model_name,
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": int(len(x_train)),
        "validation_rows": int(len(x_val)),
        "test_rows": int(len(x_test)),
        "features": FEATURE_COLUMNS,
        "classes": CLASS_ORDER,
        "metrics": {key: round(value, 6) for key, value in selected.metrics.items()},
        "test_metrics": {key: round(value, 6) for key, value in selected.metrics.items()},
        "critical_recall": round(selected.metrics["critical_recall"], 6),
        "critical_f1": round(selected.metrics["critical_f1"], 6),
        "random_state": RANDOM_STATE,
        "dataset_type": "synthetic",
        "synthetic_dataset_disclaimer": SYNTHETIC_DISCLAIMER,
        "selection_rule": [
            "critical_recall",
            "critical_f1",
            "macro_f1",
            "roc_auc",
            "accuracy",
        ],
        "class_distribution": {label: round(float(class_distribution.get(label, 0.0)), 6) for label in CLASS_ORDER},
        "split": {
            "train": 0.70,
            "validation": 0.15,
            "test": 0.15,
        },
        "confusion_matrix": [
            {
                "actual": actual,
                "NORMAL": int(confusion_df.loc[actual, "NORMAL"]),
                "WARNING": int(confusion_df.loc[actual, "WARNING"]),
                "CRITICAL": int(confusion_df.loc[actual, "CRITICAL"]),
            }
            for actual in CLASS_ORDER
        ],
        "model_health": {
            "loaded_successfully": True,
            "prediction_source": "ML_MODEL",
        },
    }

    metadata_path = model_dir / "fire_risk_model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    slide_metrics = {
        "selected_model": selected.model_name,
        "accuracy": round(selected.metrics["accuracy"], 6),
        "precision": round(selected.metrics["macro_precision"], 6),
        "recall": round(selected.metrics["macro_recall"], 6),
        "f1": round(selected.metrics["macro_f1"], 6),
        "roc_auc": round(selected.metrics["roc_auc"], 6),
        "critical_recall": round(selected.metrics["critical_recall"], 6),
        "critical_f1": round(selected.metrics["critical_f1"], 6),
    }
    slide_metrics_path = data_dir / "slide_metrics.json"
    slide_metrics_path.write_text(json.dumps(slide_metrics, indent=2), encoding="utf-8")

    return {
        "dataset_path": str(dataset_path),
        "model_path": str(selected_model_path),
        "metadata_path": str(metadata_path),
        "model_comparison_path": str(model_comparison_path),
        "confusion_matrix_path": str(confusion_path),
        "classification_report_path": str(report_path),
        "feature_importance_path": str(feature_importance_path),
        "slide_metrics_path": str(slide_metrics_path),
        "class_distribution": metadata["class_distribution"],
        "selected_model": selected.model_name,
        "metrics": metadata["test_metrics"],
    }
