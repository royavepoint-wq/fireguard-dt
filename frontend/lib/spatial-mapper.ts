import { buildingLayout } from "@/data/building-layout";
import type {
  BuildingLayout,
  FloorPresentation,
  MappedSpatialState,
  SpatialLayerVisibility,
  SpatialTone,
} from "@/components/3d/types";
import type { CombinedDigitalTwinState, ResourceStatus, RiskLevel } from "@/lib/types";

export const defaultSpatialLayerVisibility: SpatialLayerVisibility = {
  occupants: true,
  hazards: true,
  routes: true,
  resources: true,
};

function toneFromRiskLevel(riskLevel: RiskLevel): SpatialTone {
  if (riskLevel === "CRITICAL") {
    return "critical";
  }
  if (riskLevel === "WARNING") {
    return "warning";
  }
  return "safe";
}

function toneFromResourceStatus(status: ResourceStatus): SpatialTone {
  if (status === "UNAVAILABLE") {
    return "critical";
  }
  return "safe";
}

function routeToneFromStatus(status: string | undefined) {
  if (status === "NO_SAFE_ROUTE") {
    return "blocked" as const;
  }
  if (status === "BLOCKED") {
    return "blocked" as const;
  }
  if (status === "CONGESTED") {
    return "warning" as const;
  }
  return "safe" as const;
}

export function getFloorPresentation(
  layout: BuildingLayout,
  selectedFloorId: string | null,
  exploded: boolean,
): FloorPresentation[] {
  return layout.floors.map((floor) => ({
    floorId: floor.id,
    elevation: floor.elevation + (exploded ? (floor.level - 1) * 2.5 : 0),
    isFocused: selectedFloorId === null || selectedFloorId === floor.id,
    isDimmed: selectedFloorId !== null && selectedFloorId !== floor.id,
  }));
}

export function mergeLayerVisibility(
  overrides?: Partial<SpatialLayerVisibility>,
): SpatialLayerVisibility {
  return {
    ...defaultSpatialLayerVisibility,
    ...overrides,
  };
}

