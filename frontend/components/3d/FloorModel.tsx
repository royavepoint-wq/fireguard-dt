import type {
  CorridorLayout,
  ExitLayout,
  FloorLayout,
  MappedSpatialState,
  RoomLayout,
  SpatialEntity,
} from "@/components/3d/types";
import { CorridorModel } from "@/components/3d/CorridorModel";
import { ExitModel } from "@/components/3d/ExitModel";
import { HazardOverlay } from "@/components/3d/HazardOverlay";
import { OccupantMarker } from "@/components/3d/OccupantMarker";
import { ResponseMarker } from "@/components/3d/ResponseMarker";
import { RoomModel } from "@/components/3d/RoomModel";
import { RouteOverlay } from "@/components/3d/RouteOverlay";
import type { SpatialLayerVisibility } from "@/components/3d/types";

type FloorModelProps = {
  floor: FloorLayout;
  elevation: number;
  entities: SpatialEntity[];
  spatialState: MappedSpatialState;
  layerVisibility: SpatialLayerVisibility;
  opacity: number;
  isSelectedFloor: boolean;
  selectedRoomId: string | null;
  onSelectRoom: (roomId: string) => void;
};

export function FloorModel({
  floor,
  elevation,
  entities,
  spatialState,
  layerVisibility,
  opacity,
  isSelectedFloor,
  selectedRoomId,
  onSelectRoom,
}: FloorModelProps) {
  return (
    <group>
      <mesh receiveShadow position={[0, elevation - 0.06, 0]}>
        <boxGeometry args={[floor.slabSize.width, 0.12, floor.slabSize.depth]} />
        <meshStandardMaterial color="#0a2137" transparent opacity={Math.max(0.22, opacity * 0.9)} />
      </mesh>

      {entities.map((entity) => {
        if (entity.type === "room") {
          const roomState = spatialState.roomStates[entity.id];
          return (
            <group key={entity.id}>
              <RoomModel
                room={entity as RoomLayout}
                roomState={roomState}
                floorY={elevation}
                opacity={opacity}
                isSelected={selectedRoomId === entity.id}
                onSelectRoom={onSelectRoom}
              />
              {layerVisibility.hazards
                ? spatialState.hazards
                    .filter((hazard) => hazard.entityId === entity.id)
                    .map((hazard) => (
                      <HazardOverlay
                        key={hazard.id}
                        entity={entity as RoomLayout}
                        hazard={hazard}
                        floorY={elevation}
                        opacity={opacity}
                      />
                    ))
                : null}
            </group>
          );
        }

        if (entity.type === "corridor") {
          return (
            <group key={entity.id}>
              <CorridorModel corridor={entity as CorridorLayout} corridorState={spatialState.corridorStates[entity.id]} floorY={elevation} opacity={opacity} />
              {layerVisibility.hazards
                ? spatialState.hazards
                    .filter((hazard) => hazard.entityId === entity.id)
                    .map((hazard) => (
                      <HazardOverlay
                        key={hazard.id}
                        entity={entity as CorridorLayout}
                        hazard={hazard}
                        floorY={elevation}
                        opacity={opacity}
                      />
                    ))
                : null}
            </group>
          );
        }

        if (entity.type === "exit") {
          return <ExitModel key={entity.id} exitEntity={entity as ExitLayout} exitState={spatialState.exitStates[entity.id]} floorY={elevation} opacity={opacity} />;
        }

        if (entity.type === "stair") {
          return (
            <mesh key={entity.id} position={[entity.position.x, elevation + entity.position.y, entity.position.z]} castShadow receiveShadow>
              <boxGeometry args={[entity.size.width, entity.size.height, entity.size.depth]} />
              <meshStandardMaterial color="#33546d" transparent opacity={opacity * 0.92} />
            </mesh>
          );
        }

        return null;
      })}

      {layerVisibility.occupants
        ? spatialState.occupants
            .filter((marker) => marker.floorId === floor.id)
            .map((marker) => (
              <OccupantMarker key={marker.id} marker={marker} opacity={opacity} />
            ))
        : null}

      {layerVisibility.resources
        ? spatialState.resources
            .filter((marker) => marker.floorId === floor.id)
            .map((marker) => (
              <ResponseMarker key={marker.id} marker={marker} opacity={opacity} />
            ))
        : null}

      {layerVisibility.routes && isSelectedFloor
        ? spatialState.routes
            .filter((route) => route.floorId === floor.id && route.points.length > 1)
            .map((route) => (
              <RouteOverlay key={route.routeId} route={route} floorY={elevation} opacity={opacity} />
            ))
        : null}
    </group>
  );
}