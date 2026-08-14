"use client";

import { useEffect, useRef, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Text } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

import { BuildingModel } from "@/components/3d/BuildingModel";
import { RoomInfoPanel } from "@/components/3d/RoomInfoPanel";
import { SceneControls } from "@/components/3d/SceneControls";
import { SceneLegend } from "@/components/3d/SceneLegend";
import { buildingLayout } from "@/data/building-layout";
import { defaultSpatialLayerVisibility, mapDigitalTwinStateToSpatialState, mergeLayerVisibility } from "@/lib/spatial-mapper";
import type { CombinedDigitalTwinState } from "@/lib/types";

type BuildingSceneProps = {
  systemState: CombinedDigitalTwinState | null;
  loading: boolean;
  error: string | null;
  variant?: "compact" | "full";
};

type CameraRigProps = {
  selectedFloorId: string | null;
  exploded: boolean;
  autoRotate: boolean;
  resetToken: number;
  cameraPreset: "overview" | "incident" | "evacuation" | "response";
};

function CameraRig({ selectedFloorId, exploded, autoRotate, resetToken, cameraPreset }: CameraRigProps) {
  const { camera } = useThree();
  const controlsRef = useRef<OrbitControlsImpl | null>(null);

  useEffect(() => {
    const presets = {
      overview: { position: [16, 14, 16], target: [0, 2.2, 0] },
      incident: { position: [8, 8.5, 3.5], target: [2.5, 2.2, 1.5] },
      evacuation: { position: [11, 10, 10], target: [0.5, 2.2, 0] },
      response: { position: [14, 8.5, -2], target: [-2.5, 1.5, -1.2] },
    } as const;
    const preset = presets[cameraPreset];
    const floor = buildingLayout.floors.find((item) => item.id === selectedFloorId) ?? null;
    const floorYOffset = floor ? floor.elevation + (exploded ? (floor.level - 1) * 2.5 : 0) : preset.target[1];
    camera.position.set(preset.position[0], preset.position[1] + (floor ? floorYOffset - preset.target[1] : 0), preset.position[2]);
    controlsRef.current?.target.set(preset.target[0], floorYOffset, preset.target[2]);
    controlsRef.current?.update();
  }, [camera, cameraPreset, exploded, resetToken, selectedFloorId]);

  return <OrbitControls ref={controlsRef} enablePan autoRotate={autoRotate} autoRotateSpeed={0.28} minDistance={8} maxDistance={34} maxPolarAngle={Math.PI / 2.05} />;
}

function CanvasContents({
  systemState,
  selectedFloorId,
  exploded,
  layerVisibility,
  selectedRoomId,
  onSelectRoom,
  autoRotate,
  resetToken,
  cameraPreset,
}: {
  systemState: CombinedDigitalTwinState | null;
  selectedFloorId: string | null;
  exploded: boolean;
  layerVisibility: ReturnType<typeof mergeLayerVisibility>;
  selectedRoomId: string | null;
  onSelectRoom: (roomId: string) => void;
  autoRotate: boolean;
  resetToken: number;
  cameraPreset: "overview" | "incident" | "evacuation" | "response";
}) {
  const spatialState = mapDigitalTwinStateToSpatialState(systemState);

  return (
    <>
      <color attach="background" args={["#07111d"]} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[10, 18, 10]} intensity={1.1} />
      <directionalLight position={[-8, 10, -6]} intensity={0.35} />
      <gridHelper args={[32, 32, "#214e70", "#16324b"]} position={[0, -0.06, 0]} />
      <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.08, 0]}>
        <planeGeometry args={[42, 42]} />
        <meshStandardMaterial color="#061425" transparent opacity={0.42} />
      </mesh>
      <BuildingModel
        spatialState={spatialState}
        selectedFloorId={selectedFloorId}
        exploded={exploded}
        layerVisibility={layerVisibility}
        selectedRoomId={selectedRoomId}
        onSelectRoom={onSelectRoom}
      />
      <Text position={[0, 12.2, 0]} fontSize={0.72} color="#8bdfff" anchorX="center" anchorY="middle">
        FG-BLDG-01
      </Text>
      <CameraRig selectedFloorId={selectedFloorId} exploded={exploded} autoRotate={autoRotate} resetToken={resetToken} cameraPreset={cameraPreset} />
    </>
  );
}

