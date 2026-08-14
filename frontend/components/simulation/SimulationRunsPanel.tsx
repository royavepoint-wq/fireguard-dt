import { Panel } from "@/components/ui/Panel";
import type { SimulationRunSummary } from "@/lib/types";

type SimulationRunsPanelProps = {
  runs: SimulationRunSummary[];
};

export function SimulationRunsPanel({ runs }: SimulationRunsPanelProps) {
  return (
    <Panel title="Replay / Run History" subtitle="Latest in-memory deterministic simulation runs">
      {runs.length > 0 ? (
        <ul className="space-y-2 text-sm">
          {runs.slice(0, 5).map((run) => (
            <li key={run.run_id} className="rounded-2xl border border-white/8 bg-white/4 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium text-white">{run.scenario}</span>
                <span className="text-[var(--fg-muted)]">{run.status}</span>
              </div>
              <p className="mt-2 text-xs text-[var(--fg-muted)]">
                Outcome {run.outcome_quality ?? "N/A"} • Decision {run.governance_decision} • Max Risk {run.max_risk}
              </p>
              <p className="mt-1 text-xs text-[var(--fg-muted)]">
                Exposure {run.risk_exposure_score} • Evacuated {run.evacuated} • Containment {run.time_to_containment ?? "N/A"} sec
              </p>
              <p className="mt-1 text-xs text-[var(--fg-muted)]">
                Prediction Source {run.prediction_source} • Model {run.model_version ?? "N/A"} • Max Critical Prob {(run.max_critical_probability * 100).toFixed(1)}%
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-[var(--fg-muted)]">No completed runs yet.</p>
      )}
    </Panel>
  );
}