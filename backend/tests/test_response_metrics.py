from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services import simulation_engine
from app.simulation.models import SimulationStartRequest

client = TestClient(app)


def setup_function() -> None:
    simulation_engine.reset()


def test_response_eta_available_when_dispatched() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=True), run_in_background=False)
    simulation_engine.advance_seconds(66)

    response = client.get("/api/twins/response").json()
    crew_1 = next(item for item in response["crews"] if item["crew_id"] == "crew-1")
    drone_1 = next(item for item in response["drones"] if item["drone_id"] == "drone-1")

    assert crew_1["status"] in {"ASSIGNED", "EN_ROUTE", "ON_SCENE"}
    assert drone_1["status"] in {"ASSIGNED", "EN_ROUTE", "ON_SCENE"}
    if crew_1["status"] != "ON_SCENE":
        assert crew_1["eta_minutes"] > 0
    if drone_1["status"] != "ON_SCENE":
        assert drone_1["eta_minutes"] > 0


def test_response_eta_zero_when_no_active_incident() -> None:
    response = client.get("/api/twins/response").json()
    assert all(item["status"] == "AVAILABLE" for item in response["crews"])
    assert all(item["status"] == "AVAILABLE" for item in response["drones"])
    assert all(item["eta_minutes"] == 0 for item in response["crews"])
    assert all(item["eta_minutes"] == 0 for item in response["drones"])


def test_first_response_and_containment_metrics_calculated() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=True), run_in_background=False)
    simulation_engine.advance_seconds(150)

    run = client.get("/api/simulation/runs").json()[-1]
    assert run["time_to_first_dispatch"] is not None
    assert run["time_to_first_response"] is not None
    assert run["time_to_containment"] is not None
    assert run["time_to_resolution"] is not None
