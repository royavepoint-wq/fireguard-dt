from fastapi.testclient import TestClient

from app.main import app
from app.services import simulation_engine
from app.simulation.models import SimulationStartRequest, SimulationStatus

client = TestClient(app)


def setup_function() -> None:
    simulation_engine.reset()


def test_start_simulation() -> None:
    response = client.post("/api/simulation/start", json={"scenario_id": "electrical-room-fire", "speed_multiplier": 1, "auto_approve": True})

    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"

    simulation_engine.stop()


def test_start_stores_auto_approve_from_request() -> None:
    response = client.post(
        "/api/simulation/start",
        json={"scenario_id": "electrical-room-fire", "speed_multiplier": 5, "auto_approve": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["auto_approve"] is False

    status = client.get("/api/simulation/status").json()
    assert status["auto_approve"] is False

    simulation_engine.stop()


def test_reject_duplicate_start() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)

    response = client.post("/api/simulation/start", json={"scenario_id": "electrical-room-fire", "speed_multiplier": 1, "auto_approve": True})

    assert response.status_code == 409


def test_pause_resume_stop_reset_and_speed_change() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)

    assert client.post("/api/simulation/pause").json()["status"] == "PAUSED"
    assert client.post("/api/simulation/speed", json={"speed_multiplier": 5}).json()["speed_multiplier"] == 5
    assert client.post("/api/simulation/resume").json()["status"] == "RUNNING"
    assert client.post("/api/simulation/stop").json()["status"] == "STOPPED"
    assert client.post("/api/simulation/reset").json()["status"] == "STOPPED"


def test_normal_to_warning_transition() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(24)

    state = simulation_engine.get_status()
    assert state.phase.value == "WARNING"
    assert client.get("/api/twins/fire").json()["risk_level"] == "WARNING"


def test_warning_to_critical_transition() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(38)

    assert simulation_engine.get_status().phase.value == "CRITICAL"
    assert client.get("/api/twins/fire").json()["risk_level"] in {"WARNING", "CRITICAL"}


def test_corridor_c_becomes_unsafe_and_route_switches() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(56)

    building = client.get("/api/twins/building").json()
    corridor_c = next(item for item in building["corridors"] if item["corridor_id"] == "corridor-c")
    occupancy = client.get("/api/twins/occupancy").json()
    static_plan = next(item for item in occupancy["active_routes"] if item["route_id"] == "route-static-plan")
    twin_optimized = next(item for item in occupancy["active_routes"] if item["route_id"] == "route-twin-optimized")

    assert corridor_c["is_accessible"] is False
    assert static_plan["status"] in {"BLOCKED", "NO_SAFE_ROUTE"}
    assert twin_optimized["status"] in {"OPEN", "CONGESTED", "NO_SAFE_ROUTE"}
    assert twin_optimized["strategy"] == "TWIN_OPTIMIZED"
    if twin_optimized["status"] != "NO_SAFE_ROUTE":
        assert len(twin_optimized["path_nodes"]) >= 2


def test_simulation_emits_dynamic_route_lifecycle_events() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(60)

    events = client.get("/api/events").json()
    route_events = [
        event for event in events if event["event_type"] in {
            "ROUTE_UPDATED",
            "ROUTE_RECALCULATION_REQUESTED",
            "ROUTE_BLOCKED",
            "NO_SAFE_ROUTE",
        }
    ]

    assert route_events


def test_response_resources_assigned() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(72)

    response = client.get("/api/twins/response").json()
    crew_1 = next(item for item in response["crews"] if item["crew_id"] == "crew-1")
    drone_1 = next(item for item in response["drones"] if item["drone_id"] == "drone-1")
    assert crew_1["status"] in {"ASSIGNED", "EN_ROUTE", "ON_SCENE"}
    assert drone_1["status"] in {"ASSIGNED", "EN_ROUTE", "ON_SCENE"}