export function BuildingScene({ systemState, loading, error, variant = "full" }: BuildingSceneProps) {
  const [selectedFloorId, setSelectedFloorId] = useState<string | null>(null);
  const [exploded, setExploded] = useState(false);
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>("room-electrical-01");
  const [layerVisibility, setLayerVisibility] = useState(defaultSpatialLayerVisibility);
  const [autoRotate, setAutoRotate] = useState(false);
  const [resetToken, setResetToken] = useState(0);
  const [cameraPreset, setCameraPreset] = useState<"overview" | "incident" | "evacuation" | "response">("overview");

  const spatialState = mapDigitalTwinStateToSpatialState(systemState);
  const activeRoomId = selectedRoomId && spatialState.roomStates[selectedRoomId]
    ? selectedRoomId
    : spatialState.roomStates["room-electrical-01"]
      ? "room-electrical-01"
      : null;

  const selectedRoomInfo = activeRoomId ? spatialState.roomStates[activeRoomId]?.info ?? null : null;

  function handleSelectFloor(floorId: string) {
    setSelectedFloorId(floorId);
    const roomOnFloor = buildingLayout.entities.find((entity) => entity.type === "room" && entity.floorId === floorId);
    if (roomOnFloor) {
      setSelectedRoomId(roomOnFloor.id);
    }
  }

  function handleSelectBuilding() {
    setSelectedFloorId(null);
    if (spatialState.roomStates["room-electrical-01"]) {
      setSelectedRoomId("room-electrical-01");
    }
  }

  return (
    <div className={variant === "full" ? "min-w-0 space-y-4" : "min-w-0 space-y-3"}>
      <SceneControls
        floors={buildingLayout.floors}
        selectedFloorId={selectedFloorId}
        exploded={exploded}
        layerVisibility={layerVisibility}
        autoRotate={autoRotate}
        onSelectBuilding={handleSelectBuilding}
        onSelectFloor={handleSelectFloor}
        onToggleExploded={() => setExploded((value) => !value)}
        onToggleLayer={(layer) => setLayerVisibility((current) => ({ ...current, [layer]: !current[layer] }))}
        onToggleAutoRotate={() => setAutoRotate((value) => !value)}
        onResetCamera={() => setResetToken((value) => value + 1)}
        cameraPreset={cameraPreset}
        onSelectCameraPreset={(preset) => {
          setCameraPreset(preset);
          setResetToken((value) => value + 1);
        }}
      />

      <div className={variant === "full" ? "grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.8fr)_360px]" : "space-y-3"}>
        <div className="spatial-scene-card">
          {error ? <div className="spatial-banner">API Offline. Rendering spatial shell with last-known or baseline layout.</div> : null}
          {loading ? <div className="spatial-banner">Loading shared 3D spatial state...</div> : null}
          <div className={variant === "full" ? "spatial-canvas spatial-canvas-full" : "spatial-canvas spatial-canvas-compact"}>
            <Canvas camera={{ position: [16, 14, 16], fov: 42 }}>
              <CanvasContents
                systemState={systemState}
                selectedFloorId={selectedFloorId}
                exploded={exploded}
                layerVisibility={mergeLayerVisibility(layerVisibility)}
                selectedRoomId={selectedRoomId}
                onSelectRoom={setSelectedRoomId}
                autoRotate={autoRotate}
                resetToken={resetToken}
                cameraPreset={cameraPreset}
              />
            </Canvas>
            <SceneLegend />
            <div className="pointer-events-none absolute left-3 top-3 rounded-xl border border-white/15 bg-[var(--bg-deep)]/70 px-3 py-2 text-xs text-white">
              <p className="font-semibold">Electrical Room Fire</p>
              <p className="text-[var(--fg-muted)]">Phase: {systemState?.fire_twin.risk_level ?? "NORMAL"} | Risk: {Math.round((systemState?.fire_twin.fire_risk_probability ?? 0) * 100)}%</p>
            </div>
          </div>
        </div>

        <RoomInfoPanel roomInfo={selectedRoomInfo} variant={variant} />
      </div>
    </div>
  );
}