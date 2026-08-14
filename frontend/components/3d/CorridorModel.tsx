import { Billboard, Text } from "@react-three/drei";

import type { CorridorLayout, CorridorVisualState } from "@/components/3d/types";

type CorridorModelProps = {
  corridor: CorridorLayout;
  corridorState: CorridorVisualState | undefined;
  floorY: number;
  opacity: number;
};

function colorForTone(tone: CorridorVisualState["tone"] | undefined) {
  if (tone === "critical") {
    return "#b02a3a";
  }
  if (tone === "warning") {
    return "#9b6724";
  }
  return "#223f57";
}

export function CorridorModel({ corridor, corridorState, floorY, opacity }: CorridorModelProps) {
  return (
    <group>
      <mesh position={[corridor.position.x, floorY + corridor.position.y, corridor.position.z]} receiveShadow>
        <boxGeometry args={[corridor.size.width, corridor.size.height, corridor.size.depth]} />
        <meshStandardMaterial color={colorForTone(corridorState?.tone)} transparent opacity={opacity * 0.88} />
      </mesh>
      {corridor.id === "corridor-c" ? (
        <Billboard position={[corridor.position.x, floorY + corridor.position.y + 0.35, corridor.position.z]}>
          <Text fontSize={0.24} color="#9fd8ff" anchorX="center" anchorY="middle">
            {corridor.name}
          </Text>
        </Billboard>
      ) : null}
    </group>
  );
}