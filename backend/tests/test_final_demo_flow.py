from fastapi.testclient import TestClient
from time import sleep

from app.main import app

client = TestClient(app)


def _run_until_complete_or_waiting(max_steps: int = 300) -> dict[str, object]:
    for _ in range(max_steps):
        status = client.get("/api/simulation/status").json()
        if status["status"] in {"WAITING_FOR_APPROVAL", "COMPLETED", "ERROR"}:
            return status
        sleep(0.03)
    return client.get("/api/simulation/status").json()


def test_final_demo_manual_approval_flow() -> None:
    client.post("/api/simulation/reset")

    start = client.post(
        "/api/simulation/start",
        json={
            "scenario_id": "electrical-room-fire",
            "speed_multiplier": 10,
            "auto_approve": False,
            "presentation_mode": True,
        },
    )
    assert start.status_code == 200

    status = _run_until_complete_or_waiting()
    assert status["status"] in {"RUNNING", "WAITING_FOR_APPROVAL", "COMPLETED"}

    if status["status"] == "WAITING_FOR_APPROVAL":
        approval_id = status["pending_approval"]["approval_id"]
        approve = client.post(f"/api/simulation/approval/{approval_id}/approve")
        assert approve.status_code == 200

    for _ in range(400):
        status = client.get("/api/simulation/status").json()
        if status["status"] == "COMPLETED":
            break
        sleep(0.03)

    final_status = client.get("/api/simulation/status").json()
    assert final_status["status"] == "COMPLETED"
    assert final_status["phase"] == "RESOLVED"
    assert final_status["latest_run_summary"] is not None
    assert final_status["latest_run_summary"]["time_to_first_response"] is not None
    assert final_status["latest_run_summary"]["time_to_containment"] is not None


def test_evidence_package_refresh_and_exports() -> None:
    client.post(
        "/api/experiments/run",
        json={
            "scenario_ids": ["standard-electrical-fire"],
            "strategies": ["STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"],
            "runs_per_configuration": 1,
            "include_governance_branches": True,
        },
    )
    for _ in range(300):
        status = client.get("/api/experiments/status").json()
        if not status["is_running"]:
            break
        sleep(0.03)

    refresh = client.post("/api/experiments/evidence/refresh")
    assert refresh.status_code == 200
    body = refresh.json()
    assert body["status"] == "generated"

    json_export = client.get("/api/experiments/export/json")
    assert json_export.status_code == 200
    assert "application/json" in json_export.headers["content-type"]

    csv_export = client.get("/api/experiments/export/csv?kind=scenario_comparison")
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]
