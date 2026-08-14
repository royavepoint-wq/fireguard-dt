"use client";

import { useMemo } from "react";

import { BuildingScene } from "@/components/3d/BuildingScene";
import { LiveEventTimelinePanel } from "@/components/dashboard/LiveEventTimelinePanel";
import { SimulationControlBar } from "@/components/simulation/SimulationControlBar";
import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { useIntegratedRuntime } from "@/lib/useIntegratedRuntime";
import { useSimulationRuntime } from "@/lib/useSimulationRuntime";

const STAGES = [
  "Monitor",
  "Detect",
  "Predict",
  "Understand",
  "Optimize",
  "Coordinate",
  "Respond",
  "Govern",
  "Resolve",
];

function stageIndex(phase: string, waitingForApproval: boolean): number {
  if (waitingForApproval) {
    return 8;
  }
  if (phase === "ANOMALY") {
    return 2;
  }
  if (phase === "WARNING") {
    return 3;
  }
  if (phase === "CRITICAL") {
    return 4;
  }
  if (phase === "EVACUATION") {
    return 5;
  }
  if (phase === "RESPONSE") {
    return 6;
  }
  if (phase === "CONTAINMENT") {
    return 7;
  }
  if (phase === "RESOLVED") {
    return 9;
  }
  return 1;
}

