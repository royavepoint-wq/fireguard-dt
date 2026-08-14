import { Billboard, Text } from "@react-three/drei";

import type { ResponseVisualState } from "@/components/3d/types";

type ResponseMarkerProps = {
  marker: ResponseVisualState;
  opacity: number;
};

function colorForTone(tone: ResponseVisualState["tone"]) {
  if (tone === "critical") {
    return "#ff5468";
  }
  if (tone === "warning") {
    return "#ffae42";
  }
  return "#39d98a";
}

export function ResponseMarker({ marker, opacity }: ResponseMarkerProps) {
  const color = colorForTone(marker.tone);

  return (
    <group position={[marker.position.x, marker.position.y, marker.position.z]}>
      <mesh rotation={[Math.PI, 0, 0]}>
        <coneGeometry args={[0.26, 0.7, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.16} transparent opacity={opacity} />
      </mesh>
      <Billboard position={[0, 0.8, 0]}>
        <Text fontSize={0.28} color={color} anchorX="center" anchorY="middle">
          {marker.label}
        </Text>
      </Billboard>
    </group>
  );
}