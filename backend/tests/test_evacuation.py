from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_function() -> None:
    client.post("/api/digital-twin/reset")


def test_route_endpoint_returns_graph_path() -> None:
    response = client.post(
        "/api/evacuation/route",
        json={
            "start_zone_id": "room-electrical-01",
            "strategy": "TWIN_OPTIMIZED",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "DIJKSTRA"
    assert body["strategy"] == "TWIN_OPTIMIZED"
    if body["status"] != "NO_SAFE_ROUTE":
        assert len(body["path_nodes"]) >= 2
        assert len(body["path_coordinates"]) == len(body["path_nodes"])


def test_compare_endpoint_returns_all_three_strategies() -> None:
    response = client.post(
        "/api/evacuation/compare",
        json={
            "start_zone_id": "room-electrical-01",
            "strategy": "TWIN_OPTIMIZED",
        },
    )

    assert response.status_code == 200
    body = response.json()
    strategies = {item["strategy"] for item in body["results"]}
    assert strategies == {"STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"}


def test_blocking_all_exits_results_in_no_safe_route() -> None:
    building = client.get("/api/twins/building").json()
    updated_exits = [
        {**exit_item, "is_blocked": True, "is_available": False}
        for exit_item in building["exits"]
    ]
    client.patch("/api/twins/building", json={"exits": updated_exits})

    response = client.post(
        "/api/evacuation/route",
        json={
            "start_zone_id": "room-electrical-01",
            "strategy": "TWIN_OPTIMIZED",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NO_SAFE_ROUTE"
    assert body["selected_exit"] is None


def test_twin_optimized_cost_reflects_hazard_terms_over_shortest_path() -> None:
    client.patch(
        "/api/twins/fire",
        json={
            "temperature": 88.0,
            "temperature_rate": 2.2,
            "smoke_level": 0.78,
            "co_level": 52.0,
            "co2_level": 1750.0,
            "fire_risk_probability": 0.92,
            "risk_level": "CRITICAL",
        },
    )

    response = client.post(
        "/api/evacuation/compare",
        json={
            "start_zone_id": "room-electrical-01",
            "strategy": "TWIN_OPTIMIZED",
        },
    )

    assert response.status_code == 200
    body = response.json()
    by_strategy = {item["strategy"]: item for item in body["results"]}
    shortest = by_strategy["SHORTEST_PATH"]
    optimized = by_strategy["TWIN_OPTIMIZED"]

    if shortest["status"] != "NO_SAFE_ROUTE" and optimized["status"] != "NO_SAFE_ROUTE":
        assert optimized["fire_risk_cost"] >= 0
        assert optimized["smoke_risk_cost"] >= 0
        assert optimized["total_cost"] >= shortest["total_cost"]
