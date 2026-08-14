import type { FloorLayout, SpatialLayerVisibility } from "@/components/3d/types";

type SceneControlsProps = {
  floors: FloorLayout[];
  selectedFloorId: string | null;
  exploded: boolean;
  layerVisibility: SpatialLayerVisibility;
  autoRotate: boolean;
  onSelectBuilding: () => void;
  onSelectFloor: (floorId: string) => void;
  onToggleExploded: () => void;
  onToggleLayer: (layer: keyof SpatialLayerVisibility) => void;
  onToggleAutoRotate: () => void;
  onResetCamera: () => void;
  cameraPreset: "overview" | "incident" | "evacuation" | "response";
  onSelectCameraPreset: (preset: "overview" | "incident" | "evacuation" | "response") => void;
};

export function SceneControls({
  floors,
  selectedFloorId,
  exploded,
  layerVisibility,
  autoRotate,
  onSelectBuilding,
  onSelectFloor,
  onToggleExploded,
  onToggleLayer,
  onToggleAutoRotate,
  onResetCamera,
  cameraPreset,
  onSelectCameraPreset,
}: SceneControlsProps) {
  return (
    <div className="spatial-toolbar">
      <div className="spatial-toolbar-group">
        <button type="button" className={selectedFloorId === null ? "filter-btn filter-btn-active" : "filter-btn"} onClick={onSelectBuilding}>Building</button>
        {floors.map((floor) => (
          <button
            key={floor.id}
            type="button"
            className={selectedFloorId === floor.id ? "filter-btn filter-btn-active" : "filter-btn"}
            onClick={() => onSelectFloor(floor.id)}
          >
            {floor.name}
          </button>
        ))}
        <button type="button" className={exploded ? "filter-btn filter-btn-active" : "filter-btn"} onClick={onToggleExploded}>Exploded</button>
      </div>

      <div className="spatial-toolbar-group">
        <button type="button" className={layerVisibility.occupants ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onToggleLayer("occupants")}>Occupants</button>
        <button type="button" className={layerVisibility.hazards ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onToggleLayer("hazards")}>Hazards</button>
        <button type="button" className={layerVisibility.routes ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onToggleLayer("routes")}>Routes</button>
        <button type="button" className={layerVisibility.resources ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onToggleLayer("resources")}>Resources</button>
        <button type="button" className={cameraPreset === "overview" ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onSelectCameraPreset("overview")}>Overview</button>
        <button type="button" className={cameraPreset === "incident" ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onSelectCameraPreset("incident")}>Incident</button>
        <button type="button" className={cameraPreset === "evacuation" ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onSelectCameraPreset("evacuation")}>Evacuation</button>
        <button type="button" className={cameraPreset === "response" ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => onSelectCameraPreset("response")}>Response</button>
        <button type="button" className={autoRotate ? "filter-btn filter-btn-active" : "filter-btn"} onClick={onToggleAutoRotate}>Auto Rotate</button>
        <button type="button" className="filter-btn" onClick={onResetCamera}>Reset Camera</button>
      </div>
    </div>
  );
}