import { Billboard, Text } from "@react-three/drei";

import type { OccupantVisualState } from "@/components/3d/types";

type OccupantMarkerProps = {
  marker: OccupantVisualState;
  opacity: number;
};

function markerColor(tone: OccupantVisualState["tone"]) {
  void tone;
  return "#8bdfff";
}

export function OccupantMarker({ marker, opacity }: OccupantMarkerProps) {
  return (
    <group position={[marker.position.x, marker.position.y, marker.position.z]}>
      <mesh>
        <sphereGeometry args={[0.28, 16, 16]} />
        <meshStandardMaterial color="#39d8ff" emissive="#39d8ff" emissiveIntensity={0.25} transparent opacity={opacity} />
      </mesh>
      <mesh position={[-0.38, 0, 0]}>
        <sphereGeometry args={[0.18, 14, 14]} />
        <meshStandardMaterial color="#0fb1d7" transparent opacity={opacity * 0.85} />
      </mesh>
      <mesh position={[0.38, 0, 0]}>
        <sphereGeometry args={[0.18, 14, 14]} />
        <meshStandardMaterial color="#0fb1d7" transparent opacity={opacity * 0.85} />
      </mesh>
      <Billboard position={[0, 0.62, 0]}>
        <Text fontSize={0.4} color={markerColor(marker.tone)} anchorX="center" anchorY="middle">
          {marker.count}
        </Text>
      </Billboard>
    </group>
  );
}