import { describe, expect, it } from "vitest";

import { buildingLayout } from "@/data/building-layout";
import {
  defaultSpatialLayerVisibility,
  getFloorPresentation,
  mapDigitalTwinStateToSpatialState,
  mergeLayerVisibility,
} from "@/lib/spatial-mapper";
import type { CombinedDigitalTwinState } from "@/lib/types";

const baseState: CombinedDigitalTwinState = {
  fire_twin: {
    twin_id: "fire_environment",
    name: "Fire & Environment Twin",
    status: "ONLINE",
    last_updated: "2026-08-13T00:00:00Z",
    building_id: "FG-BLDG-01",
    floor_id: "floor-1",
    zone_id: "zone-1a",
    temperature: 24.6,
    temperature_rate: 0,
    smoke_level: 0.02,
    co_level: 4,
    co2_level: 450,
    humidity: 55,
    electrical_load: 42,
    fire_risk_probability: 0.08,
    risk_level: "NORMAL",
    risk_probabilities: {
      NORMAL: 0.88,
      WARNING: 0.08,
      CRITICAL: 0.04,
    },
    prediction_source: "NOT_AVAILABLE",
    model_version: null,
    prediction_confidence: 0,
    sensor_health: "HEALTHY",
    hvac_effect: 0.15,
  },
  building_twin: {
    twin_id: "building_infrastructure",
    name: "Building Infrastructure Twin",
    status: "ONLINE",
    last_updated: "2026-08-13T00:00:00Z",
    building_id: "FG-BLDG-01",
    floors: [
      { floor_id: "floor-1", name: "Floor 1", level: 1, zone_ids: ["zone-1a", "zone-1b"] },
      { floor_id: "floor-2", name: "Floor 2", level: 2, zone_ids: ["zone-2a", "zone-2b"] },
      { floor_id: "floor-3", name: "Floor 3", level: 3, zone_ids: ["zone-3a"] },
    ],
    rooms: [],
    corridors: [],
    exits: [
      { exit_id: "exit-a", name: "Exit A", floor_id: "floor-1", zone_id: "zone-1b", is_available: true, is_blocked: false },
      { exit_id: "exit-b", name: "Exit B", floor_id: "floor-1", zone_id: "zone-1b", is_available: true, is_blocked: false },
    ],
    hvac_zones: [
      { hvac_zone_id: "hvac-zone-1", name: "HVAC Zone 1", floor_id: "floor-1", status: "NORMAL", airflow_percentage: 100 },
    ],
    sprinklers: [
      { sprinkler_id: "sprinkler-1a", zone_id: "zone-1a", status: "READY", is_active: false },
    ],
    electrical_zones: [],
  },
  occupancy_twin: {
    twin_id: "occupancy_evacuation",
    name: "Occupancy & Evacuation Twin",
    status: "ONLINE",
    last_updated: "2026-08-13T00:00:00Z",
    building_id: "FG-BLDG-01",
    total_occupancy: 243,
    zones: [
      { zone_id: "zone-1a", occupancy_count: 34, density: 0.32, vulnerable_count: 2, evacuation_status: "STABLE" },
      { zone_id: "zone-1b", occupancy_count: 47, density: 0.46, vulnerable_count: 3, evacuation_status: "STABLE" },
      { zone_id: "zone-2a", occupancy_count: 58, density: 0.51, vulnerable_count: 4, evacuation_status: "STABLE" },
      { zone_id: "zone-2b", occupancy_count: 39, density: 0.35, vulnerable_count: 2, evacuation_status: "STABLE" },
      { zone_id: "zone-3a", occupancy_count: 65, density: 0.57, vulnerable_count: 5, evacuation_status: "STABLE" },
    ],
    evacuating_count: 0,
    evacuated_count: 0,
    congestion_level: "LOW",
    active_routes: [],
  },
  response_twin: {
    twin_id: "emergency_response",
    name: "Emergency Response Twin",
    status: "ONLINE",
    last_updated: "2026-08-13T00:00:00Z",
    crews: [
      { crew_id: "crew-1", name: "Crew 1", status: "AVAILABLE", current_zone_id: null, eta_minutes: 0 },
      { crew_id: "crew-2", name: "Crew 2", status: "AVAILABLE", current_zone_id: null, eta_minutes: 0 },
    ],
    drones: [
      { drone_id: "drone-1", name: "Drone 1", status: "AVAILABLE", current_zone_id: null, battery_level: 100, eta_minutes: 0 },
      { drone_id: "drone-2", name: "Drone 2", status: "AVAILABLE", current_zone_id: null, battery_level: 100, eta_minutes: 0 },
    ],
    active_incidents: [],
    dispatch_queue: [],
    average_response_eta: 0,
  },
  orchestrator: {
    status: "NORMAL",
    human_oversight: true,
    active_alerts: [],
    twins_online: 4,
    cross_twin_state: {},
    last_updated: "2026-08-13T00:00:00Z",
  },
};

