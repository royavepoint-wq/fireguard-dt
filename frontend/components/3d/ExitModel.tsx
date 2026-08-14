import { Billboard, Text } from "@react-three/drei";

import type { ExitLayout, ExitVisualState } from "@/components/3d/types";

type ExitModelProps = {
  exitEntity: ExitLayout;
  exitState: ExitVisualState | undefined;
  floorY: number;
  opacity: number;
};

export function ExitModel({ exitEntity, exitState, floorY, opacity }: ExitModelProps) {
  const blocked = exitState?.blocked ?? false;

  return (
    <group position={[exitEntity.position.x, floorY + exitEntity.position.y, exitEntity.position.z]}>
      <mesh castShadow>
        <boxGeometry args={[exitEntity.size.width, exitEntity.size.height, exitEntity.size.depth]} />
        <meshStandardMaterial color={blocked ? "#ff5468" : "#39d98a"} transparent opacity={opacity} emissive={blocked ? "#7b1d2d" : "#0a6442"} emissiveIntensity={0.35} />
      </mesh>
      <Billboard position={[0, exitEntity.size.height + 0.55, 0]}>
        <Text fontSize={0.35} color={blocked ? "#ffb8c2" : "#c7ffe3"} anchorX="center" anchorY="middle">
          {exitEntity.name}
        </Text>
      </Billboard>
    </group>
  );
}