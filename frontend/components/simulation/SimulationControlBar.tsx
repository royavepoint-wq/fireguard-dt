import { Panel } from "@/components/ui/Panel";
import type { SimulationRunSummary, SimulationState } from "@/lib/types";

type SimulationControlBarProps = {
  simulation: SimulationState | null;
  latestRun: SimulationRunSummary | null;
  pending: string | null;
  autoApprovePreference: boolean;
  onToggleAutoApproval: () => void;
  onStartDemo: () => void;
  onStartManual: () => void;
  onRunAgain: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
  onApprove: () => void;
  onReject: () => void;
};

function formatSeconds(value: number) {
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function statusBanner(status: SimulationState["status"], phase: SimulationState["phase"] | undefined) {
  if (status === "COMPLETED" || phase === "RESOLVED") {
    return {
      label: "Resolved",
      detail: "Scenario completed successfully",
      toneClass: "border-emerald-300/45 bg-emerald-500/12 text-emerald-100",
    };
  }
  if (status === "WAITING_FOR_APPROVAL") {
    return {
      label: "Awaiting Approval",
      detail: "Simulation paused until a human decision is provided",
      toneClass: "border-amber-300/45 bg-amber-500/12 text-amber-100",
    };
  }
  if (status === "PAUSED") {
    return {
      label: "Paused",
      detail: "Simulation is paused",
      toneClass: "border-sky-300/40 bg-sky-500/10 text-sky-100",
    };
  }
  if (status === "ERROR") {
    return {
      label: "Simulation Error",
      detail: "The simulation encountered an error",
      toneClass: "border-rose-300/45 bg-rose-500/12 text-rose-100",
    };
  }
  if (status === "RUNNING") {
    return {
      label: phase ?? "Running",
      detail: "Simulation is actively progressing",
      toneClass: "border-cyan-300/40 bg-cyan-500/10 text-cyan-100",
    };
  }
  return {
    label: "Scenario Ready",
    detail: "Ready to run emergency simulation",
    toneClass: "border-slate-300/35 bg-slate-500/10 text-slate-100",
  };
}

export function SimulationControlBar({
  simulation,
  latestRun,
  pending,
  autoApprovePreference,
  onToggleAutoApproval,
  onStartDemo,
  onStartManual,
  onRunAgain,
  onPause,
  onResume,
  onStop,
  onReset,
  onSpeedChange,
  onApprove,
  onReject,
}: SimulationControlBarProps) {
  const status = simulation?.status ?? "STOPPED";
  const phase = simulation?.phase;
  const waitingForApproval = status === "WAITING_FOR_APPROVAL";
  const completed = status === "COMPLETED" || phase === "RESOLVED";
  const errored = status === "ERROR";
  const paused = status === "PAUSED";
  const runSummary = latestRun ?? simulation?.latest_run_summary ?? null;
  const banner = statusBanner(status, phase);

  const canPause = status === "RUNNING";
  const canResume = status === "PAUSED";
  const canStop = status === "RUNNING" || status === "PAUSED" || status === "WAITING_FOR_APPROVAL";
  const canReset = status !== "STOPPED" || simulation?.latest_run_summary !== null;
  const canStart = pending === null && status !== "RUNNING" && !waitingForApproval;
  const canRunAgain = completed && pending === null;
  const shouldAllowSpeedChange = pending === null && !waitingForApproval;

  return (
    <Panel title="Simulation Control" subtitle="Deterministic emergency scenario playback with live twin synchronization">
      <div className={`mb-4 rounded-xl border px-3 py-2 ${banner.toneClass}`}>
        <p className="text-xs font-semibold uppercase tracking-[0.16em]">{banner.label}</p>
        <p className="mt-1 text-sm">{banner.detail}</p>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1.6fr_1fr]">
        <div className="flex flex-wrap gap-2">
          <button type="button" className="action-btn" disabled={!canStart} onClick={onStartDemo}>RUN FULL DEMO</button>
          <button type="button" className="filter-btn" disabled={!canStart} onClick={onStartManual}>START SCENARIO</button>
          <button type="button" className="filter-btn" disabled={!canRunAgain} onClick={onRunAgain}>Run Again</button>
          <button type="button" className="filter-btn" disabled={!canPause || pending !== null} onClick={onPause}>Pause</button>
          <button type="button" className="filter-btn" disabled={!canResume || pending !== null || waitingForApproval} onClick={onResume}>Resume</button>
          <button type="button" className="filter-btn" disabled={!canStop || pending !== null} onClick={onStop}>Stop</button>
          <button type="button" className="filter-btn" disabled={!canReset || pending !== null} onClick={onReset}>RESET DEMO</button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs uppercase tracking-[0.18em] text-[var(--fg-muted)]">Speed</span>
          {[1, 2, 5].map((speed) => (
            <button
              key={speed}
              type="button"
              className={simulation?.speed_multiplier === speed ? "filter-btn filter-btn-active" : "filter-btn"}
              disabled={!shouldAllowSpeedChange}
              onClick={() => onSpeedChange(speed)}
            >
              {speed}x
            </button>
          ))}
          <span className="ml-2 text-xs uppercase tracking-[0.18em] text-[var(--fg-muted)]">Demo Mode</span>
          <button type="button" className={autoApprovePreference ? "filter-btn filter-btn-active" : "filter-btn"} disabled={pending !== null || simulation?.status === "RUNNING" || waitingForApproval} onClick={onToggleAutoApproval}>{autoApprovePreference ? "ON" : "OFF"}</button>
        </div>
      </div>

      {simulation?.pending_approval?.status === "PENDING" ? (
        <div className="mt-4 rounded-2xl border border-amber-300/55 bg-amber-500/12 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">Human Approval Required</p>
          <p className="mt-2 text-base font-semibold text-white">High-Risk Action: {simulation.pending_approval.action_description}</p>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Reason: {simulation.pending_approval.message}</p>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Risk: {simulation.pending_approval.risk_level}</p>
          {waitingForApproval ? (
            <p className="mt-1 text-sm text-amber-200">Simulation Paused - Awaiting Human Approval</p>
          ) : null}
          <div className="mt-3 flex gap-2">
            <button type="button" className="filter-btn filter-btn-active" disabled={pending !== null} onClick={onApprove}>Approve Action</button>
            <button type="button" className="filter-btn" disabled={pending !== null} onClick={onReject}>Reject Action</button>
          </div>
        </div>
      ) : null}

      {completed ? (
        <div className="mt-4 rounded-2xl border border-emerald-300/35 bg-emerald-500/8 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">Scenario Complete</p>
          <p className="mt-2 text-base font-semibold text-white">{simulation?.scenario_name ?? runSummary?.scenario ?? "Electrical Room Fire"}</p>
          <p className="mt-1 text-sm text-emerald-100">
            Scenario Outcome: RESOLVED - {runSummary?.outcome_quality === "DEGRADED" ? "DEGRADED RESPONSE" : "OPTIMAL RESPONSE"}
          </p>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">
            Governance Decision: HVAC Isolation {runSummary?.governance_decision === "HVAC_ISOLATION_REJECTED" ? "REJECTED" : "APPROVED"}
          </p>
          <ul className="mt-2 space-y-1 text-sm text-[var(--fg-muted)]">
            <li>OK Fire contained</li>
            <li>OK Evacuation completed</li>
            <li>OK Emergency response completed</li>
            <li>OK Incident resolved</li>
          </ul>
          {runSummary?.decision_impact_summary ? (
            <p className="mt-2 text-sm text-[var(--fg-muted)]">Decision Impact: {runSummary.decision_impact_summary}</p>
          ) : null}
          <dl className="mt-3 grid gap-2 sm:grid-cols-2">
            <div className="kv-item"><dt>Simulation Time</dt><dd>{formatSeconds(simulation?.elapsed_seconds ?? runSummary?.duration ?? 0)}</dd></div>
            <div className="kv-item"><dt>Maximum Risk</dt><dd>{runSummary?.max_risk ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Occupants at Risk</dt><dd>{runSummary?.occupants_at_risk ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Evacuated</dt><dd>{runSummary?.evacuated ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Resources Dispatched</dt><dd>{runSummary?.resources_dispatched ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Containment Time</dt><dd>{runSummary?.time_to_containment ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Resolution Time</dt><dd>{runSummary?.time_to_resolution ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Risk Exposure</dt><dd>{runSummary?.risk_exposure_score ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Unsafe Zone Duration</dt><dd>{runSummary?.unsafe_zone_duration ?? "N/A"}</dd></div>
            <div className="kv-item"><dt>Peak Congestion</dt><dd>{runSummary?.peak_congestion ?? "N/A"}</dd></div>
          </dl>
        </div>
      ) : null}

      {status === "STOPPED" ? (
        <div className="mt-4 rounded-2xl border border-white/10 bg-white/4 p-4">
          <p className="text-sm text-[var(--fg-muted)]">Ready to run emergency simulation</p>
          <p className="mt-1 text-base font-semibold text-white">{simulation?.scenario_name ?? "Electrical Room Fire"}</p>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">Status: STOPPED | Phase: {simulation?.phase ?? "NORMAL"} | Time: 00:00 / 02:00</p>
        </div>
      ) : null}

      {paused ? (
        <div className="mt-4 rounded-2xl border border-sky-300/35 bg-sky-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-200">Simulation Paused</p>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">Current Phase: {simulation?.phase ?? "N/A"}</p>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Time: {formatSeconds(simulation?.elapsed_seconds ?? 0)}</p>
        </div>
      ) : null}

      {errored ? (
        <div className="mt-4 rounded-2xl border border-rose-300/35 bg-rose-500/10 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-rose-200">Simulation Error</p>
          <p className="mt-2 text-sm text-[var(--fg-muted)]">{simulation?.last_error ?? "An unexpected simulation error occurred."}</p>
        </div>
      ) : null}
    </Panel>
  );
}