export function mapDigitalTwinStateToSpatialState(
  systemState: CombinedDigitalTwinState | null,
  layout: BuildingLayout = buildingLayout,
): MappedSpatialState {
  const roomStates: MappedSpatialState["roomStates"] = {};
  const corridorStates: MappedSpatialState["corridorStates"] = {};
  const exitStates: MappedSpatialState["exitStates"] = {};
  const hazards: MappedSpatialState["hazards"] = [];
  const occupants: MappedSpatialState["occupants"] = [];
  const resources: MappedSpatialState["resources"] = [];
  const routes: MappedSpatialState["routes"] = [];

  const floorNameById = new Map(layout.floors.map((floor) => [floor.id, floor.name]));
  const occupancyZoneById = new Map(systemState?.occupancy_twin.zones.map((zone) => [zone.zone_id, zone]) ?? []);
  const routeById = new Map(systemState?.occupancy_twin.active_routes.map((route) => [route.route_id, route]) ?? []);
  const exitById = new Map(systemState?.building_twin.exits.map((exitItem) => [exitItem.exit_id, exitItem]) ?? []);
  const sprinklerByZone = new Map(systemState?.building_twin.sprinklers.map((sprinkler) => [sprinkler.zone_id, sprinkler]) ?? []);
  const hvacByFloor = new Map(systemState?.building_twin.hvac_zones.map((zone) => [zone.floor_id, zone]) ?? []);
  const riskTone = systemState ? toneFromRiskLevel(systemState.fire_twin.risk_level) : "safe";
  const hasSensorAnomaly = systemState ? systemState.fire_twin.sensor_health !== "HEALTHY" : false;

  for (const entity of layout.entities) {
    if (entity.type === "room") {
      const occupancy = entity.zoneId ? occupancyZoneById.get(entity.zoneId) : undefined;
      const isHazardRoom = Boolean(
        systemState && (entity.zoneId === systemState.fire_twin.zone_id || entity.id === systemState.fire_twin.zone_id || entity.roomId === systemState.fire_twin.zone_id),
      );
      let roomTone: SpatialTone = "muted";
      if (isHazardRoom) {
        if (systemState?.fire_twin.risk_level === "CRITICAL") {
          roomTone = "critical";
        } else if (systemState?.fire_twin.risk_level === "WARNING") {
          roomTone = "warning";
        } else if (hasSensorAnomaly) {
          roomTone = "safe";
        }
      }
      const sprinkler = entity.zoneId ? sprinklerByZone.get(entity.zoneId) : undefined;
      const hvacZone = hvacByFloor.get(entity.floorId);

      roomStates[entity.id] = {
        roomId: entity.id,
        tone: roomTone,
        label: entity.name,
        isSelectedHazardRoom: isHazardRoom,
        info: {
          roomId: entity.roomId ?? entity.id,
          name: entity.name,
          floorId: entity.floorId,
          floorName: floorNameById.get(entity.floorId) ?? entity.floorId,
          zoneId: entity.zoneId ?? null,
          status: isHazardRoom ? systemState?.fire_twin.risk_level ?? "NORMAL" : occupancy?.evacuation_status ?? "NORMAL",
          tone: roomTone,
          temperature: isHazardRoom && systemState ? `${systemState.fire_twin.temperature.toFixed(1)}°C` : "N/A",
          smoke: isHazardRoom && systemState ? systemState.fire_twin.smoke_level.toFixed(2) : "N/A",
          co: isHazardRoom && systemState ? systemState.fire_twin.co_level.toFixed(1) : "N/A",
          fireRisk: isHazardRoom && systemState ? `${Math.round(systemState.fire_twin.fire_risk_probability * 100)}%` : "N/A",
          occupancy: occupancy ? String(occupancy.occupancy_count) : "N/A",
          density: occupancy ? occupancy.density.toFixed(2) : "N/A",
          vulnerableCount: occupancy ? String(occupancy.vulnerable_count) : "N/A",
          evacuationStatus: occupancy?.evacuation_status ?? "N/A",
          hvacZone: hvacZone?.name ?? "N/A",
          sprinkler: sprinkler ? sprinkler.status : "N/A",
        },
      };

      if (occupancy && entity.zoneId) {
        occupants.push({
          id: `occupancy-${entity.id}`,
          zoneId: entity.zoneId,
          roomId: entity.id,
          floorId: entity.floorId,
          count: occupancy.occupancy_count,
          density: occupancy.density,
          label: `${occupancy.occupancy_count}`,
          tone: "safe",
          position: {
            x: entity.position.x,
            y: entity.position.y + 0.9,
            z: entity.position.z,
          },
        });
      }
    }

    if (entity.type === "corridor") {
      const backendCorridor = systemState?.building_twin.corridors.find((corridor) => corridor.corridor_id === entity.id);
      const showSmoke = Boolean(systemState && entity.id === "corridor-c" && systemState.fire_twin.smoke_level >= 0.1);
      const tone = backendCorridor?.is_accessible === false ? "critical" : showSmoke ? riskTone : "muted";
      corridorStates[entity.id] = {
        corridorId: entity.id,
        tone,
      };

      hazards.push({
        id: `hazard-risk-${entity.id}`,
        entityId: entity.id,
        kind: "risk",
        tone,
        visible: Boolean(systemState && entity.id === "corridor-c" && systemState.fire_twin.risk_level !== "NORMAL"),
      });

      hazards.push({
        id: `hazard-smoke-${entity.id}`,
        entityId: entity.id,
        kind: "smoke",
        tone,
        visible: showSmoke,
      });
    }

    if (entity.type === "exit") {
      const exitState = exitById.get(entity.exitId);
      const blocked = Boolean(exitState?.is_blocked);
      exitStates[entity.id] = {
        exitId: entity.exitId,
        tone: blocked ? "critical" : "safe",
        label: blocked ? "BLOCKED" : "AVAILABLE",
        blocked,
      };
    }

    if (entity.type === "resource-node" && systemState) {
      const source = entity.resourceKind === "crew"
        ? systemState.response_twin.crews.find((crew) => crew.crew_id === entity.resourceId)
        : systemState.response_twin.drones.find((drone) => drone.drone_id === entity.resourceId);
      if (!source) {
        console.warn(`Missing spatial resource mapping for ${entity.resourceKind} ${entity.resourceId}`);
        continue;
      }
      resources.push({
        id: entity.id,
        resourceId: entity.resourceId,
        kind: entity.resourceKind,
        floorId: entity.floorId,
        label: source.name,
        status: source.status,
        tone: toneFromResourceStatus(source.status),
        position: {
          x: entity.position.x,
          y: entity.position.y + 0.65,
          z: entity.position.z,
        },
      });
    }
  }

  if ((systemState?.occupancy_twin.active_routes.length ?? 0) > 0) {
    for (const routeState of systemState?.occupancy_twin.active_routes ?? []) {
      const tone = routeToneFromStatus(routeState.status);
      const dynamicPoints = (routeState.path_coordinates ?? []).map((point) => ({ x: point.x, y: point.y, z: point.z }));
      const fallbackRoute = layout.routes.find((route) => route.id === routeState.route_id);
      const points = dynamicPoints.length > 1 ? dynamicPoints : (fallbackRoute?.points ?? []);
      const floorId = routeState.path_coordinates?.[0]?.floor_id ?? fallbackRoute?.floorId ?? "floor-1";
      const label = routeState.strategy ? routeState.strategy.replaceAll("_", " ") : routeState.route_id;

      routes.push({
        routeId: routeState.route_id,
        label,
        floorId,
        tone,
        points,
        visible: routeState.status !== "NO_SAFE_ROUTE" && points.length > 1,
      });
    }
  } else {
    for (const route of layout.routes) {
      const routeState = routeById.get(route.id);
      const tone = routeToneFromStatus(routeState?.status);
      routes.push({
        routeId: route.id,
        label: route.name,
        floorId: route.floorId,
        tone,
        points: route.points,
        visible: routeState ? routeState.status === "OPEN" || route.defaultVisible : route.defaultVisible,
      });
    }
  }

  const activeHazardZones = new Set(
    hazards.filter((hazard) => hazard.visible).map((hazard) => hazard.entityId),
  ).size;
  const blockedExits = Object.values(exitStates).filter((exitState) => exitState.blocked).length;

  return {
    roomStates,
    corridorStates,
    exitStates,
    hazards,
    occupants,
    resources,
    routes,
    summary: {
      buildingStatus: systemState?.building_twin.status ?? "OFFLINE",
      floors: layout.floors.length,
      activeHazardZones,
      blockedExits,
      occupancy: systemState?.occupancy_twin.total_occupancy ?? 0,
      activeEvacuations: systemState?.occupancy_twin.evacuating_count ?? 0,
      responseResources: systemState ? systemState.response_twin.crews.length + systemState.response_twin.drones.length : 0,
    },
  };
}