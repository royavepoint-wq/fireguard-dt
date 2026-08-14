from __future__ import annotations

FEATURE_LABELS: dict[str, str] = {
    "temperature": "Temperature",
    "temperature_rate": "Temperature Rise",
    "smoke_level": "Smoke Concentration",
    "co_level": "CO Concentration",
    "co2_level": "CO2 Concentration",
    "humidity": "Humidity",
    "electrical_load": "Electrical Load",
    "occupancy": "Occupancy",
    "hvac_running": "HVAC Running",
    "sprinkler_active": "Sprinkler Active",
}


def feature_label(name: str) -> str:
    return FEATURE_LABELS.get(name, name.replace("_", " ").title())