def test_auto_approval_off_waits_for_human_at_5x() -> None:
    simulation_engine.start(
        SimulationStartRequest(
            scenario_id="electrical-room-fire",
            speed_multiplier=5,
            auto_approve=False,
        ),
        run_in_background=False,
    )
    simulation_engine.advance_seconds(70)

    status = client.get("/api/simulation/status").json()
    assert status["status"] == "WAITING_FOR_APPROVAL"
    assert status["auto_approve"] is False
    assert status["pause_reason"] == "AWAITING_APPROVAL"
    assert status["pending_approval"]["status"] == "PENDING"
    assert status["phase"] not in {"CONTAINMENT", "RESOLVED"}

    building = client.get("/api/twins/building").json()
    hvac_zone_3 = next(item for item in building["hvac_zones"] if item["hvac_zone_id"] == "hvac-zone-3")
    assert hvac_zone_3["status"] != "ISOLATED"

    elapsed_before = status["elapsed_seconds"]
    phase_before = status["phase"]
    simulation_engine.advance_seconds(40)
    still_waiting = client.get("/api/simulation/status").json()
    assert still_waiting["status"] == "WAITING_FOR_APPROVAL"
    assert still_waiting["elapsed_seconds"] == elapsed_before
    assert still_waiting["phase"] == phase_before


def test_approve_from_waiting_resumes_and_can_resolve() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)
    waiting = client.get("/api/simulation/status").json()
    approval_id = waiting["pending_approval"]["approval_id"]
    elapsed_before = waiting["elapsed_seconds"]

    approved = client.post(f"/api/simulation/approval/{approval_id}/approve").json()
    assert approved["status"] == "RUNNING"
    assert approved["pending_approval"] is None
    assert approved["elapsed_seconds"] == elapsed_before

    simulation_engine.advance_seconds(15)
    building = client.get("/api/twins/building").json()
    hvac_zone_3 = next(item for item in building["hvac_zones"] if item["hvac_zone_id"] == "hvac-zone-3")
    assert hvac_zone_3["status"] == "ISOLATED"

    events = client.get("/api/events").json()
    approval_events = [event for event in events if event["event_type"] == "APPROVAL_GRANTED"]
    assert approval_events
    assert approval_events[-1]["payload"]["decision_source"] == "HUMAN"

    simulation_engine.advance_seconds(120)
    terminal = client.get("/api/simulation/status").json()
    assert terminal["phase"] in {"CONTAINMENT", "RESOLVED"}
    assert terminal["status"] == "COMPLETED"


def test_reject_from_waiting_uses_rejection_branch() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)
    waiting = client.get("/api/simulation/status").json()
    approval_id = waiting["pending_approval"]["approval_id"]

    rejected = client.post(f"/api/simulation/approval/{approval_id}/reject").json()
    assert rejected["status"] == "RUNNING"
    assert rejected["pending_approval"] is None

    events = client.get("/api/events").json()
    rejected_events = [event for event in events if event["event_type"] == "APPROVAL_REJECTED"]
    assert rejected_events
    assert rejected_events[-1]["payload"]["decision_source"] == "HUMAN"

    simulation_engine.advance_seconds(20)
    building = client.get("/api/twins/building").json()
    hvac_zone_3 = next(item for item in building["hvac_zones"] if item["hvac_zone_id"] == "hvac-zone-3")
    assert hvac_zone_3["status"] != "ISOLATED"


