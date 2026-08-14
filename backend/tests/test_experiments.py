from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _wait_for_completion(max_checks: int = 120) -> None:
    for _index in range(max_checks):
        status = client.get("/api/experiments/status").json()
        if not status["is_running"]:
            return
    raise AssertionError("Experiment run did not complete in expected time.")


def test_experiment_run_and_results_for_same_scenario_conditions() -> None:
    response = client.post(
        "/api/experiments/run",
        json={
            "scenario_ids": ["standard-electrical-fire"],
            "strategies": ["STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"],
            "runs_per_configuration": 1,
            "include_governance_branches": False,
        },
    )
    assert response.status_code == 200

    _wait_for_completion()

    results = client.get("/api/experiments/results?scenario=standard-electrical-fire").json()
    rows = results["scenario_results"]
    assert {item["strategy"] for item in rows} == {"STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"}

    warning_times = {item["time_to_warning"] for item in rows}
    critical_times = {item["time_to_critical"] for item in rows}
    assert len(warning_times) == 1
    assert len(critical_times) == 1


def test_blocked_exit_and_peak_occupancy_variations_produce_results() -> None:
    response = client.post(
        "/api/experiments/run",
        json={
            "scenario_ids": ["blocked-exit", "peak-occupancy", "sprinkler-failure"],
            "strategies": ["TWIN_OPTIMIZED"],
            "runs_per_configuration": 1,
            "include_governance_branches": False,
        },
    )
    assert response.status_code == 200

    _wait_for_completion()
    results = client.get("/api/experiments/results").json()
    scenario_ids = {item["scenario_id"] for item in results["scenario_results"]}
    assert "blocked-exit" in scenario_ids
    assert "peak-occupancy" in scenario_ids
    assert "sprinkler-failure" in scenario_ids


def test_experiment_files_generated() -> None:
    response = client.post(
        "/api/experiments/run",
        json={
            "scenario_ids": ["standard-electrical-fire"],
            "strategies": ["STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"],
            "runs_per_configuration": 1,
            "include_governance_branches": True,
        },
    )
    assert response.status_code == 200
    _wait_for_completion()

    repo_root = Path(__file__).resolve().parents[2]
    assert (repo_root / "data" / "experiments" / "scenario_results.csv").exists()
    assert (repo_root / "data" / "experiments" / "strategy_comparison.csv").exists()
    assert (repo_root / "data" / "experiments" / "governance_comparison.csv").exists()
    assert (repo_root / "data" / "experiments" / "experiment_summary.json").exists()
    assert (repo_root / "data" / "results" / "final_project_metrics.json").exists()
    assert (repo_root / "data" / "results" / "slide_metrics.json").exists()