export default function PresentationPage() {
  const { systemState, simulation, runs, explanation, events, loading, error } = useIntegratedRuntime({
    pollMs: 1000,
    includeSimulation: true,
    includeRuns: true,
    includeExplanation: true,
    eventLimit: 160,
  });
  const {
    pending,
    autoApprovePreference,
    setAutoApprovePreference,
    runPresentationDemo,
    runStart,
    runAction,
    changeSpeed,
    runAgain,
  } = useSimulationRuntime({ pollMs: 1000 });

  const waitingForApproval = simulation?.status === "WAITING_FOR_APPROVAL";
  const currentStage = stageIndex(simulation?.phase ?? "NORMAL", waitingForApproval);
  const route = systemState?.occupancy_twin.active_routes[0] ?? null;
  const firstResponse = runs[0]?.time_to_first_response ?? simulation?.latest_run_summary?.time_to_first_response ?? null;

  const fireRiskLabel = simulation?.phase === "CONTAINMENT" ? "CONTAINED" : systemState?.fire_twin.risk_level ?? "NORMAL";
  const responseStatus = waitingForApproval
    ? "ACTIVE"
    : simulation?.phase === "RESOLVED"
      ? "RESOLVED"
      : simulation?.phase === "CONTAINMENT"
        ? "CONTAINED"
        : "READY";

  const contributors = useMemo(
    () => (explanation?.top_positive_contributors ?? []).slice(0, 3).map((row) => row.feature_label),
    [explanation],
  );

  return (
    <div className="space-y-4">
      <PageHeader
        title="Presentation Mode"
        description="Full demo view for end-to-end incident lifecycle, governed autonomy, and final outcomes."
      />

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Fire Risk" value={fireRiskLabel} helper={`Electrical Room | ${((systemState?.fire_twin.fire_risk_probability ?? 0) * 100).toFixed(1)}%`} statusLabel={systemState?.fire_twin.risk_level ?? "NORMAL"} statusTone={fireRiskLabel === "CRITICAL" ? "critical" : fireRiskLabel === "WARNING" ? "warning" : "safe"} />
        <MetricCard label="Occupants at Risk" value={systemState?.occupancy_twin.evacuating_count ?? 0} helper="Live exposure estimate" statusLabel={(systemState?.occupancy_twin.evacuating_count ?? 0) > 0 ? "ACTIVE" : "NORMAL"} statusTone={(systemState?.occupancy_twin.evacuating_count ?? 0) > 0 ? "warning" : "safe"} />
        <MetricCard label="Safe Exits" value={`${systemState?.building_twin.exits.filter((item) => item.is_available).length ?? 0}/${systemState?.building_twin.exits.length ?? 0}`} helper="Shared 3D state" statusLabel="LIVE" statusTone="info" />
        <MetricCard label="Response" value={responseStatus} helper="Emergency Response Twin" statusLabel={responseStatus} statusTone={responseStatus === "READY" || responseStatus === "RESOLVED" ? "safe" : "warning"} />
      </section>

      <Panel title="Presentation Stage" subtitle="Automatic stage indicator for incident lifecycle narrative">
        <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-9">
          {STAGES.map((stage, index) => {
            const active = index + 1 === currentStage;
            return (
              <div key={stage} className={active ? "rounded-xl border border-cyan-300/50 bg-cyan-500/18 px-3 py-2 text-sm text-white" : "rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--fg-muted)]"}>
                <div className="text-[10px] uppercase tracking-[0.18em]">{index + 1}</div>
                <div className="font-semibold">{stage}</div>
              </div>
            );
          })}
        </div>
      </Panel>

      <section className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <Panel title="Shared 3D Spatial Model" subtitle="Fire, smoke, occupancy, route, blocked infrastructure, and response markers">
          <BuildingScene systemState={systemState} loading={loading} error={error} variant="full" />
        </Panel>

        <div className="space-y-4">
          <Panel title="Intelligence" subtitle="ML prediction and explainability evidence">
            <div className="space-y-2 text-sm">
              <div className="system-row"><span>Prediction</span><span>{explanation?.predicted_class ?? "N/A"}</span></div>
              <div className="system-row"><span>Confidence</span><span>{typeof explanation?.confidence === "number" ? `${(explanation.confidence * 100).toFixed(1)}%` : "N/A"}</span></div>
              <div className="system-row"><span>Top 3 Contributors</span><span>{contributors.join(" | ") || "N/A"}</span></div>
              <div className="system-row"><span>Physical Consistency</span><span>{explanation?.physical_consistency.status === "PHYSICALLY_CONSISTENT" ? "VERIFIED" : explanation?.physical_consistency.status ?? "N/A"}</span></div>
              <div className="system-row"><span>Model Version</span><span>{explanation?.model_version ?? "N/A"}</span></div>
            </div>
          </Panel>

          <Panel title="Evacuation & Response" subtitle="Current route and emergency action summary">
            <div className="space-y-2 text-sm">
              <div className="system-row"><span>Recommended Strategy</span><span>{route?.strategy?.replaceAll("_", " ") ?? "N/A"}</span></div>
              <div className="system-row"><span>Selected Exit</span><span>{route?.to_exit_id ?? "N/A"}</span></div>
              <div className="system-row"><span>Estimated Time</span><span>{typeof route?.estimated_time_seconds === "number" ? `${route.estimated_time_seconds.toFixed(1)} s` : "N/A"}</span></div>
              <div className="system-row"><span>Hazard Exposure</span><span>{typeof route?.hazard_exposure_score === "number" ? route.hazard_exposure_score.toFixed(2) : "N/A"}</span></div>
              <div className="system-row"><span>First Response Time</span><span>{typeof firstResponse === "number" ? `${firstResponse}s` : "N/A"}</span></div>
            </div>
          </Panel>

          <Panel title="Governance" subtitle="Responsible autonomy checkpoint">
            {waitingForApproval ? (
              <p className="rounded-xl border border-amber-300/60 bg-amber-500/20 p-3 text-sm font-semibold text-amber-100">HUMAN APPROVAL REQUIRED</p>
            ) : null}
            <div className="space-y-2 text-sm">
              <div className="system-row"><span>Demo Mode</span><span>{autoApprovePreference ? "AUTO APPROVAL" : "MANUAL APPROVAL"}</span></div>
              <div className="system-row"><span>Decision</span><span>{simulation?.governance_decision ?? "PENDING"}</span></div>
              <div className="system-row"><span>Outcome Effect</span><span>{simulation?.latest_run_summary?.decision_impact_summary ?? "Pending"}</span></div>
            </div>
          </Panel>
        </div>
      </section>

      <SimulationControlBar
        simulation={simulation}
        latestRun={runs[0] ?? simulation?.latest_run_summary ?? null}
        pending={pending}
        autoApprovePreference={autoApprovePreference}
        onToggleAutoApproval={() => setAutoApprovePreference((value) => !value)}
        onStartDemo={() => void runPresentationDemo()}
        onStartManual={() => void runStart({ scenario_id: "electrical-room-fire", speed_multiplier: 5, auto_approve: autoApprovePreference, presentation_mode: true })}
        onRunAgain={() => void runAgain()}
        onPause={() => void runAction("pause")}
        onResume={() => void runAction("resume")}
        onStop={() => void runAction("stop")}
        onReset={() => void runAction("reset")}
        onSpeedChange={(speed) => void changeSpeed(speed)}
        onApprove={() => void runAction("approve")}
        onReject={() => void runAction("reject")}
      />

      <section>
        <LiveEventTimelinePanel externalEvents={events} externalLoading={loading} externalError={error} />
      </section>

      {simulation?.status === "COMPLETED" || simulation?.phase === "RESOLVED" ? (
        <Panel title="Scenario Complete" subtitle="Final incident outcome and measured metrics">
          <p className="text-base font-semibold text-white">Outcome: RESOLVED - {simulation?.latest_run_summary?.outcome_quality === "DEGRADED" ? "DEGRADED RESPONSE" : "OPTIMAL RESPONSE"}</p>
          <dl className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            <div className="kv-item"><dt>Maximum Risk</dt><dd>{simulation?.latest_run_summary?.max_risk ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Occupants at Risk</dt><dd>{simulation?.latest_run_summary?.occupants_at_risk ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Evacuated</dt><dd>{simulation?.latest_run_summary?.evacuated ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Selected Route Strategy</dt><dd>{route?.strategy?.replaceAll("_", " ") ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Hazard Exposure</dt><dd>{simulation?.latest_run_summary?.risk_exposure_score ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>First Response Time</dt><dd>{simulation?.latest_run_summary?.time_to_first_response ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Containment Time</dt><dd>{simulation?.latest_run_summary?.time_to_containment ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Resolution Time</dt><dd>{simulation?.latest_run_summary?.time_to_resolution ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Governance Decision</dt><dd>{simulation?.latest_run_summary?.governance_decision ?? "N/A"}</dd></div>
          </dl>
        </Panel>
      ) : null}
    </div>
  );
}
