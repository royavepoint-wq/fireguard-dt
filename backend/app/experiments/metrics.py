from __future__ import annotations

from app.experiments.models import ExperimentResultRecord


def congestion_level_to_value(label: str | None) -> float:
    if label == "HIGH":
        return 1.55
    if label == "MODERATE":
        return 1.25
    if label == "LOW":
        return 1.0
    return 0.0


def route_peak_congestion(route_metrics: dict[str, object] | None, fallback_level: str | None) -> float | None:
    if route_metrics is None:
        return congestion_level_to_value(fallback_level) if fallback_level else None
    value = route_metrics.get("peak_route_congestion")
    if isinstance(value, (int, float)):
        return float(value)
    return congestion_level_to_value(fallback_level) if fallback_level else None


def estimated_evacuation_time(
    *,
    route_metrics: dict[str, object] | None,
    baseline_completion_window: float | None,
    baseline_route_seconds: float | None,
) -> float | None:
    if baseline_completion_window is None:
        return None
    if route_metrics is None:
        return baseline_completion_window

    route_seconds = route_metrics.get("estimated_time_seconds")
    if not isinstance(route_seconds, (int, float)):
        return baseline_completion_window

    if baseline_route_seconds is None or baseline_route_seconds <= 0:
        return round(float(baseline_completion_window), 3)

    multiplier = float(route_seconds) / float(baseline_route_seconds)
    return round(float(baseline_completion_window) * max(0.25, multiplier), 3)


def hazard_exposure_metric(
    *,
    occupants_at_risk: int,
    route_metrics: dict[str, object] | None,
    evacuation_time_seconds: float | None,
) -> float | None:
    if route_metrics is None or evacuation_time_seconds is None:
        return None

    segment_hazard = route_metrics.get("hazard_exposure_score")
    if not isinstance(segment_hazard, (int, float)):
        return None

    # Prototype simulation risk score: occupants_on_segment * segment_hazard_risk * time_on_segment.
    exposure = float(occupants_at_risk) * float(segment_hazard) * float(evacuation_time_seconds)
    return round(exposure / 100.0, 3)


def percentage_delta(baseline: float | None, value: float | None) -> float | None:
    if baseline is None or value is None or baseline == 0:
        return None
    return round(((baseline - value) / baseline) * 100.0, 3)


def recommend_label(rows: list[ExperimentResultRecord]) -> dict[str, str]:
    fastest = min((row for row in rows if row.evacuation_time is not None), key=lambda row: row.evacuation_time or 10e9, default=None)
    safest = min(
        (row for row in rows if row.hazard_exposure_score is not None),
        key=lambda row: (row.unsafe_segment_count or 10e9, row.hazard_exposure_score or 10e9, row.peak_congestion or 10e9, row.evacuation_time or 10e9),
        default=None,
    )
    recommended = safest

    labels: dict[str, str] = {}
    if fastest is not None:
        labels[fastest.strategy.value] = "FASTEST"
    if safest is not None:
        labels[safest.strategy.value] = "SAFEST" if safest.strategy.value not in labels else f"{labels[safest.strategy.value]} / SAFEST"
    if recommended is not None:
        labels[recommended.strategy.value] = "RECOMMENDED" if recommended.strategy.value not in labels else f"{labels[recommended.strategy.value]} / RECOMMENDED"
    return labels
