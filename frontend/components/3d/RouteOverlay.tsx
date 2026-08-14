import { Line, Text } from "@react-three/drei";

import type { RouteVisualState } from "@/components/3d/types";

type RouteOverlayProps = {
  route: RouteVisualState;
  floorY: number;
  opacity: number;
};

function routeColor(tone: RouteVisualState["tone"]) {
  if (tone === "blocked") {
    return "#ff5468";
  }
  if (tone === "warning") {
    return "#ffae42";
  }
  return "#39d98a";
}

export function RouteOverlay({ route, floorY, opacity }: RouteOverlayProps) {
  if (!route.visible) {
    return null;
  }

  const points = route.points.map((point) => [point.x, floorY + point.y + 0.08, point.z] as [number, number, number]);
  const labelPoint = route.points[1] ?? route.points[0];

  return (
    <group>
      <Line points={points} color={routeColor(route.tone)} lineWidth={2.8} transparent opacity={opacity} />
      <Text position={[labelPoint.x, floorY + labelPoint.y + 0.5, labelPoint.z]} fontSize={0.28} color={routeColor(route.tone)} anchorX="center" anchorY="middle">
        {route.label}
      </Text>
    </group>
  );
}