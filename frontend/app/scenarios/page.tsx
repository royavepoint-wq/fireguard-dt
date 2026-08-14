"use client";

import { useEffect, useMemo, useState } from "react";
import { ScenarioPresetPanel } from "@/components/simulation/ScenarioPresetPanel";
import { SimulationControlBar } from "@/components/simulation/SimulationControlBar";
import { SimulationProgressPanel } from "@/components/simulation/SimulationProgressPanel";
import { SimulationRunsPanel } from "@/components/simulation/SimulationRunsPanel";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getExperimentResults, getExperimentScenarioLibrary, getExperimentStatus, runExperiments } from "@/lib/api";
import type { ApprovalMode, EvacuationRouteStrategy, ExperimentResultsResponse, ExperimentScenarioDefinition } from "@/lib/types";
import { useDigitalTwinRuntime } from "@/lib/useDigitalTwinRuntime";
import { useSimulationRuntime } from "@/lib/useSimulationRuntime";

type FormState = {
  fireOrigin: string;
  fireSeverity: string;
  occupancy: string;
  exitStatus: string;
  hvacState: string;
  sprinklerState: string;
};

const defaultState: FormState = {
  fireOrigin: "Electrical Room",
  fireSeverity: "High",
  occupancy: "250",
  exitStatus: "Exit B Blocked",
  hvacState: "Running",
  sprinklerState: "Failed",
};

