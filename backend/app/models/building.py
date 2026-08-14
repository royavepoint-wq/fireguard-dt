from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.common import APIModel, TwinStatus, utc_now


class Floor(APIModel):
    floor_id: str
    name: str
    level: int
    zone_ids: list[str] = Field(default_factory=list)


class Room(APIModel):
    room_id: str
    name: str
    floor_id: str
    zone_id: str
    room_type: str
    occupancy_limit: int | None = None


class Corridor(APIModel):
    corridor_id: str
    name: str
    floor_id: str
    zone_id: str
    is_accessible: bool = True
    status: str = "SAFE"


class Exit(APIModel):
    exit_id: str
    name: str
    floor_id: str | None = None
    zone_id: str | None = None
    is_available: bool = True
    is_blocked: bool = False


class HVACZone(APIModel):
    hvac_zone_id: str
    name: str
    floor_id: str
    status: str = "NORMAL"
    airflow_percentage: float = 100.0

    @field_validator("airflow_percentage")
    @classmethod
    def validate_airflow(cls, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            raise ValueError("airflow_percentage must be between 0 and 100")
        return value


class Sprinkler(APIModel):
    sprinkler_id: str
    zone_id: str
    status: str = "READY"
    is_active: bool = False


class ElectricalZone(APIModel):
    electrical_zone_id: str
    name: str
    floor_id: str
    load_percentage: float = 42.0
    status: str = "NORMAL"

    @field_validator("load_percentage")
    @classmethod
    def validate_load(cls, value: float) -> float:
        if not 0.0 <= value <= 100.0:
            raise ValueError("load_percentage must be between 0 and 100")
        return value


class BuildingInfrastructureTwinState(APIModel):
    twin_id: str = "building_infrastructure"
    name: str = "Building Infrastructure Twin"
    status: TwinStatus = TwinStatus.ONLINE
    last_updated: datetime = Field(default_factory=utc_now)

    building_id: str = "FG-BLDG-01"
    floors: list[Floor] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    corridors: list[Corridor] = Field(default_factory=list)
    exits: list[Exit] = Field(default_factory=list)
    hvac_zones: list[HVACZone] = Field(default_factory=list)
    sprinklers: list[Sprinkler] = Field(default_factory=list)
    electrical_zones: list[ElectricalZone] = Field(default_factory=list)


class BuildingInfrastructureTwinUpdate(APIModel):
    name: str | None = None
    status: TwinStatus | None = None
    building_id: str | None = None
    floors: list[Floor] | None = None
    rooms: list[Room] | None = None
    corridors: list[Corridor] | None = None
    exits: list[Exit] | None = None
    hvac_zones: list[HVACZone] | None = None
    sprinklers: list[Sprinkler] | None = None
    electrical_zones: list[ElectricalZone] | None = None


def build_default_building_state() -> BuildingInfrastructureTwinState:
    return BuildingInfrastructureTwinState(
        floors=[
            Floor(floor_id="floor-1", name="Floor 1", level=1, zone_ids=["zone-1a", "zone-1b"]),
            Floor(floor_id="floor-2", name="Floor 2", level=2, zone_ids=["zone-2a", "zone-2b"]),
            Floor(floor_id="floor-3", name="Floor 3", level=3, zone_ids=["zone-3a"]),
        ],
        rooms=[
            Room(
                room_id="room-electrical-01",
                name="Electrical Room",
                floor_id="floor-1",
                zone_id="zone-1a",
                room_type="UTILITY",
                occupancy_limit=6,
            ),
            Room(
                room_id="room-ops-01",
                name="Operations Room",
                floor_id="floor-2",
                zone_id="zone-2a",
                room_type="OPERATIONS",
                occupancy_limit=48,
            ),
            Room(
                room_id="room-conference-01",
                name="Conference Suite",
                floor_id="floor-3",
                zone_id="zone-3a",
                room_type="ASSEMBLY",
                occupancy_limit=72,
            ),
        ],
        corridors=[
            Corridor(corridor_id="corridor-a", name="Corridor A", floor_id="floor-2", zone_id="zone-2b"),
            Corridor(corridor_id="corridor-b", name="Corridor B", floor_id="floor-3", zone_id="zone-3a"),
            Corridor(corridor_id="corridor-c", name="Corridor C", floor_id="floor-1", zone_id="zone-1a"),
        ],
        exits=[
            Exit(exit_id="exit-a", name="Exit A", floor_id="floor-1", zone_id="zone-1b"),
            Exit(exit_id="exit-b", name="Exit B", floor_id="floor-1", zone_id="zone-1b"),
            Exit(exit_id="exit-c", name="Exit C", floor_id="floor-2", zone_id="zone-2b"),
            Exit(exit_id="exit-d", name="Exit D", floor_id="floor-3", zone_id="zone-3a"),
        ],
        hvac_zones=[
            HVACZone(hvac_zone_id="hvac-zone-1", name="HVAC Zone 1", floor_id="floor-2"),
            HVACZone(hvac_zone_id="hvac-zone-2", name="HVAC Zone 2", floor_id="floor-3"),
            HVACZone(hvac_zone_id="hvac-zone-3", name="HVAC Zone 3", floor_id="floor-1"),
        ],
        sprinklers=[
            Sprinkler(sprinkler_id="sprinkler-1a", zone_id="zone-1a"),
            Sprinkler(sprinkler_id="sprinkler-2a", zone_id="zone-2a"),
            Sprinkler(sprinkler_id="sprinkler-3a", zone_id="zone-3a"),
        ],
        electrical_zones=[
            ElectricalZone(electrical_zone_id="electrical-zone-1", name="Electrical Zone 1", floor_id="floor-1", load_percentage=42.0),
            ElectricalZone(electrical_zone_id="electrical-zone-2", name="Electrical Zone 2", floor_id="floor-2", load_percentage=38.0),
            ElectricalZone(electrical_zone_id="electrical-zone-3", name="Electrical Zone 3", floor_id="floor-3", load_percentage=35.0),
        ],
    )