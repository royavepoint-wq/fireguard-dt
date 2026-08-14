from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_roi_scenarios_available() -> None:
    response = client.get("/api/roi/scenarios")
    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    assert {item["scenario"] for item in scenarios} == {"CONSERVATIVE", "BASE", "OPTIMISTIC"}


def test_roi_calculation_conservative_base_optimistic() -> None:
    conservative = client.post("/api/roi/calculate", json={"scenario": "CONSERVATIVE"}).json()
    base = client.post("/api/roi/calculate", json={"scenario": "BASE"}).json()
    optimistic = client.post("/api/roi/calculate", json={"scenario": "OPTIMISTIC"}).json()

    assert conservative["three_year_roi_percent"] <= base["three_year_roi_percent"]
    assert base["three_year_roi_percent"] <= optimistic["three_year_roi_percent"]


def test_roi_no_payback_when_net_benefit_negative() -> None:
    assumptions = client.get("/api/roi/assumptions").json()["scenarios"]
    base = next(item for item in assumptions if item["scenario"] == "BASE")
    base["avoided_downtime"] = 1000
    base["damage_risk_reduction"] = 1000
    base["maintenance_savings"] = 1000
    base["response_efficiency"] = 1000
    base["false_alarm_reduction"] = 1000
    base["compliance_preparedness_value"] = 1000

    response = client.post(
        "/api/roi/calculate",
        json={"scenario": "BASE", "assumptions_override": base},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["annual_net_benefit"] < 0
    assert body["payback_months"] is None
    assert body["payback_statement"] == "No Payback Within Model Horizon"


def test_roi_assumption_override_applied() -> None:
    assumptions = client.get("/api/roi/assumptions").json()["scenarios"]
    base = next(item for item in assumptions if item["scenario"] == "BASE")
    base["maintenance_savings"] = base["maintenance_savings"] + 5000

    response = client.post(
        "/api/roi/calculate",
        json={"scenario": "BASE", "assumptions_override": base},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["benefit_breakdown"]["maintenance_savings"] == base["maintenance_savings"]