def test_approved_and_rejected_branches_have_meaningfully_different_outcomes() -> None:
    # Approved branch
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)
    approval_id = client.get("/api/simulation/status").json()["pending_approval"]["approval_id"]
    client.post(f"/api/simulation/approval/{approval_id}/approve")
    simulation_engine.advance_seconds(80)
    approved_terminal = client.get("/api/simulation/status").json()
    assert approved_terminal["status"] == "COMPLETED"
    approved_run = client.get("/api/simulation/runs").json()[-1]

    # Rejected branch
    simulation_engine.reset()
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)
    approval_id = client.get("/api/simulation/status").json()["pending_approval"]["approval_id"]
    client.post(f"/api/simulation/approval/{approval_id}/reject")
    simulation_engine.advance_seconds(120)
    rejected_terminal = client.get("/api/simulation/status").json()
    assert rejected_terminal["status"] == "COMPLETED"
    rejected_run = client.get("/api/simulation/runs").json()[-1]

    assert approved_run["governance_decision"] == "HVAC_ISOLATION_APPROVED"
    assert rejected_run["governance_decision"] == "HVAC_ISOLATION_REJECTED"
    assert approved_run["outcome_quality"] == "OPTIMAL"
    assert rejected_run["outcome_quality"] == "DEGRADED"
    assert approved_run["time_to_containment"] < rejected_run["time_to_containment"]
    assert approved_run["time_to_resolution"] < rejected_run["time_to_resolution"]
    assert approved_run["unsafe_zone_duration"] < rejected_run["unsafe_zone_duration"]


def test_rejected_branch_logs_extended_smoke_exposure_event() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)
    approval_id = client.get("/api/simulation/status").json()["pending_approval"]["approval_id"]
    client.post(f"/api/simulation/approval/{approval_id}/reject")

    events = client.get("/api/events").json()
    smoke_extension_events = [event for event in events if "smoke exposure period is extended" in event["message"].lower()]
    assert smoke_extension_events


def test_auto_approval_on_records_required_and_granted_events() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=True), run_in_background=False)
    simulation_engine.advance_seconds(75)

    status = client.get("/api/simulation/status").json()
    assert status["status"] == "RUNNING"
    assert status["pending_approval"] is None

    building = client.get("/api/twins/building").json()
    hvac_zone_3 = next(item for item in building["hvac_zones"] if item["hvac_zone_id"] == "hvac-zone-3")
    assert hvac_zone_3["status"] == "ISOLATED"

    events = client.get("/api/events").json()
    required_events = [event for event in events if event["event_type"] == "APPROVAL_REQUIRED"]
    granted_events = [event for event in events if event["event_type"] == "APPROVAL_GRANTED"]
    assert required_events
    assert granted_events
    assert granted_events[-1]["payload"]["decision_source"] == "AUTO_APPROVED_DEMO_ACTION"


def test_reset_clears_pending_approval() -> None:
    simulation_engine.start(SimulationStartRequest(auto_approve=False), run_in_background=False)
    simulation_engine.advance_seconds(70)
    pending_state = client.get("/api/simulation/status").json()
    assert pending_state["pending_approval"] is not None

    reset_state = client.post("/api/simulation/reset").json()
    assert reset_state["pending_approval"] is None
    assert reset_state["status"] == "STOPPED"


def test_reset_restores_initial_twin_state() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(80)

    client.post("/api/simulation/reset")
    fire = client.get("/api/twins/fire").json()
    occupancy = client.get("/api/twins/occupancy").json()
    response = client.get("/api/twins/response").json()

    assert fire["temperature"] == 24.6
    assert occupancy["evacuating_count"] == 0
    assert response["crews"][0]["status"] == "AVAILABLE"


def test_sensor_anomaly_does_not_trigger_critical_fire() -> None:
    simulation_engine.start(SimulationStartRequest(scenario_id="sensor-anomaly"), run_in_background=False)
    simulation_engine.advance_seconds(45)

    fire = client.get("/api/twins/fire").json()
    assert fire["risk_level"] != "CRITICAL"


def test_run_summary_stored() -> None:
    simulation_engine.start(SimulationStartRequest(), run_in_background=False)
    simulation_engine.advance_seconds(120)

    runs = client.get("/api/simulation/runs").json()
    assert len(runs) >= 1
    assert runs[-1]["status"] == SimulationStatus.COMPLETED