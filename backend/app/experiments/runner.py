from __future__ import annotations

from csv import DictWriter
from datetime import datetime
from json import dump
from pathlib import Path
from threading import Lock, Thread
from statistics import mean

from app.experiments.comparison import build_strategy_comparison
from app.experiments.metrics import estimated_evacuation_time, hazard_exposure_metric, route_peak_congestion
from app.experiments.models import (
    ApprovalMode,
    ExperimentResultRecord,
    ExperimentResultsResponse,
    ExperimentRunRequest,
    ExperimentStatusResponse,
    GovernanceComparisonRecord,
)
from app.experiments.scenario_library import get_scenario, list_scenarios
from app.models.occupancy import RouteStrategy
from app.services.event_bus import InMemoryEventBus
from app.services.ml.fire_predictor import FireRiskPredictor
from app.services.roi.calculator import RoiCalculator
from app.services.roi.models import RoiCalculationRequest, RoiScenario
from app.simulation.engine import SimulationEngine
from app.simulation.models import SimulationStartRequest, SimulationStatus


class ExperimentRunner:
    def __init__(self, *, simulation_engine: SimulationEngine, event_bus: InMemoryEventBus, fire_risk_predictor: FireRiskPredictor) -> None:
        self._simulation_engine = simulation_engine
        self._event_bus = event_bus
        self._fire_risk_predictor = fire_risk_predictor
        self._lock = Lock()
        self._status = ExperimentStatusResponse()
        self._scenario_results: list[ExperimentResultRecord] = []
        self._governance_results: list[GovernanceComparisonRecord] = []
        self._repo_root = Path(__file__).resolve().parents[3]

    def list_scenarios(self):
        return list_scenarios()

    def run(self, request: ExperimentRunRequest) -> ExperimentStatusResponse:
        with self._lock:
            if self._status.is_running:
                return self._status

            scenario_ids = request.scenario_ids or [scenario.scenario_id for scenario in list_scenarios()]
            total_configurations = len(scenario_ids) * request.runs_per_configuration
            if request.include_governance_branches:
                total_configurations += len(scenario_ids)

            self._status = ExperimentStatusResponse(
                is_running=True,
                progress=0.0,
                total_configurations=total_configurations,
                completed_configurations=0,
                started_at=datetime.utcnow(),
                completed_at=None,
                last_error=None,
            )

            worker = Thread(target=self._run_worker, args=(request, scenario_ids), daemon=True)
            worker.start()
            return self._status

    def status(self) -> ExperimentStatusResponse:
        with self._lock:
            return self._status.model_copy(deep=True)

    def refresh_evidence_package(self) -> dict[str, object]:
        with self._lock:
            scenario_results = self._scenario_results[:]
            governance_results = self._governance_results[:]

        if not scenario_results:
            final_dir = self._repo_root / "data" / "final"
            return {
                "status": "no_active_results",
                "path": str(final_dir),
                "scenario_results": 0,
                "strategy_rows": 0,
                "governance_rows": 0,
            }

        strategy_comparison = build_strategy_comparison(scenario_results)
        self._write_outputs(scenario_results, strategy_comparison, governance_results)
        final_dir = self._repo_root / "data" / "final"
        return {
            "status": "generated",
            "path": str(final_dir),
            "scenario_results": len(scenario_results),
            "strategy_rows": len(strategy_comparison),
            "governance_rows": len(governance_results),
        }

    def results(self, *, scenario: str | None = None, strategy: RouteStrategy | None = None) -> ExperimentResultsResponse:
        with self._lock:
            scenario_results = self._scenario_results[:]
            governance = self._governance_results[:]
            status = self._status.model_copy(deep=True)

        if scenario is not None:
            scenario_results = [item for item in scenario_results if item.scenario_id == scenario]
            governance = [item for item in governance if item.scenario_id == scenario]

        if strategy is not None:
            scenario_results = [item for item in scenario_results if item.strategy == strategy]

        strategy_comparison = build_strategy_comparison(scenario_results)

        return ExperimentResultsResponse(
            status=status,
            scenario_results=scenario_results,
            strategy_comparison=strategy_comparison,
            governance_comparison=governance,
        )

    def _increment_progress(self) -> None:
        with self._lock:
            self._status.completed_configurations += 1
            if self._status.total_configurations > 0:
                self._status.progress = round(self._status.completed_configurations / self._status.total_configurations, 4)

    def _run_worker(self, request: ExperimentRunRequest, scenario_ids: list[str]) -> None:
        scenario_results: list[ExperimentResultRecord] = []
        governance_results: list[GovernanceComparisonRecord] = []

        try:
            for scenario_id in scenario_ids:
                scenario_definition = get_scenario(scenario_id)

                for run_index in range(request.runs_per_configuration):
                    summary = self._run_simulation_once(scenario_definition.simulation_scenario_id, approval_mode=ApprovalMode.AUTO_APPROVE)
                    per_strategy = self._build_strategy_records(
                        summary=summary,
                        scenario_id=scenario_definition.scenario_id,
                        scenario_name=scenario_definition.name,
                        strategies=request.strategies,
                        run_suffix=f"-{run_index + 1}",
                        approval_mode=ApprovalMode.AUTO_APPROVE,
                    )
                    scenario_results.extend(per_strategy)
                    self._increment_progress()

                if request.include_governance_branches and not scenario_definition.sensor_anomaly:
                    approved = self._run_simulation_once(scenario_definition.simulation_scenario_id, approval_mode=ApprovalMode.FORCE_APPROVE)
                    rejected = self._run_simulation_once(scenario_definition.simulation_scenario_id, approval_mode=ApprovalMode.FORCE_REJECT)

                    approved_records = self._build_strategy_records(
                        summary=approved,
                        scenario_id=scenario_definition.scenario_id,
                        scenario_name=scenario_definition.name,
                        strategies=[RouteStrategy.TWIN_OPTIMIZED],
                        run_suffix="-gov-approved",
                        approval_mode=ApprovalMode.FORCE_APPROVE,
                    )
                    rejected_records = self._build_strategy_records(
                        summary=rejected,
                        scenario_id=scenario_definition.scenario_id,
                        scenario_name=scenario_definition.name,
                        strategies=[RouteStrategy.TWIN_OPTIMIZED],
                        run_suffix="-gov-rejected",
                        approval_mode=ApprovalMode.FORCE_REJECT,
                    )

                    scenario_results.extend(approved_records)
                    scenario_results.extend(rejected_records)

                    if approved_records:
                        row = approved_records[0]
                        governance_results.append(
                            GovernanceComparisonRecord(
                                scenario_id=scenario_definition.scenario_id,
                                branch=ApprovalMode.FORCE_APPROVE,
                                containment_time=row.time_to_containment,
                                hazard_exposure_score=row.hazard_exposure_score,
                                evacuation_time=row.evacuation_time,
                                unsafe_zone_duration=row.unsafe_zone_duration,
                                response_resources_used=row.resources_dispatched,
                                outcome_quality=row.outcome_quality,
                            )
                        )

                    if rejected_records:
                        row = rejected_records[0]
                        governance_results.append(
                            GovernanceComparisonRecord(
                                scenario_id=scenario_definition.scenario_id,
                                branch=ApprovalMode.FORCE_REJECT,
                                containment_time=row.time_to_containment,
                                hazard_exposure_score=row.hazard_exposure_score,
                                evacuation_time=row.evacuation_time,
                                unsafe_zone_duration=row.unsafe_zone_duration,
                                response_resources_used=row.resources_dispatched,
                                outcome_quality=row.outcome_quality,
                            )
                        )

                    self._increment_progress()

            strategy_comparison = build_strategy_comparison(scenario_results)
            self._write_outputs(scenario_results, strategy_comparison, governance_results)

            with self._lock:
                self._scenario_results = scenario_results
                self._governance_results = governance_results
                self._status.is_running = False
                self._status.completed_at = datetime.utcnow()
                self._status.progress = 1.0

        except Exception as error:  # pragma: no cover - defensive status surfacing
            with self._lock:
                self._status.is_running = False
                self._status.completed_at = datetime.utcnow()
                self._status.last_error = str(error)

    def _run_simulation_once(self, simulation_scenario_id: str, *, approval_mode: ApprovalMode) -> dict[str, object]:
        self._simulation_engine.reset()
        auto_approve = approval_mode == ApprovalMode.AUTO_APPROVE
        self._simulation_engine.start(
            SimulationStartRequest(
                scenario_id=simulation_scenario_id,
                speed_multiplier=10,
                auto_approve=auto_approve,
                presentation_mode=False,
            ),
            run_in_background=False,
        )

        guard = 0
        while guard < 800:
            status = self._simulation_engine.get_status()
            if status.status == SimulationStatus.COMPLETED:
                break
            if status.status == SimulationStatus.WAITING_FOR_APPROVAL and status.pending_approval is not None:
                if approval_mode == ApprovalMode.FORCE_REJECT:
                    self._simulation_engine.reject_action_by_id(status.pending_approval.approval_id)
                else:
                    self._simulation_engine.approve_action_by_id(status.pending_approval.approval_id)
            self._simulation_engine.advance_seconds(1)
            guard += 1

        status = self._simulation_engine.get_status()
        summary = status.latest_run_summary
        if summary is None:
            runs = self._simulation_engine.get_runs()
            if not runs:
                raise RuntimeError("Simulation did not produce a run summary.")
            summary = runs[-1].model_dump(mode="json")
        return summary

    def _build_strategy_records(
        self,
        *,
        summary: dict[str, object],
        scenario_id: str,
        scenario_name: str,
        strategies: list[RouteStrategy],
        run_suffix: str,
        approval_mode: ApprovalMode,
    ) -> list[ExperimentResultRecord]:
        route_map = {
            RouteStrategy.STATIC_PLAN: summary.get("static_plan_metrics"),
            RouteStrategy.SHORTEST_PATH: summary.get("shortest_path_metrics"),
            RouteStrategy.TWIN_OPTIMIZED: summary.get("twin_optimized_metrics"),
        }

        completion_time = summary.get("evacuation_completion_time")
        evacuation_start = summary.get("time_to_evacuation")
        baseline_window = None
        if isinstance(completion_time, int) and isinstance(evacuation_start, int):
            baseline_window = float(max(0, completion_time - evacuation_start))

        baseline_route_seconds = None
        twin_metrics = route_map.get(RouteStrategy.TWIN_OPTIMIZED)
        if isinstance(twin_metrics, dict):
            twin_estimated = twin_metrics.get("estimated_time_seconds")
            if isinstance(twin_estimated, (int, float)):
                baseline_route_seconds = float(twin_estimated)

        records: list[ExperimentResultRecord] = []
        for strategy in strategies:
            route_metrics = route_map.get(strategy)
            metrics = route_metrics if isinstance(route_metrics, dict) else None

            estimated_time = estimated_evacuation_time(
                route_metrics=metrics,
                baseline_completion_window=baseline_window,
                baseline_route_seconds=baseline_route_seconds,
            )
            occupants_at_risk = int(summary.get("occupants_at_risk") or 0)
            exposure_score = hazard_exposure_metric(
                occupants_at_risk=occupants_at_risk,
                route_metrics=metrics,
                evacuation_time_seconds=estimated_time,
            )

            peak_congestion_value = route_peak_congestion(metrics, str(summary.get("peak_congestion")) if summary.get("peak_congestion") is not None else None)

            unsafe_segments = None
            distance = None
            selected_exit = None
            status = "N/A"
            if metrics is not None:
                status_value = metrics.get("status")
                status = str(status_value) if status_value is not None else "N/A"
                unsafe = metrics.get("unsafe_segments")
                unsafe_segments = int(unsafe) if isinstance(unsafe, int) else None
                distance_value = metrics.get("distance_meters")
                distance = float(distance_value) if isinstance(distance_value, (int, float)) else None
                selected_value = metrics.get("selected_exit")
                selected_exit = str(selected_value) if selected_value is not None else None

            records.append(
                ExperimentResultRecord(
                    run_id=f"{summary.get('run_id')}-{strategy.value}{run_suffix}",
                    scenario_id=scenario_id,
                    scenario_name=scenario_name,
                    strategy=strategy,
                    approval_mode=approval_mode,
                    evacuation_time=estimated_time,
                    hazard_exposure_score=exposure_score,
                    peak_congestion=peak_congestion_value,
                    unsafe_segment_count=unsafe_segments,
                    distance_travelled=distance,
                    selected_exit=selected_exit,
                    time_to_warning=int(summary["time_to_warning"]) if isinstance(summary.get("time_to_warning"), int) else None,
                    time_to_critical=int(summary["time_to_critical"]) if isinstance(summary.get("time_to_critical"), int) else None,
                    time_to_evacuation=int(summary["time_to_evacuation"]) if isinstance(summary.get("time_to_evacuation"), int) else None,
                    time_to_first_dispatch=int(summary["time_to_first_dispatch"]) if isinstance(summary.get("time_to_first_dispatch"), int) else None,
                    time_to_first_response=int(summary["time_to_first_response"]) if isinstance(summary.get("time_to_first_response"), int) else None,
                    time_to_containment=int(summary["time_to_containment"]) if isinstance(summary.get("time_to_containment"), int) else None,
                    time_to_resolution=int(summary["time_to_resolution"]) if isinstance(summary.get("time_to_resolution"), int) else None,
                    occupants_at_risk=occupants_at_risk,
                    occupants_evacuated=int(summary.get("evacuated") or 0),
                    resources_dispatched=int(summary.get("resources_dispatched") or 0),
                    outcome_quality=str(summary.get("outcome_quality")) if summary.get("outcome_quality") is not None else None,
                    unsafe_zone_duration=int(summary.get("unsafe_zone_duration") or 0),
                    status=status,
                )
            )

        return records

    def _write_outputs(self, scenario_results: list[ExperimentResultRecord], strategy_comparison, governance_results: list[GovernanceComparisonRecord]) -> None:
        experiments_dir = self._repo_root / "data" / "experiments"
        experiments_dir.mkdir(parents=True, exist_ok=True)

        scenario_rows = [row.model_dump(mode="json") for row in scenario_results]
        comparison_rows = [row.model_dump(mode="json") for row in strategy_comparison]
        governance_rows = [row.model_dump(mode="json") for row in governance_results]

        self._write_csv(experiments_dir / "scenario_results.csv", scenario_rows)
        self._write_csv(experiments_dir / "strategy_comparison.csv", comparison_rows)
        self._write_csv(experiments_dir / "governance_comparison.csv", governance_rows)

        with (experiments_dir / "experiment_summary.json").open("w", encoding="utf-8") as handle:
            dump(
                {
                    "generated_at": datetime.utcnow().isoformat(),
                    "scenario_count": len({row.scenario_id for row in scenario_results}),
                    "run_count": len(scenario_results),
                    "comparison_rows": len(comparison_rows),
                    "governance_rows": len(governance_rows),
                    "hazard_exposure_definition": "Prototype simulation risk score: occupants_on_segment * segment_hazard_risk * time_on_segment (normalized /100).",
                    "evacuation_time_definition": "Time from evacuation activation to all affected occupants reaching safe exits; strategy rows use deterministic scaling from route ETA under identical hazard state.",
                    "note": "Simulation metrics are deterministic prototype outputs and not certified life-safety measurements.",
                },
                handle,
                indent=2,
            )

        self._write_project_results(scenario_results, strategy_comparison, governance_results)

    def _write_project_results(self, scenario_results: list[ExperimentResultRecord], strategy_comparison, governance_results: list[GovernanceComparisonRecord]) -> None:
        results_dir = self._repo_root / "data" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        model_info = self._fire_risk_predictor.model_info()
        model_metrics = self._fire_risk_predictor.metrics()
        base_roi = RoiCalculator().calculate(RoiCalculationRequest(scenario=RoiScenario.BASE))

        static_rows = [row for row in scenario_results if row.strategy == RouteStrategy.STATIC_PLAN and row.approval_mode == ApprovalMode.AUTO_APPROVE]
        shortest_rows = [row for row in scenario_results if row.strategy == RouteStrategy.SHORTEST_PATH and row.approval_mode == ApprovalMode.AUTO_APPROVE]
        optimized_rows = [row for row in scenario_results if row.strategy == RouteStrategy.TWIN_OPTIMIZED and row.approval_mode == ApprovalMode.AUTO_APPROVE]

        def _avg(items: list[ExperimentResultRecord], field: str) -> float | None:
            values = [getattr(item, field) for item in items if isinstance(getattr(item, field), (int, float))]
            if not values:
                return None
            return round(float(mean(values)), 3)

        static_evac = _avg(static_rows, "evacuation_time")
        shortest_evac = _avg(shortest_rows, "evacuation_time")
        optimized_evac = _avg(optimized_rows, "evacuation_time")
        static_exposure = _avg(static_rows, "hazard_exposure_score")
        shortest_exposure = _avg(shortest_rows, "hazard_exposure_score")
        optimized_exposure = _avg(optimized_rows, "hazard_exposure_score")

        optimized_rows_comparison = [
            row
            for row in strategy_comparison
            if row.strategy == RouteStrategy.TWIN_OPTIMIZED and row.evacuation_time_change_vs_static_pct is not None
        ]

        def _avg_comparison(rows, field: str) -> float | None:
            values = [getattr(item, field) for item in rows if isinstance(getattr(item, field), (int, float))]
            if not values:
                return None
            return round(float(mean(values)), 3)

        evacuation_time_change_vs_static = _avg_comparison(optimized_rows_comparison, "evacuation_time_change_vs_static_pct")
        hazard_exposure_reduction_vs_static = _avg_comparison(optimized_rows_comparison, "hazard_exposure_reduction_vs_static_pct")

        response_row = optimized_rows[0] if optimized_rows else (scenario_results[0] if scenario_results else None)

        final_metrics = {
            "selected_ml_model": model_info.model_name,
            "ml_accuracy": model_metrics.accuracy,
            "ml_macro_f1": model_metrics.macro_f1,
            "critical_recall": model_metrics.critical_recall,
            "static_evacuation_time": static_evac,
            "shortest_path_evacuation_time": shortest_evac,
            "optimized_evacuation_time": optimized_evac,
            "static_hazard_exposure": static_exposure,
            "shortest_hazard_exposure": shortest_exposure,
            "optimized_hazard_exposure": optimized_exposure,
            "evacuation_time_change_vs_static": evacuation_time_change_vs_static,
            "hazard_exposure_reduction_vs_static": hazard_exposure_reduction_vs_static,
            "time_to_first_response": response_row.time_to_first_response if response_row else None,
            "time_to_containment": response_row.time_to_containment if response_row else None,
            "base_3_year_roi": base_roi.three_year_roi_percent,
            "measured_simulation_metrics": {
                "source": "SIMULATION_RESULT",
                "scenario_count": len({row.scenario_id for row in scenario_results}),
            },
            "illustrative_financial_assumptions": {
                "source": "ILLUSTRATIVE_ROI",
                "disclosure": base_roi.assumption_disclosure,
            },
        }

        slide_metrics = {
            "prediction_accuracy": {"value": model_metrics.accuracy, "unit": "ratio", "source_type": "MODEL_TEST_RESULT"},
            "macro_f1": {"value": model_metrics.macro_f1, "unit": "ratio", "source_type": "MODEL_TEST_RESULT"},
            "critical_recall": {"value": model_metrics.critical_recall, "unit": "ratio", "source_type": "MODEL_TEST_RESULT"},
            "evacuation_time_change": {"value": final_metrics["evacuation_time_change_vs_static"], "unit": "percent", "source_type": "SIMULATION_RESULT"},
            "hazard_exposure_reduction": {"value": final_metrics["hazard_exposure_reduction_vs_static"], "unit": "percent", "source_type": "SIMULATION_RESULT"},
            "first_response_time": {"value": final_metrics["time_to_first_response"], "unit": "seconds", "source_type": "SIMULATION_RESULT"},
            "containment_time": {"value": final_metrics["time_to_containment"], "unit": "seconds", "source_type": "SIMULATION_RESULT"},
            "projected_3_year_roi": {"value": final_metrics["base_3_year_roi"], "unit": "percent", "source_type": "ILLUSTRATIVE_ROI"},
        }

        with (results_dir / "final_project_metrics.json").open("w", encoding="utf-8") as handle:
            dump(final_metrics, handle, indent=2)
        with (results_dir / "slide_metrics.json").open("w", encoding="utf-8") as handle:
            dump(slide_metrics, handle, indent=2)

        self._write_final_evidence_package(
            scenario_results=scenario_results,
            strategy_comparison=strategy_comparison,
            governance_results=governance_results,
            model_info=model_info.model_dump(mode="json"),
            model_metrics=model_metrics.model_dump(mode="json"),
            final_metrics=final_metrics,
        )

    def _write_final_evidence_package(
        self,
        *,
        scenario_results: list[ExperimentResultRecord],
        strategy_comparison,
        governance_results: list[GovernanceComparisonRecord],
        model_info: dict[str, object],
        model_metrics: dict[str, object],
        final_metrics: dict[str, object],
    ) -> None:
        final_dir = self._repo_root / "data" / "final"
        final_dir.mkdir(parents=True, exist_ok=True)

        strategy_rows = [row.model_dump(mode="json") for row in strategy_comparison]
        governance_rows = [row.model_dump(mode="json") for row in governance_results]

        self._write_csv(final_dir / "scenario_comparison.csv", strategy_rows)
        self._write_csv(final_dir / "governance_comparison.csv", governance_rows)

        response_rows: list[dict[str, object]] = []
        for row in scenario_results:
            if row.strategy != RouteStrategy.TWIN_OPTIMIZED or row.approval_mode != ApprovalMode.AUTO_APPROVE:
                continue
            response_rows.append(
                {
                    "scenario_id": row.scenario_id,
                    "scenario_name": row.scenario_name,
                    "first_dispatch_time": row.time_to_first_dispatch,
                    "first_response_time": row.time_to_first_response,
                    "containment_time": row.time_to_containment,
                    "resolution_time": row.time_to_resolution,
                    "resources_dispatched": row.resources_dispatched,
                    "outcome_quality": row.outcome_quality,
                }
            )
        self._write_csv(final_dir / "response_metrics.csv", response_rows)

        ml_rows = [
            {
                "metric": "accuracy",
                "value": model_metrics.get("accuracy"),
                "source": "MODEL_TEST_RESULT",
            },
            {
                "metric": "macro_f1",
                "value": model_metrics.get("macro_f1"),
                "source": "MODEL_TEST_RESULT",
            },
            {
                "metric": "critical_recall",
                "value": model_metrics.get("critical_recall"),
                "source": "MODEL_TEST_RESULT",
            },
            {
                "metric": "roc_auc",
                "value": model_metrics.get("roc_auc"),
                "source": "MODEL_TEST_RESULT",
            },
            {
                "metric": "model_name",
                "value": model_info.get("model_name"),
                "source": "MODEL_TEST_RESULT",
            },
        ]
        self._write_csv(final_dir / "ml_metrics.csv", ml_rows)

        roi_calculator = RoiCalculator()
        roi_rows = []
        for scenario in [RoiScenario.CONSERVATIVE, RoiScenario.BASE, RoiScenario.OPTIMISTIC]:
            scenario_result = roi_calculator.calculate(RoiCalculationRequest(scenario=scenario)).model_dump(mode="json")
            roi_rows.append(
                {
                    "scenario": scenario_result.get("scenario"),
                    "initial_investment": scenario_result.get("initial_investment"),
                    "annual_benefit": scenario_result.get("annual_benefit"),
                    "payback_months": scenario_result.get("payback_months"),
                    "three_year_roi_percent": scenario_result.get("three_year_roi_percent"),
                    "source": "ILLUSTRATIVE_ROI",
                }
            )
        self._write_csv(final_dir / "roi_scenarios.csv", roi_rows)

        with (final_dir / "project_metrics.json").open("w", encoding="utf-8") as handle:
            dump(
                {
                    **final_metrics,
                    "provenance": {
                        "model_metrics": "MODEL_TEST_RESULT",
                        "strategy_metrics": "SIMULATION_RESULT",
                        "response_metrics": "SIMULATION_RESULT",
                        "roi_metrics": "ILLUSTRATIVE_ROI",
                    },
                    "generated_at": datetime.utcnow().isoformat(),
                },
                handle,
                indent=2,
            )

    def _write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return

        fieldnames = list(rows[0].keys())
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
