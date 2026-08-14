"use client";

import Link from "next/link";
import { Flame, ShieldCheck, Siren, UsersRound } from "lucide-react";

import { BuildingScene } from "@/components/3d/BuildingScene";
import { ApiStatusBadge } from "@/components/ui/ApiStatusBadge";
import { LiveEventTimelinePanel } from "@/components/dashboard/LiveEventTimelinePanel";
import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SimulationControlBar } from "@/components/simulation/SimulationControlBar";
import { SimulationProgressPanel } from "@/components/simulation/SimulationProgressPanel";
import { mapDigitalTwinStateToSpatialState } from "@/lib/spatial-mapper";
import { useIntegratedRuntime } from "@/lib/useIntegratedRuntime";
import { useSimulationRuntime } from "@/lib/useSimulationRuntime";
import type { StatusTone } from "@/lib/types";

function toneForStatus(status: string): StatusTone {
  if (status === "CRITICAL" || status === "OFFLINE") {
    return "critical";
  }
  if (status === "WARNING" || status === "DEGRADED") {
    return "warning";
  }
  return "safe";
}

export function CommandCenterClient() {
  const { systemState, explanation, events, loading, error } = useIntegratedRuntime({ pollMs: 1000, eventLimit: 150, includeExplanation: true });
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
  const availableExits = systemState?.building_twin.exits.filter((exitItem) => exitItem.is_available).length ?? 0;
  const totalExits = systemState?.building_twin.exits.length ?? 0;
  const occupantsAtRisk = simulation?.phase === "EVACUATION" || simulation?.phase === "RESPONSE" || simulation?.phase === "CONTAINMENT"
    ? systemState?.occupancy_twin.evacuating_count ?? 0
    : 0;
  const responseReady = systemState?.response_twin.crews.every((crew) => crew.status === "AVAILABLE")
    && systemState.response_twin.drones.every((drone) => drone.status === "AVAILABLE");
  const responseStateLabel = simulation?.phase === "RESOLVED"
    ? "RESOLVED"
    : simulation?.phase === "CONTAINMENT"
      ? "CONTAINED"
      : systemState?.response_twin.crews.some((crew) => crew.status === "ON_SCENE") || systemState?.response_twin.drones.some((drone) => drone.status === "ON_SCENE")
        ? "ACTIVE"
        : responseReady
          ? "READY"
          : "ACTIVE";
  const primaryRoute = systemState?.occupancy_twin.active_routes[0] ?? null;
  const topContributors = (explanation?.top_positive_contributors ?? []).slice(0, 3).map((item) => item.feature_label);
  const pendingApproval = simulation?.pending_approval?.status === "PENDING";
  const governanceSummary = pendingApproval
    ? "HUMAN APPROVAL REQUIRED"
    : simulation?.governance_decision === "HVAC_ISOLATION_REJECTED"
      ? "HVAC Isolation - REJECTED"
      : simulation?.governance_decision === "HVAC_ISOLATION_APPROVED"
        ? "HVAC Isolation - APPROVED"
        : "No Pending Approval";
  const firstResponseEta = (() => {
    if (!systemState) {
      return "N/A";
    }
    const values = [
      ...systemState.response_twin.crews.map((crew) => crew.eta_minutes),
      ...systemState.response_twin.drones.map((drone) => drone.eta_minutes),
    ].filter((value) => value > 0);
    if (!values.length) {
      return "N/A";
    }
    return `${Math.min(...values).toFixed(1)} min`;
  })();

  return (
    <div>
      <PageHeader
        title="Command Center"
        description="Unified operational cockpit for live incident awareness, AI prediction, optimization, response coordination, and governed autonomy."
        actions={(
          <div className="flex items-center gap-2">
            <ApiStatusBadge />
            <Link href="/presentation" className="action-btn">Presentation Mode</Link>
          </div>
        )}
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Fire Risk"
          value={simulation?.phase === "CONTAINMENT" ? "CONTAINED" : systemState?.fire_twin.risk_level ?? "OFFLINE"}
          helper={systemState?.fire_twin.prediction_source === "ML_MODEL" ? "ML Fire Risk from live fire twin state" : "Rule-Based Fallback Risk from live fire twin state"}
          statusLabel={systemState?.fire_twin.risk_level ?? "OFFLINE"}
          statusTone={toneForStatus(systemState?.fire_twin.risk_level ?? "OFFLINE")}
          icon={<Flame className="h-5 w-5" />}
        />
        <MetricCard
          label="Occupants at Risk"
          value={occupantsAtRisk}
          helper={occupantsAtRisk > 0 ? "Live evacuation exposure" : "No active risk exposure"}
          statusLabel={occupantsAtRisk > 0 ? "ACTIVE" : "NORMAL"}
          statusTone={toneForStatus(systemState?.occupancy_twin.congestion_level === "HIGH" ? "WARNING" : "NORMAL")}
          icon={<UsersRound className="h-5 w-5" />}
        />
        <MetricCard
          label="Safe Exits"
          value={`${availableExits} / ${totalExits}`}
          helper="Directly mapped into the 3D exit layer"
          statusLabel={spatialState.summary.blockedExits > 0 ? "WATCH" : "CLEAR"}
          statusTone={spatialState.summary.blockedExits > 0 ? "warning" : "safe"}
          icon={<ShieldCheck className="h-5 w-5" />}
        />
        <MetricCard
          label="Response Status"
          value={responseStateLabel}
          helper="Crew and drone staging markers"
          statusLabel={responseStateLabel}
          statusTone={responseStateLabel === "READY" || responseStateLabel === "RESOLVED" ? "safe" : "warning"}
          icon={<Siren className="h-5 w-5" />}
        />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]">
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

      <section className="mt-4 grid gap-4 xl:grid-cols-[2fr_1fr]">
        <Panel title="Shared 3D Spatial Model" subtitle="Shared context across buildings, hazards, occupants, routes, and response operations">
          <BuildingScene systemState={systemState} loading={loading} error={error} variant="compact" />
        </Panel>

        <Panel title="Live System" subtitle="Twin, spatial, and orchestrator availability">
          <ul className="space-y-2 text-sm">
            <li className="system-row"><span>Fire & Environment Twin</span><StatusBadge label={systemState?.fire_twin.status ?? "OFFLINE"} tone={toneForStatus(systemState?.fire_twin.status ?? "OFFLINE")} /></li>
            <li className="system-row"><span>Building Infrastructure Twin</span><StatusBadge label={systemState?.building_twin.status ?? "OFFLINE"} tone={toneForStatus(systemState?.building_twin.status ?? "OFFLINE")} /></li>
            <li className="system-row"><span>Occupancy & Evacuation Twin</span><StatusBadge label={systemState?.occupancy_twin.status ?? "OFFLINE"} tone={toneForStatus(systemState?.occupancy_twin.status ?? "OFFLINE")} /></li>
            <li className="system-row"><span>Emergency Response Twin</span><StatusBadge label={systemState?.response_twin.status ?? "OFFLINE"} tone={toneForStatus(systemState?.response_twin.status ?? "OFFLINE")} /></li>
            <li className="system-row"><span>AI / Decision Orchestrator</span><StatusBadge label={systemState?.orchestrator.status ?? "OFFLINE"} tone={toneForStatus(systemState?.orchestrator.status ?? "OFFLINE")} /></li>
            <li className="system-row"><span>Active Hazard Zones</span><StatusBadge label={String(spatialState.summary.activeHazardZones)} tone={spatialState.summary.activeHazardZones > 0 ? "warning" : "safe"} /></li>
          </ul>
          {error ? <p className="mt-4 text-sm text-[var(--accent-red)]">System Offline | Backend connection unavailable</p> : null}
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Intelligence Summary" subtitle="Prediction, explainability, and consistency checks">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>ML Prediction</span><span>{explanation?.predicted_class ?? "N/A"}</span></div>
            <div className="system-row"><span>Confidence</span><span>{typeof explanation?.confidence === "number" ? `${(explanation.confidence * 100).toFixed(1)}%` : "N/A"}</span></div>
            <div className="system-row"><span>Physical Consistency</span><span>{explanation?.physical_consistency.status === "PHYSICALLY_CONSISTENT" ? "VERIFIED" : (explanation?.physical_consistency.status ?? "N/A")}</span></div>
            <div className="system-row"><span>Model Version</span><span>{explanation?.model_version ?? "N/A"}</span></div>
          </div>
          <div className="mt-3 text-sm text-[var(--fg-muted)]">
            Top contributors: {topContributors.length > 0 ? topContributors.join(" | ") : "N/A"}
          </div>
        </Panel>

        <Panel title="Evacuation Summary" subtitle="Dynamic risk-aware evacuation optimization using live Digital Twin state">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Recommended Strategy</span><span>{primaryRoute?.strategy?.replaceAll("_", " ") ?? "N/A"}</span></div>
            <div className="system-row"><span>Selected Exit</span><span>{primaryRoute?.to_exit_id ?? "N/A"}</span></div>
            <div className="system-row"><span>Estimated Time</span><span>{typeof primaryRoute?.estimated_time_seconds === "number" ? `${primaryRoute.estimated_time_seconds.toFixed(1)} s` : "N/A"}</span></div>
            <div className="system-row"><span>Hazard Exposure</span><span>{typeof primaryRoute?.hazard_exposure_score === "number" ? primaryRoute.hazard_exposure_score.toFixed(2) : "N/A"}</span></div>
            <div className="system-row"><span>Recalculation Trigger</span><span>{primaryRoute?.status === "NO_SAFE_ROUTE" ? "No Safe Route" : "Twin State Change"}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Response Summary" subtitle="Emergency Response Twin readiness and active phase">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Crew Status</span><span>{systemState?.response_twin.crews.map((item) => item.status).join(", ") ?? "N/A"}</span></div>
            <div className="system-row"><span>Drone Status</span><span>{systemState?.response_twin.drones.map((item) => item.status).join(", ") ?? "N/A"}</span></div>
            <div className="system-row"><span>First-response ETA</span><span>{firstResponseEta}</span></div>
            <div className="system-row"><span>Current response phase</span><span>{simulation?.phase ?? "NORMAL"}</span></div>
          </div>
        </Panel>
        <Panel title="Governance Summary" subtitle="Human oversight and branch outcome visibility">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Status</span><span>{governanceSummary}</span></div>
            <div className="system-row"><span>Demo Mode</span><span>{simulation?.auto_approve ? "AUTO APPROVAL" : "MANUAL APPROVAL"}</span></div>
            <div className="system-row"><span>Outcome Effect</span><span>{simulation?.latest_run_summary?.decision_impact_summary ?? "Pending"}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <LiveEventTimelinePanel externalEvents={events} externalLoading={loading} externalError={error} />
      </section>
    </div>
  );
}