describe("spatial mapper", () => {
  it("keeps normal building geometry neutral with no active hazard overlays", () => {
    const mapped = mapDigitalTwinStateToSpatialState(baseState);

    expect(mapped.roomStates["room-electrical-01"].tone).toBe("muted");
    expect(mapped.roomStates["room-office-a-01"].tone).toBe("muted");
    expect(mapped.corridorStates["corridor-c"].tone).toBe("muted");
    expect(mapped.hazards.some((hazard) => hazard.visible)).toBe(false);
  });

  it("maps fire warning and smoke risk onto the electrical room and corridor c", () => {
    const mapped = mapDigitalTwinStateToSpatialState({
      ...baseState,
      fire_twin: {
        ...baseState.fire_twin,
        risk_level: "WARNING",
        fire_risk_probability: 0.38,
        smoke_level: 0.35,
      },
      occupancy_twin: {
        ...baseState.occupancy_twin,
        active_routes: [
          { route_id: "route-a", from_zone_id: "zone-1a", to_exit_id: "exit-a", status: "BLOCKED", estimated_capacity: 80 },
          { route_id: "route-b", from_zone_id: "zone-1a", to_exit_id: "exit-b", status: "CONGESTED", estimated_capacity: 65 },
        ],
      },
    });

    expect(mapped.roomStates["room-electrical-01"].tone).toBe("warning");
    expect(mapped.roomStates["room-office-a-01"].tone).toBe("muted");
    expect(mapped.hazards.find((hazard) => hazard.id === "hazard-smoke-corridor-c")?.visible).toBe(true);
    expect(mapped.routes.find((route) => route.routeId === "route-b")?.tone).toBe("warning");
  });

  it("maps blocked exit state to critical visual tone", () => {
    const mapped = mapDigitalTwinStateToSpatialState({
      ...baseState,
      building_twin: {
        ...baseState.building_twin,
        exits: [
          baseState.building_twin.exits[0],
          { ...baseState.building_twin.exits[1], is_available: false, is_blocked: true },
        ],
      },
      occupancy_twin: {
        ...baseState.occupancy_twin,
        active_routes: [
          { route_id: "route-a", from_zone_id: "zone-1a", to_exit_id: "exit-a", status: "OPEN", estimated_capacity: 80 },
          { route_id: "route-b", from_zone_id: "zone-1a", to_exit_id: "exit-b", status: "BLOCKED", estimated_capacity: 65 },
        ],
      },
    });

    expect(mapped.exitStates["exit-b"].blocked).toBe(true);
    expect(mapped.exitStates["exit-b"].tone).toBe("critical");
    expect(mapped.routes.find((route) => route.routeId === "route-b")?.tone).toBe("blocked");
  });

  it("calculates floor presentation for exploded focused mode", () => {
    const presentation = getFloorPresentation(buildingLayout, "floor-2", true);

    expect(presentation[1].isFocused).toBe(true);
    expect(presentation[0].isDimmed).toBe(true);
    expect(presentation[2].elevation).toBeGreaterThan(buildingLayout.floors[2].elevation);
  });

  it("merges scene visibility controls without losing defaults", () => {
    const merged = mergeLayerVisibility({ hazards: false, routes: false });

    expect(defaultSpatialLayerVisibility.occupants).toBe(true);
    expect(merged).toEqual({
      occupants: true,
      hazards: false,
      routes: false,
      resources: true,
    });
  });
});