export default function ScenariosPage() {
  const { systemState } = useDigitalTwinRuntime({ pollMs: 1000 });
  const [form, setForm] = useState<FormState>(defaultState);
  const [selectedScenarioId, setSelectedScenarioId] = useState("electrical-room-fire");
  const [selectedRoutingStrategy, setSelectedRoutingStrategy] = useState<EvacuationRouteStrategy>("TWIN_OPTIMIZED");
  const [selectedApprovalMode, setSelectedApprovalMode] = useState<ApprovalMode>("AUTO_APPROVE");
  const [experimentLibrary, setExperimentLibrary] = useState<ExperimentScenarioDefinition[]>([]);
  const [experimentResults, setExperimentResults] = useState<ExperimentResultsResponse | null>(null);
  const [experimentRunning, setExperimentRunning] = useState(false);
  const [experimentError, setExperimentError] = useState<string | null>(null);
  const {
    simulation,
    scenarios,
    runs,
    pending,
    autoApprovePreference,
    setAutoApprovePreference,
    runPresentationDemo,
    runStart,
    runAction,
    changeSpeed,
    runAgain,
    error,
  } = useSimulationRuntime({ pollMs: 1000 });

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [library, results, status] = await Promise.all([
          getExperimentScenarioLibrary(),
          getExperimentResults(),
          getExperimentStatus(),
        ]);
        if (!active) {
          return;
        }
        setExperimentLibrary(library);
        setExperimentResults(results);
        setExperimentRunning(status.is_running);
        setExperimentError(null);
      } catch (loadError) {
        if (active) {
          setExperimentError(loadError instanceof Error ? loadError.message : "Unable to load scenario experiments.");
        }
      }
    };

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, 1200);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const selectedExperimentScenario = useMemo(
    () => experimentLibrary.find((scenario) => scenario.simulation_scenario_id === selectedScenarioId) ?? null,
    [experimentLibrary, selectedScenarioId],
  );

  const selectedScenarioRows = useMemo(
    () => (experimentResults?.strategy_comparison ?? []).filter((row) => row.scenario_id === (selectedExperimentScenario?.scenario_id ?? "")),
    [experimentResults, selectedExperimentScenario],
  );

  const summaryFromLatestRun = runs[0] ?? simulation?.latest_run_summary ?? null;

  const fastest = selectedScenarioRows.find((row) => row.recommendation_label?.includes("FASTEST"))?.strategy;
  const safest = selectedScenarioRows.find((row) => row.recommendation_label?.includes("SAFEST"))?.strategy;
  const recommended = selectedScenarioRows.find((row) => row.recommendation_label?.includes("RECOMMENDED"))?.strategy;

  const onChange = (key: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const runScenarioExperiment = async () => {
    if (!selectedExperimentScenario) {
      return;
    }
    try {
      setExperimentError(null);
      setExperimentRunning(true);
      await runExperiments({
        scenario_ids: [selectedExperimentScenario.scenario_id],
        strategies: [selectedRoutingStrategy],
        runs_per_configuration: 1,
        include_governance_branches: true,
      });
    } catch (runError) {
      setExperimentError(runError instanceof Error ? runError.message : "Failed to start scenario experiment.");
      setExperimentRunning(false);
    }
  };

  const compareStrategies = async () => {
    if (!selectedExperimentScenario) {
      return;
    }
    try {
      setExperimentError(null);
      setExperimentRunning(true);
      await runExperiments({
        scenario_ids: [selectedExperimentScenario.scenario_id],
        strategies: ["STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"],
        runs_per_configuration: 1,
        include_governance_branches: true,
      });
    } catch (runError) {
      setExperimentError(runError instanceof Error ? runError.message : "Failed to start strategy comparison.");
      setExperimentRunning(false);
    }
  };

  const chartRows = selectedScenarioRows.filter((row) => typeof row.evacuation_time === "number");
  const maxEvacuation = Math.max(1, ...chartRows.map((row) => row.evacuation_time ?? 0));
  const maxExposure = Math.max(1, ...chartRows.map((row) => row.hazard_exposure_score ?? 0));
  const maxCongestion = Math.max(1, ...chartRows.map((row) => row.peak_congestion ?? 0));

  return (
    <div>
      <PageHeader
        title="Scenario Lab"
        description="Scenario experiment engine with repeatable strategy comparisons, response metrics, and safety-first recommendations."
      />

      <section className="grid gap-4 xl:grid-cols-[1.55fr_1fr]">
        <SimulationControlBar
          simulation={simulation}
          latestRun={runs[0] ?? simulation?.latest_run_summary ?? null}
          pending={pending}
          autoApprovePreference={autoApprovePreference}
          onToggleAutoApproval={() => setAutoApprovePreference((value) => !value)}
          onStartDemo={() => void runPresentationDemo()}
          onStartManual={() => void runStart({ scenario_id: selectedScenarioId, speed_multiplier: 1, auto_approve: autoApprovePreference, presentation_mode: false })}
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

      <section className="mt-4">
        <ScenarioPresetPanel scenarios={scenarios} selectedScenarioId={selectedScenarioId} onSelectScenario={setSelectedScenarioId} />
      </section>

      <Panel title="Scenario Controls" subtitle="Default Electrical Room Fire is fully implemented; other presets apply deterministic parameter variations where available">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="form-field">
            <span>Fire Origin</span>
            <input value={form.fireOrigin} onChange={(e) => onChange("fireOrigin", e.target.value)} />
          </label>
          <label className="form-field">
            <span>Fire Severity</span>
            <input value={form.fireSeverity} onChange={(e) => onChange("fireSeverity", e.target.value)} />
          </label>
          <label className="form-field">
            <span>Occupancy</span>
            <input value={form.occupancy} onChange={(e) => onChange("occupancy", e.target.value)} />
          </label>
          <label className="form-field">
            <span>Exit Status</span>
            <input value={form.exitStatus} onChange={(e) => onChange("exitStatus", e.target.value)} />
          </label>
          <label className="form-field">
            <span>HVAC State</span>
            <input value={form.hvacState} onChange={(e) => onChange("hvacState", e.target.value)} />
          </label>
          <label className="form-field">
            <span>Sprinkler State</span>
            <input value={form.sprinklerState} onChange={(e) => onChange("sprinklerState", e.target.value)} />
          </label>
          <label className="form-field">
            <span>Routing Strategy</span>
            <select value={selectedRoutingStrategy} onChange={(e) => setSelectedRoutingStrategy(e.target.value as EvacuationRouteStrategy)}>
              <option value="STATIC_PLAN">Static Plan</option>
              <option value="SHORTEST_PATH">Shortest Path</option>
              <option value="TWIN_OPTIMIZED">Twin Optimized</option>
            </select>
          </label>
          <label className="form-field">
            <span>Approval Mode</span>
            <select value={selectedApprovalMode} onChange={(e) => setSelectedApprovalMode(e.target.value as ApprovalMode)}>
              <option value="AUTO_APPROVE">Auto Approve</option>
              <option value="FORCE_APPROVE">Force Approve (Experiment Branch)</option>
              <option value="FORCE_REJECT">Force Reject (Experiment Branch)</option>
            </select>
          </label>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-4">
          <button type="button" className="action-btn" onClick={() => void runStart({ scenario_id: selectedScenarioId, speed_multiplier: 1, auto_approve: autoApprovePreference, presentation_mode: false })}>
            Run Simulation
          </button>
          <button type="button" className="action-btn" disabled={experimentRunning} onClick={() => void runScenarioExperiment()}>
            {experimentRunning ? "Running..." : "Run Scenario"}
          </button>
          <button type="button" className="filter-btn" disabled={experimentRunning} onClick={() => void compareStrategies()}>
            Compare Strategies
          </button>
          <button type="button" className="filter-btn" onClick={() => void runPresentationDemo()}>
            Run Emergency Demo
          </button>
          <StatusBadge label={selectedExperimentScenario?.readiness ?? "LIMITED"} tone={selectedExperimentScenario?.readiness === "READY" ? "safe" : "warning"} />
        </div>
        <p className="mt-3 text-sm text-[var(--accent-orange)]">
          {scenarios.find((scenario) => scenario.scenario_id === selectedScenarioId)?.implementation_note ?? "Scenario note unavailable."}
        </p>
        {error ? <p className="mt-4 text-sm text-[var(--accent-red)]">{error}</p> : null}
        {experimentError ? <p className="mt-2 text-sm text-[var(--accent-red)]">{experimentError}</p> : null}
      </Panel>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Scenario Result" subtitle="Actual run metrics from simulation and route analytics">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Evacuation Time</span><span>{summaryFromLatestRun?.evacuation_completion_time ?? "N/A"}</span></div>
            <div className="system-row"><span>Hazard Exposure</span><span>{summaryFromLatestRun?.risk_exposure_score ?? "N/A"}</span></div>
            <div className="system-row"><span>Peak Congestion</span><span>{summaryFromLatestRun?.peak_congestion ?? "N/A"}</span></div>
            <div className="system-row"><span>Response Time</span><span>{summaryFromLatestRun?.time_to_first_response ?? "N/A"}</span></div>
            <div className="system-row"><span>Containment Time</span><span>{summaryFromLatestRun?.time_to_containment ?? "N/A"}</span></div>
            <div className="system-row"><span>Outcome</span><span>{summaryFromLatestRun?.outcome_quality ?? "N/A"}</span></div>
          </div>
        </Panel>

        <Panel title="Trade-Off Interpretation" subtitle="Safety-first ranking logic: valid route -> unsafe segments -> hazard -> congestion -> time">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Fastest</span><span>{fastest ? fastest.replaceAll("_", " ") : "N/A"}</span></div>
            <div className="system-row"><span>Safest</span><span>{safest ? safest.replaceAll("_", " ") : "N/A"}</span></div>
            <div className="system-row"><span>Recommended</span><span>{recommended ? recommended.replaceAll("_", " ") : "N/A"}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Strategy Results Table" subtitle="Same hazard scenario reused across static, shortest, and twin-optimized strategies for fair comparison">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-[var(--fg-muted)]">
                  <th className="px-2 py-2">Strategy</th>
                  <th className="px-2 py-2">Evacuation Time</th>
                  <th className="px-2 py-2">Hazard Exposure</th>
                  <th className="px-2 py-2">Peak Congestion</th>
                  <th className="px-2 py-2">Distance</th>
                  <th className="px-2 py-2">Selected Exit</th>
                  <th className="px-2 py-2">Response Time</th>
                </tr>
              </thead>
              <tbody>
                {selectedScenarioRows.map((row) => (
                  <tr key={`${row.scenario_id}-${row.strategy}`} className="border-t border-white/8">
                    <td className="px-2 py-2">{row.strategy.replaceAll("_", " ")}</td>
                    <td className="px-2 py-2">{row.evacuation_time ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.hazard_exposure_score ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.peak_congestion ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.distance_travelled ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.selected_exit ?? "N/A"}</td>
                    <td className="px-2 py-2">{experimentResults?.scenario_results.find((item) => item.scenario_id === row.scenario_id && item.strategy === row.strategy)?.time_to_first_response ?? "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Evacuation Time by Strategy">
          <div className="space-y-2">
            {chartRows.map((row) => (
              <div key={`evac-${row.strategy}`}>
                <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]"><span>{row.strategy.replaceAll("_", " ")}</span><span>{row.evacuation_time ?? "N/A"}</span></div>
                <div className="h-2 rounded-full bg-white/10"><div className="h-full bg-[var(--accent-cyan)]" style={{ width: `${Math.max(4, ((row.evacuation_time ?? 0) / maxEvacuation) * 100)}%` }} /></div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Hazard Exposure by Strategy">
          <div className="space-y-2">
            {chartRows.map((row) => (
              <div key={`hazard-${row.strategy}`}>
                <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]"><span>{row.strategy.replaceAll("_", " ")}</span><span>{row.hazard_exposure_score ?? "N/A"}</span></div>
                <div className="h-2 rounded-full bg-white/10"><div className="h-full bg-[var(--accent-red)]" style={{ width: `${Math.max(4, ((row.hazard_exposure_score ?? 0) / maxExposure) * 100)}%` }} /></div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Peak Congestion by Strategy">
          <div className="space-y-2">
            {chartRows.map((row) => (
              <div key={`congestion-${row.strategy}`}>
                <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]"><span>{row.strategy.replaceAll("_", " ")}</span><span>{row.peak_congestion ?? "N/A"}</span></div>
                <div className="h-2 rounded-full bg-white/10"><div className="h-full bg-[var(--accent-orange)]" style={{ width: `${Math.max(4, ((row.peak_congestion ?? 0) / maxCongestion) * 100)}%` }} /></div>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <SimulationRunsPanel runs={runs} />
      </section>

      <section className="mt-4">
        <Panel title="Experiment History" subtitle="Recent deterministic scenario experiment records">
          {(experimentResults?.scenario_results ?? []).length === 0 ? <p className="text-sm text-[var(--fg-muted)]">No experiment runs yet.</p> : null}
          <ul className="space-y-2 text-sm">
            {(experimentResults?.scenario_results ?? []).slice(0, 8).map((item) => (
              <li key={item.run_id} className="rounded-2xl border border-white/8 bg-white/4 p-3">
                <div className="flex items-center justify-between gap-3"><span>{item.scenario_name}</span><span>{item.strategy.replaceAll("_", " ")}</span></div>
                <p className="mt-1 text-xs text-[var(--fg-muted)]">Outcome {item.outcome_quality ?? "N/A"} • Evacuation {item.evacuation_time ?? "N/A"} • Containment {item.time_to_containment ?? "N/A"}</p>
              </li>
            ))}
          </ul>
        </Panel>
      </section>
    </div>
  );
}
