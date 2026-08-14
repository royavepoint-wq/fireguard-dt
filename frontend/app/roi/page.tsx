"use client";

import { useEffect, useMemo, useState } from "react";

import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import {
  calculateRoi,
  getExperimentResults,
  getFireRiskMetrics,
  getFireRiskModelInfo,
  getResultsCsvExportUrl,
  getResultsJsonExportUrl,
  getRoiAssumptions,
  getRoiScenarios,
  refreshEvidencePackage,
} from "@/lib/api";
import type { ExperimentResultsResponse, FireRiskMetrics, FireRiskModelInfo, RoiAssumptions, RoiCalculationResult, RoiScenario } from "@/lib/types";

function money(value: number, currency = "SGD"): string {
  return `${currency} ${value.toLocaleString("en-SG", { maximumFractionDigits: 0 })}`;
}

export default function RoiPage() {
  const [scenario, setScenario] = useState<RoiScenario>("BASE");
  const [assumptions, setAssumptions] = useState<Record<RoiScenario, RoiAssumptions>>({} as Record<RoiScenario, RoiAssumptions>);
  const [result, setResult] = useState<RoiCalculationResult | null>(null);
  const [modelMetrics, setModelMetrics] = useState<FireRiskMetrics | null>(null);
  const [modelInfo, setModelInfo] = useState<FireRiskModelInfo | null>(null);
  const [experimentResults, setExperimentResults] = useState<ExperimentResultsResponse | null>(null);
  const [evidenceStatus, setEvidenceStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [scenarioSet, assumptionSet, experimentSet, mlMetrics, mlInfo] = await Promise.all([
          getRoiScenarios(),
          getRoiAssumptions(),
          getExperimentResults(),
          getFireRiskMetrics(),
          getFireRiskModelInfo(),
        ]);
        if (!active) {
          return;
        }
        const map = Object.fromEntries(scenarioSet.scenarios.map((item) => [item.scenario, item])) as Record<RoiScenario, RoiAssumptions>;
        const merged = { ...map, ...Object.fromEntries(assumptionSet.scenarios.map((item) => [item.scenario, item])) } as Record<RoiScenario, RoiAssumptions>;
        setAssumptions(merged);
        const baseResult = await calculateRoi({ scenario: "BASE" });
        if (!active) {
          return;
        }
        setExperimentResults(experimentSet);
        setModelMetrics(mlMetrics);
        setModelInfo(mlInfo);
        setResult(baseResult);
        setError(null);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load ROI analytics.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const activeAssumption = assumptions[scenario];

  const recalculate = async () => {
    if (!activeAssumption) {
      return;
    }
    try {
      const next = await calculateRoi({ scenario, assumptions_override: activeAssumption });
      setResult(next);
      setError(null);
    } catch (calcError) {
      setError(calcError instanceof Error ? calcError.message : "Unable to recalculate ROI.");
    }
  };

  const scenarioRoiBars = useMemo(() => {
    const rows = Object.values(assumptions);
    return rows.map((item) => ({ key: item.scenario, value: item.scenario === result?.scenario ? result.three_year_roi_percent : null }));
  }, [assumptions, result]);

  const strategyRows = experimentResults?.strategy_comparison ?? [];
  const governanceRows = experimentResults?.governance_comparison ?? [];
  const latestResponse = experimentResults?.scenario_results.find((item) => item.strategy === "TWIN_OPTIMIZED" && item.approval_mode === "AUTO_APPROVE") ?? null;

  const triggerEvidenceRefresh = async () => {
    try {
      const status = await refreshEvidencePackage();
      setEvidenceStatus(`Evidence package refreshed: ${status.path}`);
      setError(null);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unable to refresh evidence package.");
    }
  };

  return (
    <div>
      <PageHeader
        title="ROI & Analytics"
        description="ROI model with explicit assumption disclosure and experiment-linked technical evidence."
        actions={
          <div className="flex gap-2">
            {(["CONSERVATIVE", "BASE", "OPTIMISTIC"] as RoiScenario[]).map((option) => (
              <button key={option} type="button" className={scenario === option ? "filter-btn filter-btn-active" : "filter-btn"} onClick={() => setScenario(option)}>{option}</button>
            ))}
            <button type="button" className="action-btn" onClick={() => void recalculate()}>Recalculate</button>
            <button type="button" className="filter-btn" onClick={() => void triggerEvidenceRefresh()}>Refresh Evidence</button>
            <a className="filter-btn" href={getResultsJsonExportUrl()} target="_blank" rel="noreferrer">Export Results JSON</a>
            <a className="filter-btn" href={getResultsCsvExportUrl("scenario_comparison")} target="_blank" rel="noreferrer">Export Results CSV</a>
          </div>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Initial Investment" value={result ? money(result.initial_investment, result.currency) : "N/A"} helper="Illustrative Project Assumption" statusLabel={scenario} statusTone="info" />
        <MetricCard label="Annual Benefit" value={result ? money(result.annual_benefit, result.currency) : "N/A"} helper="Illustrative Project Assumption" statusLabel="ASSUMPTION" statusTone="warning" />
        <MetricCard label="Payback Period" value={result?.payback_statement ?? "N/A"} helper="Computed from monthly net benefit" statusLabel="MODEL" statusTone="info" />
        <MetricCard label="Base 3-Year ROI" value={result ? `${result.three_year_roi_percent.toFixed(2)}%` : "N/A"} helper="Illustrative scenario result" statusLabel="ILLUSTRATIVE" statusTone="warning" />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Cost Breakdown" subtitle="Illustrative Project Assumption (SGD)">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>IoT</span><span>{result ? money(result.cost_breakdown.iot ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Platform</span><span>{result ? money(result.cost_breakdown.platform ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>ML</span><span>{result ? money(result.cost_breakdown.ml ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Security</span><span>{result ? money(result.cost_breakdown.security ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Training</span><span>{result ? money(result.cost_breakdown.training ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Operations</span><span>{result ? money(result.cost_breakdown.operations ?? 0, result.currency) : "N/A"}</span></div>
          </div>
        </Panel>

        <Panel title="Benefit Breakdown" subtitle="Illustrative Project Assumption (SGD)">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Downtime Reduction</span><span>{result ? money(result.benefit_breakdown.downtime_reduction ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Damage Risk Reduction</span><span>{result ? money(result.benefit_breakdown.damage_risk_reduction ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Maintenance Savings</span><span>{result ? money(result.benefit_breakdown.maintenance_savings ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Response Efficiency</span><span>{result ? money(result.benefit_breakdown.response_efficiency ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>False Alarm Reduction</span><span>{result ? money(result.benefit_breakdown.false_alarm_reduction ?? 0, result.currency) : "N/A"}</span></div>
            <div className="system-row"><span>Compliance Value</span><span>{result ? money(result.benefit_breakdown.compliance_value ?? 0, result.currency) : "N/A"}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="3-Year Cumulative Cost vs Benefit">
          <div className="space-y-3">
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]"><span>3-Year Cost</span><span>{result ? money(result.three_year_cost, result.currency) : "N/A"}</span></div>
              <div className="h-2 rounded-full bg-white/10"><div className="h-full bg-[var(--accent-red)]" style={{ width: result ? "100%" : "0%" }} /></div>
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]"><span>3-Year Benefit</span><span>{result ? money(result.three_year_benefit, result.currency) : "N/A"}</span></div>
              <div className="h-2 rounded-full bg-white/10"><div className="h-full bg-[var(--accent-green)]" style={{ width: result ? `${Math.min(100, (result.three_year_benefit / Math.max(1, result.three_year_cost)) * 100)}%` : "0%" }} /></div>
            </div>
          </div>
        </Panel>

        <Panel title="ROI by Scenario">
          <div className="space-y-2 text-sm">
            {scenarioRoiBars.map((item) => (
              <div key={item.key} className="system-row">
                <span>{item.key}</span>
                <span>{item.value === null ? "Recalculate to view" : `${item.value.toFixed(2)}%`}</span>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Assumption Editor" subtitle="Adjust key assumptions and recalculate">
          {activeAssumption ? (
            <div className="grid gap-3 md:grid-cols-2">
              <label className="form-field"><span>Initial Investment (IoT)</span><input value={activeAssumption.iot_sensor_integration} onChange={(e) => setAssumptions((prev) => ({ ...prev, [scenario]: { ...activeAssumption, iot_sensor_integration: Number(e.target.value) || 0 } }))} /></label>
              <label className="form-field"><span>Annual Operating Cost (Cloud)</span><input value={activeAssumption.annual_cloud_operations} onChange={(e) => setAssumptions((prev) => ({ ...prev, [scenario]: { ...activeAssumption, annual_cloud_operations: Number(e.target.value) || 0 } }))} /></label>
              <label className="form-field"><span>Damage Risk Reduction</span><input value={activeAssumption.damage_risk_reduction} onChange={(e) => setAssumptions((prev) => ({ ...prev, [scenario]: { ...activeAssumption, damage_risk_reduction: Number(e.target.value) || 0 } }))} /></label>
              <label className="form-field"><span>Downtime Savings</span><input value={activeAssumption.avoided_downtime} onChange={(e) => setAssumptions((prev) => ({ ...prev, [scenario]: { ...activeAssumption, avoided_downtime: Number(e.target.value) || 0 } }))} /></label>
              <label className="form-field"><span>Maintenance Savings</span><input value={activeAssumption.maintenance_savings} onChange={(e) => setAssumptions((prev) => ({ ...prev, [scenario]: { ...activeAssumption, maintenance_savings: Number(e.target.value) || 0 } }))} /></label>
            </div>
          ) : (
            <p className="text-sm text-[var(--fg-muted)]">N/A</p>
          )}
          <button type="button" className="action-btn mt-4" onClick={() => void recalculate()}>Recalculate</button>
        </Panel>

        <Panel title="Project Impact" subtitle="Technical evidence kept separate from financial assumptions">
          <div className="space-y-2 text-sm">
            {Object.entries(result?.technical_evidence ?? {}).map(([key, value]) => (
              <div key={key} className="system-row"><span>{key.replaceAll("_", " ")}</span><span>{String(value)}</span></div>
            ))}
          </div>
          {evidenceStatus ? <p className="mt-3 text-sm text-[var(--accent-green)]">{evidenceStatus}</p> : null}
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Evaluation Summary" subtitle="Predictive Model Performance, Simulation Strategy Results, Governance Impact, and ROI Scenarios">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Selected Model</span><span>{modelInfo?.model_name ?? "N/A"}</span></div>
            <div className="system-row"><span>Accuracy</span><span>{typeof modelMetrics?.accuracy === "number" ? `${(modelMetrics.accuracy * 100).toFixed(1)}%` : "N/A"}</span></div>
            <div className="system-row"><span>Macro F1</span><span>{typeof modelMetrics?.macro_f1 === "number" ? `${(modelMetrics.macro_f1 * 100).toFixed(1)}%` : "N/A"}</span></div>
            <div className="system-row"><span>Critical Recall</span><span>{typeof modelMetrics?.critical_recall === "number" ? `${(modelMetrics.critical_recall * 100).toFixed(1)}%` : "N/A"}</span></div>
            <div className="system-row"><span>ROC-AUC</span><span>{typeof modelMetrics?.roc_auc === "number" ? `${(modelMetrics.roc_auc * 100).toFixed(1)}%` : "N/A"}</span></div>
            <div className="system-row"><span>First Response Time</span><span>{latestResponse?.time_to_first_response ?? "N/A"}</span></div>
            <div className="system-row"><span>Containment Time</span><span>{latestResponse?.time_to_containment ?? "N/A"}</span></div>
          </div>
        </Panel>

        <Panel title="Results Provenance" subtitle="Differentiate measured technical outputs from illustrative finance assumptions">
          <div className="space-y-3 text-sm">
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="font-semibold text-white">Prediction Accuracy</p>
              <p className="text-[var(--fg-muted)]">{typeof modelMetrics?.accuracy === "number" ? `${(modelMetrics.accuracy * 100).toFixed(1)}%` : "N/A"}</p>
              <p className="text-[var(--fg-muted)]">Source: unseen synthetic test set (MODEL_TEST_RESULT)</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="font-semibold text-white">Hazard Exposure Reduction</p>
              <p className="text-[var(--fg-muted)]">{strategyRows.find((row) => row.strategy === "TWIN_OPTIMIZED")?.hazard_exposure_reduction_vs_static_pct ?? "N/A"}%</p>
              <p className="text-[var(--fg-muted)]">Source: scenario simulation vs Static Plan (SIMULATION_RESULT)</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="font-semibold text-white">3-Year ROI</p>
              <p className="text-[var(--fg-muted)]">{result ? `${result.three_year_roi_percent.toFixed(2)}%` : "N/A"}</p>
              <p className="text-[var(--fg-muted)]">Source: illustrative financial model (ILLUSTRATIVE_ROI)</p>
            </div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Strategy Comparison" subtitle="Static vs Shortest vs Twin Optimized (Evacuation Time, Hazard Exposure, Peak Congestion)">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-[var(--fg-muted)]">
                  <th className="px-2 py-2">Scenario</th>
                  <th className="px-2 py-2">Strategy</th>
                  <th className="px-2 py-2">Time</th>
                  <th className="px-2 py-2">Exposure</th>
                  <th className="px-2 py-2">Congestion</th>
                  <th className="px-2 py-2">Label</th>
                </tr>
              </thead>
              <tbody>
                {strategyRows.map((row) => (
                  <tr key={`${row.scenario_id}-${row.strategy}`} className="border-t border-white/8">
                    <td className="px-2 py-2">{row.scenario_name}</td>
                    <td className="px-2 py-2">{row.strategy.replaceAll("_", " ")}</td>
                    <td className="px-2 py-2">{row.evacuation_time ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.hazard_exposure_score ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.peak_congestion ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.recommendation_label ?? "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Governance Comparison" subtitle="Approved HVAC Isolation vs Rejected HVAC Isolation">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-[var(--fg-muted)]">
                  <th className="px-2 py-2">Scenario</th>
                  <th className="px-2 py-2">Branch</th>
                  <th className="px-2 py-2">Containment</th>
                  <th className="px-2 py-2">Exposure</th>
                  <th className="px-2 py-2">Unsafe Duration</th>
                  <th className="px-2 py-2">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {governanceRows.map((row) => (
                  <tr key={`${row.scenario_id}-${row.branch}`} className="border-t border-white/8">
                    <td className="px-2 py-2">{row.scenario_id}</td>
                    <td className="px-2 py-2">{row.branch.replaceAll("_", " ")}</td>
                    <td className="px-2 py-2">{row.containment_time ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.hazard_exposure_score ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.unsafe_zone_duration ?? "N/A"}</td>
                    <td className="px-2 py-2">{row.outcome_quality ?? "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Executive Summary" subtitle="Final integrated outcome">
          <p className="text-sm text-[var(--fg-muted)]">
            FireGuard DT demonstrates how four interacting Digital Twins combine predictive AI, spatial context, dynamic optimization,
            emergency response, and governed autonomy to support adaptive fire-emergency management.
          </p>
        </Panel>
        <Panel title="Prototype Methodology" subtitle="What is real computation vs simulated vs illustrative">
          <div className="space-y-2 text-sm">
            <p className="text-white">Real computation: ML model training and evaluation, graph optimization, scenario metric calculation, ROI calculation.</p>
            <p className="text-white">Simulated inputs: building sensor streams, occupant behavior, fire/smoke evolution, emergency resource movement.</p>
            <p className="text-white">Illustrative: financial ROI assumptions.</p>
            <p className="text-[var(--fg-muted)]">Academic Digital Twin Prototype: FireGuard DT is an academic simulation and decision-support prototype. It is not certified for real emergency-management deployment.</p>
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Assumption Disclosure" subtitle="Mandatory transparency">
          <p className="text-sm text-[var(--fg-muted)]">
            {result?.assumption_disclosure ?? "ROI values are illustrative project assumptions for academic feasibility analysis. They are not observed production financial results."}
          </p>
          {loading ? <p className="mt-3 text-sm text-[var(--fg-muted)]">Loading ROI model...</p> : null}
          {error ? <p className="mt-3 text-sm text-[var(--accent-red)]">{error}</p> : null}
        </Panel>
      </section>
    </div>
  );
}
