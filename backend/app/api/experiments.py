from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from pathlib import Path

from app.experiments.models import ExperimentResultsResponse, ExperimentRunRequest
from app.models.occupancy import RouteStrategy
from app.services import experiment_runner

router = APIRouter(prefix="/api/experiments")


@router.get("/library")
def get_experiment_scenarios():
    return experiment_runner.list_scenarios()


@router.post("/run")
def run_experiments(request: ExperimentRunRequest):
    return experiment_runner.run(request)


@router.get("/status")
def experiment_status():
    return experiment_runner.status()


@router.get("/results", response_model=ExperimentResultsResponse)
def experiment_results(
    scenario: str | None = Query(default=None),
    strategy: RouteStrategy | None = Query(default=None),
):
    return experiment_runner.results(scenario=scenario, strategy=strategy)


@router.post("/evidence/refresh")
def refresh_evidence_package():
    return experiment_runner.refresh_evidence_package()


@router.get("/export/json")
def export_results_json():
    output = experiment_runner.refresh_evidence_package()
    path = Path(output["path"]) / "project_metrics.json"
    return FileResponse(path, media_type="application/json", filename="fireguard-project-metrics.json")


@router.get("/export/csv")
def export_results_csv(kind: str = Query(default="scenario_comparison")):
    output = experiment_runner.refresh_evidence_package()
    path = Path(output["path"]) / f"{kind}.csv"
    if not path.exists():
                path = Path(output["path"]) / "scenario_comparison.csv"
                kind = "scenario_comparison"
    return FileResponse(path, media_type="text/csv", filename=f"fireguard-{kind}.csv")
