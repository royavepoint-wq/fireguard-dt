import { Panel } from "@/components/ui/Panel";
import type { SpatialRoomInfo } from "@/components/3d/types";

type RoomInfoPanelProps = {
  roomInfo: SpatialRoomInfo | null;
  variant?: "compact" | "full";
};

export function RoomInfoPanel({ roomInfo, variant = "full" }: RoomInfoPanelProps) {
  return (
    <Panel title="Room Information" subtitle="Live room and zone data derived from shared backend twin state">
      {roomInfo ? (
        <dl className={variant === "full" ? "detail-grid" : "space-y-3"}>
          <div className="kv-item"><dt>Room</dt><dd>{roomInfo.name}</dd></div>
          <div className="kv-item"><dt>Floor</dt><dd>{roomInfo.floorName}</dd></div>
          <div className="kv-item"><dt>Room ID</dt><dd>{roomInfo.roomId}</dd></div>
          <div className="kv-item"><dt>Status</dt><dd>{roomInfo.status}</dd></div>
          <div className="kv-item"><dt>Temperature</dt><dd>{roomInfo.temperature}</dd></div>
          <div className="kv-item"><dt>Smoke</dt><dd>{roomInfo.smoke}</dd></div>
          <div className="kv-item"><dt>CO</dt><dd>{roomInfo.co}</dd></div>
          <div className="kv-item"><dt>Fire Risk</dt><dd>{roomInfo.fireRisk}</dd></div>
          <div className="kv-item"><dt>Occupancy</dt><dd>{roomInfo.occupancy}</dd></div>
          <div className="kv-item"><dt>Density</dt><dd>{roomInfo.density}</dd></div>
          <div className="kv-item"><dt>Vulnerable Count</dt><dd>{roomInfo.vulnerableCount}</dd></div>
          <div className="kv-item"><dt>Evacuation Status</dt><dd>{roomInfo.evacuationStatus}</dd></div>
          <div className="kv-item"><dt>HVAC Zone</dt><dd>{roomInfo.hvacZone}</dd></div>
          <div className="kv-item"><dt>Sprinkler</dt><dd>{roomInfo.sprinkler}</dd></div>
        </dl>
      ) : (
        <p className="text-sm text-[var(--fg-muted)]">Select a room in the 3D scene to inspect mapped twin state.</p>
      )}
    </Panel>
  );
}