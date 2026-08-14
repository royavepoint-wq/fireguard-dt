"use client";

import { useState } from "react";
import { Billboard, Html, Text, useCursor } from "@react-three/drei";

import type { RoomLayout, RoomVisualState } from "@/components/3d/types";

type RoomModelProps = {
  room: RoomLayout;
  roomState: RoomVisualState;
  floorY: number;
  opacity: number;
  isSelected: boolean;
  onSelectRoom: (roomId: string) => void;
};

function colorForTone(tone: RoomVisualState["tone"]) {
  if (tone === "critical") {
    return "#ff5468";
  }
  if (tone === "warning") {
    return "#ffae42";
  }
  if (tone === "muted") {
    return "#2f475c";
  }
  return "#3a5f7b";
}

function isImportantRoomLabel(roomId: string) {
  return roomId === "room-electrical-01";
}

export function RoomModel({ room, roomState, floorY, opacity, isSelected, onSelectRoom }: RoomModelProps) {
  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

  return (
    <group position={[room.position.x, floorY + room.position.y, room.position.z]}>
      <mesh
        castShadow
        receiveShadow
        rotation={[0, room.rotation ?? 0, 0]}
        onClick={() => onSelectRoom(room.id)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <boxGeometry args={[room.size.width, room.size.height, room.size.depth]} />
        <meshStandardMaterial
          color={colorForTone(roomState.tone)}
          emissive={isSelected ? "#39d8ff" : "#102435"}
          emissiveIntensity={isSelected ? 0.42 : hovered ? 0.16 : 0.05}
          transparent
          opacity={Math.min(1, opacity + (isSelected ? 0.12 : 0))}
        />
      </mesh>
      {isImportantRoomLabel(room.id) ? (
        <Billboard position={[0, room.size.height + 0.45, 0]}>
          <Text fontSize={0.28} color="#8bdfff" anchorX="center" anchorY="middle">
            {room.name}
          </Text>
        </Billboard>
      ) : null}
      {hovered ? (
        <Html position={[0, room.size.height + 0.6, 0]} center>
          <div className="spatial-tooltip">{room.name}</div>
        </Html>
      ) : null}
    </group>
  );
}