import { Panel } from "@/components/ui/Panel";
import type { SimulationScenario } from "@/lib/types";

type ScenarioPresetPanelProps = {
  scenarios: SimulationScenario[];
  selectedScenarioId: string;
  onSelectScenario: (scenarioId: string) => void;
};

export function ScenarioPresetPanel({ scenarios, selectedScenarioId, onSelectScenario }: ScenarioPresetPanelProps) {
  const readinessLabel = (supportLevel: SimulationScenario["support_level"]) => (supportLevel === "LIMITED" ? "LIMITED" : "READY");

  return (
    <Panel title="Scenario Presets" subtitle="Standard Electrical Fire is fully implemented; other presets apply deterministic parameter variations where supported">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {scenarios.map((scenario) => (
          <button
            key={scenario.scenario_id}
            type="button"
            className={scenario.scenario_id === selectedScenarioId ? "scenario-card scenario-card-active" : "scenario-card"}
            onClick={() => onSelectScenario(scenario.scenario_id)}
          >
            <p className="text-sm font-semibold text-white">{scenario.name}</p>
            <p className="mt-2 text-xs text-[var(--fg-muted)]">{scenario.description}</p>
            <p className="mt-3 text-[10px] uppercase tracking-[0.18em] text-cyan-200">{readinessLabel(scenario.support_level)}</p>
          </button>
        ))}
      </div>
    </Panel>
  );
}