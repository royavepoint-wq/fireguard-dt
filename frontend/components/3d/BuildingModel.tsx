import { buildingLayout } from "@/data/building-layout";
import { FloorModel } from "@/components/3d/FloorModel";
import { getFloorPresentation } from "@/lib/spatial-mapper";
import type { MappedSpatialState, SpatialLayerVisibility } from "@/components/3d/types";

type BuildingModelProps = {
  spatialState: MappedSpatialState;
  selectedFloorId: string | null;
  exploded: boolean;
  layerVisibility: SpatialLayerVisibility;
  selectedRoomId: string | null;
  onSelectRoom: (roomId: string) => void;
};

export function BuildingModel({ spatialState, selectedFloorId, exploded, layerVisibility, selectedRoomId, onSelectRoom }: BuildingModelProps) {
  const presentation = getFloorPresentation(buildingLayout, selectedFloorId, exploded);

  return (
    <group>
      {presentation.map((floorPresentation) => {
        const floor = buildingLayout.floors.find((item) => item.id === floorPresentation.floorId);
        if (!floor) {
          return null;
        }

        return (
          <FloorModel
            key={floor.id}
            floor={floor}
            elevation={floorPresentation.elevation}
            entities={buildingLayout.entities.filter((entity) => entity.floorId === floor.id && entity.type !== "resource-node")}
            spatialState={spatialState}
            layerVisibility={layerVisibility}
            opacity={floorPresentation.isDimmed ? 0.18 : 0.94}
            isSelectedFloor={!floorPresentation.isDimmed}
            selectedRoomId={selectedRoomId}
            onSelectRoom={onSelectRoom}
          />
        );
      })}

      {layerVisibility.resources
        ? presentation.map((floorPresentation) => {
            const floorResourceState = spatialState.resources.filter((resource) => resource.floorId === floorPresentation.floorId);
            if (floorResourceState.length === 0) {
              return null;
            }
            return null;
          })
        : null}
    </group>
  );
}