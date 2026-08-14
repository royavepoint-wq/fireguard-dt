import { Panel } from "@/components/ui/Panel";
import type { DeveloperActionName } from "@/lib/useDigitalTwinRuntime";

type DeveloperControlsPanelProps = {
  activeAction: DeveloperActionName | null;
  onRunAction: (action: DeveloperActionName) => void;
};

export function DeveloperControlsPanel({ activeAction, onRunAction }: DeveloperControlsPanelProps) {
  return (
    <Panel title="Debug Controls" subtitle="Manual actions that visibly update the shared 3D spatial layer">
      <div className="grid gap-3">
        <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => onRunAction("increase-temperature")}>Increase Fire Twin Temperature</button>
        <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => onRunAction("set-smoke-warning")}>Set Smoke Warning</button>
        <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => onRunAction("block-exit-b")}>Block Exit B</button>
        <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => onRunAction("increase-occupancy")}>Increase Occupancy</button>
        <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => onRunAction("assign-crew-1")}>Assign Crew 1</button>
        <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => onRunAction("reset-all")}>Reset All</button>
      </div>
      {activeAction ? <p className="mt-3 text-sm text-[var(--fg-muted)]">Applying spatial test action...</p> : null}
    </Panel>
  );
}