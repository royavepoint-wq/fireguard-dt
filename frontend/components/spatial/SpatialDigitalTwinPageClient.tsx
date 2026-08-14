"use client";

import { BuildingScene } from "@/components/3d/BuildingScene";
import { ApiStatusBadge } from "@/components/ui/ApiStatusBadge";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { SimulationControlBar } from "@/components/simulation/SimulationControlBar";
import { SimulationProgressPanel } from "@/components/simulation/SimulationProgressPanel";
import { SimulationRunsPanel } from "@/components/simulation/SimulationRunsPanel";
import { mapDigitalTwinStateToSpatialState } from "@/lib/spatial-mapper";
import { useSimulationRuntime } from "@/lib/useSimulationRuntime";
import { useDigitalTwinRuntime } from "@/lib/useDigitalTwinRuntime";

export function SpatialDigitalTwinPageClient() {
  const { systemState, loading, error, refresh } = useDigitalTwinRuntime({ pollMs: 1000 });
  const {
    simulation,
    runs,
    pending,
    autoApprovePreference,
    setAutoApprovePreference,
    runPresentationDemo,
    runStart,
    runAction,
    changeSpeed,
    runAgain,
  } = useSimulationRuntime({ pollMs: 1000 });
  const spatialState = mapDigitalTwinStateToSpatialState(systemState);

  return (
    <div>
      <PageHeader
        title="Spatial Digital Twin"
        description="Shared 3D building visualization and spatial integration layer for all four domain twins. This is not a fifth twin."
        actions={<ApiStatusBadge />}
      />

      <section className="mb-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]">
        <SimulationControlBar
          simulation={simulation}
          latestRun={runs[0] ?? simulation?.latest_run_summary ?? null}
          pending={pending}
          autoApprovePreference={autoApprovePreference}
          onToggleAutoApproval={() => setAutoApprovePreference((value) => !value)}
          onStartDemo={() => void runPresentationDemo()}
          onStartManual={() => void runStart({ scenario_id: "electrical-room-fire", speed_multiplier: 1, auto_approve: autoApprovePreference, presentation_mode: false })}
          onRunAgain={() => void runAgain()}
          onPause={() => void runAction("pause")}
          onResume={() => void runAction("resume")}
          onStop={() => void runAction("stop")}
          onReset={() => void runAction("reset")}
          onSpeedChange={(speed) => void changeSpeed(speed)}
          onApprove={() => void runAction("approve")}
          onReject={() => void runAction("reject")}
        />
        <SimulationProgressPanel simulation={simulation} latestRun={runs[0] ?? simulation?.latest_run_summary ?? null} fireTwin={systemState?.fire_twin ?? null} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <Panel title="Shared 3D Building Model" subtitle="Perspective digital twin view with floor focus, exploded mode, and live overlays">
          <BuildingScene systemState={systemState} loading={loading} error={error} variant="full" />
        </Panel>

        <div className="space-y-4">
          <Panel title="Spatial State Summary" subtitle="Derived from live backend twin state wherever possible">
            <dl className="space-y-3">
              <div className="system-row"><dt>Building Status</dt><dd>{spatialState.summary.buildingStatus}</dd></div>
              <div className="system-row"><dt>Floors</dt><dd>{spatialState.summary.floors}</dd></div>
              <div className="system-row"><dt>Active Hazard Zones</dt><dd>{spatialState.summary.activeHazardZones}</dd></div>
              <div className="system-row"><dt>Blocked Exits</dt><dd>{spatialState.summary.blockedExits}</dd></div>
              <div className="system-row"><dt>Occupancy</dt><dd>{spatialState.summary.occupancy}</dd></div>
              <div className="system-row"><dt>Active Evacuations</dt><dd>{spatialState.summary.activeEvacuations}</dd></div>
              <div className="system-row"><dt>Response Resources</dt><dd>{spatialState.summary.responseResources}</dd></div>
            </dl>
          </Panel>

          <Panel title="Spatial Mapper" subtitle="Live twin state -> shared spatial IDs -> 3D visualization">
            <p className="text-sm text-[var(--fg-muted)]">
              Four domain twins publish state through shared spatial IDs. The spatial mapper converts that live backend state into room tones, hazard overlays,
              exit availability, occupancy markers, route states, and response staging visuals.
            </p>
            <button type="button" className="action-btn mt-4" onClick={() => void refresh(true)}>Refresh Spatial State</button>
            {error ? <p className="mt-3 text-sm text-[var(--accent-red)]">{error}</p> : null}
          </Panel>

          <Panel title="Response Resource Status" subtitle="Live crew and drone readiness mapped into scene markers">
            <ul className="space-y-2 text-sm">
              {systemState?.response_twin.crews.map((crew) => (
                <li key={crew.crew_id} className="system-row"><span>{crew.name}</span><span>{crew.status}</span></li>
              ))}
              {systemState?.response_twin.drones.map((drone) => (
                <li key={drone.drone_id} className="system-row"><span>{drone.name}</span><span>{drone.status}</span></li>
              ))}
              {!systemState ? <li className="text-sm text-[var(--fg-muted)]">API offline. Resource statuses unavailable.</li> : null}
            </ul>
          </Panel>

          <SimulationRunsPanel runs={runs} />
        </div>
      </section>
    </div>
  );
}