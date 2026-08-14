import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { FireTwinState, SimulationRunSummary, SimulationState, StatusTone } from "@/lib/types";

function formatSeconds(value: number) {
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function toneForPhase(phase: string): StatusTone {
  if (phase === "CRITICAL") {
    return "critical";
  }
  if (phase === "WARNING" || phase === "EVACUATION" || phase === "RESPONSE" || phase === "CONTAINMENT") {
    return "warning";
  }
  return "safe";
}

type SimulationProgressPanelProps = {
  simulation: SimulationState | null;
  latestRun: SimulationRunSummary | null;
  fireTwin: FireTwinState | null;
};

export function SimulationProgressPanel({ simulation, latestRun, fireTwin }: SimulationProgressPanelProps) {
  const progress = simulation?.progress ?? 0;
  const barWidth = `${Math.round(progress * 100)}%`;
  const showRunSummary = Boolean(latestRun && (simulation?.status === "COMPLETED" || simulation?.status === "STOPPED"));
  const completedRun = showRunSummary ? latestRun : null;

  return (
    <Panel title="Simulation Progress" subtitle="Deterministic emergency lifecycle with live ML fire-risk inference">
      {simulation?.status === "WAITING_FOR_APPROVAL" && simulation.pending_approval ? (
        <div className="mb-4 rounded-2xl border border-amber-300/55 bg-amber-500/12 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">Human Approval Required</p>
          <p className="mt-2 text-base font-semibold text-white">{simulation.pending_approval.action_description}</p>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Simulation Paused - Awaiting Human Approval</p>
        </div>
      ) : null}
      <div className="flex items-center gap-3">
        <StatusBadge label={simulation?.phase ?? "NORMAL"} tone={toneForPhase(simulation?.phase ?? "NORMAL")} />
        <span className="text-sm text-[var(--fg-muted)]">{simulation?.current_stage_label ?? "Monitoring"}</span>
      </div>
      {simulation?.phase === "RESOLVED" || simulation?.status === "COMPLETED" ? (
        <p className="mt-2 text-xs text-[var(--fg-muted)]">
          Resolved means the emergency reached a stable end state: hazard contained, evacuation stabilized/completed,
          response actions completed, and no pending governance approval remains.
        </p>
      ) : null}
      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="kv-item"><dt>Scenario</dt><dd>{simulation?.scenario_name ?? "Electrical Room Fire"}</dd></div>
        <div className="kv-item"><dt>Time</dt><dd>{formatSeconds(simulation?.elapsed_seconds ?? 0)} / 02:00</dd></div>
        <div className="kv-item"><dt>Status</dt><dd>{simulation?.status ?? "STOPPED"}</dd></div>
        <div className="kv-item"><dt>{fireTwin?.prediction_source === "ML_MODEL" ? "ML Fire Risk" : "Rule-Based Fallback Risk"}</dt><dd>{Math.round((fireTwin?.fire_risk_probability ?? 0) * 100)}%</dd></div>
      </dl>
      <p className="mt-2 text-xs text-[var(--fg-muted)]">
        Source: {fireTwin?.prediction_source ?? "NOT_AVAILABLE"} {fireTwin?.model_version ? `| Model ${fireTwin.model_version}` : ""} | Confidence: {Math.round((fireTwin?.prediction_confidence ?? 0) * 100)}%
      </p>
      <div className="mt-4">
        <div className="simulation-progress-track"><div className="simulation-progress-fill" style={{ width: barWidth }} /></div>
      </div>
      {completedRun ? (
        <div className="mt-4 rounded-2xl border border-white/10 bg-white/4 p-4">
          <p className="text-sm font-semibold text-white">Scenario Complete</p>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">
            Outcome: {completedRun.outcome_quality === "DEGRADED" ? "RESOLVED - DEGRADED RESPONSE" : "RESOLVED - OPTIMAL RESPONSE"}
          </p>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <div className="kv-item"><dt>Maximum Risk</dt><dd>{completedRun.max_risk}</dd></div>
            <div className="kv-item"><dt>Occupants at Risk</dt><dd>{completedRun.occupants_at_risk}</dd></div>
            <div className="kv-item"><dt>Evacuated</dt><dd>{completedRun.evacuated}</dd></div>
            <div className="kv-item"><dt>Resources Dispatched</dt><dd>{completedRun.resources_dispatched}</dd></div>
            <div className="kv-item"><dt>Time to Warning</dt><dd>{completedRun.time_to_warning ?? "N/A"} sec</dd></div>
            <div className="kv-item"><dt>Time to Critical</dt><dd>{completedRun.time_to_critical ?? "N/A"} sec</dd></div>
            <div className="kv-item"><dt>Time to Evacuation</dt><dd>{completedRun.time_to_evacuation ?? "N/A"} sec</dd></div>
            <div className="kv-item"><dt>Time to Containment</dt><dd>{completedRun.time_to_containment ?? "N/A"} sec</dd></div>
            <div className="kv-item"><dt>Time to Resolution</dt><dd>{completedRun.time_to_resolution ?? "N/A"} sec</dd></div>
            <div className="kv-item"><dt>Risk Exposure Score</dt><dd>{completedRun.risk_exposure_score}</dd></div>
            <div className="kv-item"><dt>Unsafe Zone Duration</dt><dd>{completedRun.unsafe_zone_duration} sec</dd></div>
            <div className="kv-item"><dt>Governance Decision</dt><dd>{completedRun.governance_decision}</dd></div>
          </dl>
          {completedRun.decision_impact_summary ? (
            <p className="mt-3 text-sm text-[var(--fg-muted)]">Decision Impact: {completedRun.decision_impact_summary}</p>
          ) : null}
        </div>
      ) : null}
    </Panel>
  );
}