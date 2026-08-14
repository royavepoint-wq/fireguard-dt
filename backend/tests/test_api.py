from fastapi.testclient import TestClient

from app.main import app
from app.services import simulation_engine
from app.simulation.models import SimulationStartRequest

client = TestClient(app)


def setup_function() -> None:
    client.delete("/api/events")
    client.post("/api/digital-twin/reset")


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_fire_twin() -> None:
    response = client.get("/api/twins/fire")

    assert response.status_code == 200
    body = response.json()
    assert body["twin_id"] == "fire_environment"
    assert body["temperature"] == 24.6


def test_update_fire_twin() -> None:
    response = client.patch(
        "/api/twins/fire",
        json={
            "temperature": 31.2,
            "temperature_rate": 0.8,
            "fire_risk_probability": 0.42,
            "risk_level": "WARNING",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["temperature"] == 31.2
    assert body["risk_level"] == "WARNING"


def test_invalid_fire_twin_update() -> None:
    response = client.patch(
        "/api/twins/fire",
        json={"humidity": 120},
    )

    assert response.status_code == 422


def test_get_building_twin() -> None:
    response = client.get("/api/twins/building")

    assert response.status_code == 200
    body = response.json()
    assert body["building_id"] == "FG-BLDG-01"
    assert len(body["floors"]) == 3


def test_update_exit_b_state() -> None:
    building_response = client.get("/api/twins/building")
    exits = building_response.json()["exits"]
    updated_exits = [
        {**exit_item, "is_available": False, "is_blocked": True}
        if exit_item["exit_id"] == "exit-b"
        else exit_item
        for exit_item in exits
    ]

    response = client.patch("/api/twins/building", json={"exits": updated_exits})

    assert response.status_code == 200
    exit_b = next(exit_item for exit_item in response.json()["exits"] if exit_item["exit_id"] == "exit-b")
    assert exit_b["is_blocked"] is True
    assert exit_b["is_available"] is False


def test_get_occupancy_twin() -> None:
    response = client.get("/api/twins/occupancy")

    assert response.status_code == 200
    assert response.json()["total_occupancy"] == 243


def test_get_response_twin() -> None:
    response = client.get("/api/twins/response")

    assert response.status_code == 200
    body = response.json()
    assert len(body["crews"]) == 2
    assert len(body["drones"]) == 2


def test_event_publication() -> None:
    client.patch("/api/twins/fire", json={"temperature": 29.0})

    response = client.get("/api/events?source_twin=fire_environment")

    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[-1]["event_type"] == "TWIN_STATE_UPDATED"


def test_digital_twin_reset() -> None:
    response = client.post("/api/digital-twin/reset")

    assert response.status_code == 200
    body = response.json()
    assert body["fire_twin"]["temperature"] == 24.6
    assert body["orchestrator"]["status"] == "NORMAL"

    events_response = client.get("/api/events")
    events = events_response.json()
    assert len(events) >= 5
    assert events[-1]["event_type"] == "SYSTEM_INITIALIZED"


def test_digital_twin_reset_clears_pending_approval() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)

    pending_before = client.get("/api/simulation/status").json()
    assert pending_before["pending_approval"] is not None

    client.post("/api/digital-twin/reset")
    status_after = client.get("/api/simulation/status").json()
    assert status_after["status"] == "STOPPED"
    assert status_after["pending_approval"] is None


def test_combined_digital_twin_state() -> None:
    response = client.get("/api/digital-twin/state")

    assert response.status_code == 200
    body = response.json()
    assert body["fire_twin"]["twin_id"] == "fire_environment"
    assert body["fire_twin"]["prediction_source"] in {"ML_MODEL", "RULE_BASED_FALLBACK"}
    assert body["building_twin"]["building_id"] == "FG-BLDG-01"
    assert body["orchestrator"]["twins_online"] == 4


def test_orchestrator_status() -> None:
    response = client.get("/api/orchestrator/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NORMAL"
    assert body["human_oversight"] is True