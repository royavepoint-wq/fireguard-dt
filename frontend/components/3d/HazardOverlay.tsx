"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type { Mesh } from "three";

import type { CorridorLayout, HazardVisualState, RoomLayout } from "@/components/3d/types";

type HazardOverlayProps = {
  entity: RoomLayout | CorridorLayout;
  hazard: HazardVisualState;
  floorY: number;
  opacity: number;
};

function colorForTone(tone: HazardVisualState["tone"]) {
  if (tone === "critical") {
    return "#ff5468";
  }
  return "#ffae42";
}

export function HazardOverlay({ entity, hazard, floorY, opacity }: HazardOverlayProps) {
  const meshRef = useRef<Mesh | null>(null);

  useFrame((state) => {
    if (!meshRef.current || !hazard.visible) {
      return;
    }
    const material = meshRef.current.material as { opacity?: number };
    const pulse = 0.22 + ((Math.sin(state.clock.elapsedTime * 2.3) + 1) / 2) * 0.22;
    material.opacity = pulse * opacity;
  });

  if (!hazard.visible) {
    return null;
  }

  if (hazard.kind === "smoke") {
    return (
      <mesh ref={meshRef} position={[entity.position.x, floorY + entity.position.y + 0.8, entity.position.z]}>
        <sphereGeometry args={[Math.max(entity.size.width, entity.size.depth) * 0.24, 24, 24]} />
        <meshStandardMaterial color="#9db3c9" transparent opacity={opacity * 0.22} emissive="#9db3c9" emissiveIntensity={0.08} />
      </mesh>
    );
  }

  return (
    <mesh ref={meshRef} position={[entity.position.x, floorY + entity.position.y + entity.size.height + 0.08, entity.position.z]}>
      <boxGeometry args={[entity.size.width * 1.06, 0.14, entity.size.depth * 1.06]} />
      <meshStandardMaterial color={colorForTone(hazard.tone)} transparent opacity={opacity * 0.3} emissive={colorForTone(hazard.tone)} emissiveIntensity={0.28} />
    </mesh>
  );
}