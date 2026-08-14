from __future__ import annotations

from app.experiments.metrics import recommend_label
from app.experiments.models import ExperimentResultRecord, StrategyComparisonRecord
from app.experiments.models import ApprovalMode
from app.models.occupancy import RouteStrategy

from app.experiments.metrics import percentage_delta


def build_strategy_comparison(records: list[ExperimentResultRecord]) -> list[StrategyComparisonRecord]:
    rows: list[StrategyComparisonRecord] = []

    grouped: dict[str, list[ExperimentResultRecord]] = {}
    for record in records:
        if record.approval_mode != ApprovalMode.AUTO_APPROVE:
            continue
        grouped.setdefault(record.scenario_id, []).append(record)

    for scenario_id, scenario_rows in grouped.items():
        recommendation_labels = recommend_label(scenario_rows)
        static_row = next((item for item in scenario_rows if item.strategy == RouteStrategy.STATIC_PLAN), None)
        for item in scenario_rows:
            rows.append(
                StrategyComparisonRecord(
                    scenario_id=item.scenario_id,
                    scenario_name=item.scenario_name,
                    strategy=item.strategy,
                    evacuation_time=item.evacuation_time,
                    hazard_exposure_score=item.hazard_exposure_score,
                    peak_congestion=item.peak_congestion,
                    distance_travelled=item.distance_travelled,
                    selected_exit=item.selected_exit,
                    evacuation_time_change_vs_static_pct=percentage_delta(static_row.evacuation_time if static_row else None, item.evacuation_time),
                    hazard_exposure_reduction_vs_static_pct=percentage_delta(static_row.hazard_exposure_score if static_row else None, item.hazard_exposure_score),
                    congestion_reduction_vs_static_pct=percentage_delta(static_row.peak_congestion if static_row else None, item.peak_congestion),
                    recommendation_label=recommendation_labels.get(item.strategy.value),
                )
            )

    return rows
