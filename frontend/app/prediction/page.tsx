"use client";

import { useEffect, useMemo, useState } from "react";

import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getDigitalTwinState, getFireRiskMetrics, getFireRiskModelInfo } from "@/lib/api";
import type { CombinedDigitalTwinState, FireRiskMetrics, FireRiskModelInfo, RiskLevel, StatusTone } from "@/lib/types";

const PROBABILITY_ORDER: RiskLevel[] = ["NORMAL", "WARNING", "CRITICAL"];

function asPercent(value: number | undefined): string {
  if (typeof value !== "number") {
    return "N/A";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function toneForRisk(level: RiskLevel): StatusTone {
  if (level === "CRITICAL") {
    return "critical";
  }
  if (level === "WARNING") {
    return "warning";
  }
  return "safe";
}

export default function PredictionPage() {
  const [state, setState] = useState<CombinedDigitalTwinState | null>(null);
  const [modelInfo, setModelInfo] = useState<FireRiskModelInfo | null>(null);
  const [metrics, setMetrics] = useState<FireRiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [nextState, nextInfo, nextMetrics] = await Promise.all([
          getDigitalTwinState(),
          getFireRiskModelInfo(),
          getFireRiskMetrics(),
        ]);

        if (!active) {
          return;
        }

        setState(nextState);
        setModelInfo(nextInfo);
        setMetrics(nextMetrics);
        setError(null);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load predictive intelligence data.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();
    const interval = window.setInterval(() => {
      void load();
    }, 1000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const fireTwin = state?.fire_twin ?? null;
  const modelOnline = modelInfo?.loaded_successfully ?? false;
  const selectedModelName = modelOnline ? modelInfo?.model_name ?? metrics?.selected_model ?? "N/A" : "ML Model Unavailable";
  const modelStatusLabel = modelOnline ? "MODEL ONLINE" : "MODEL FALLBACK";

  const sensorRows = useMemo(() => {
    if (!state) {
      return [];
    }

    const sprinklerActive = state.building_twin.sprinklers.some((sprinkler) => sprinkler.zone_id === "zone-1a" && sprinkler.is_active);
    const hvacZone3 = state.building_twin.hvac_zones.find((zone) => zone.hvac_zone_id === "hvac-zone-3");

    return [
      ["Temperature", `${fireTwin?.temperature?.toFixed(2) ?? "0.00"} C`],
      ["Temperature Rate", `${fireTwin?.temperature_rate?.toFixed(2) ?? "0.00"} C/s`],
      ["Smoke", `${fireTwin?.smoke_level?.toFixed(3) ?? "0.000"}`],
      ["CO", `${fireTwin?.co_level?.toFixed(2) ?? "0.00"}`],
      ["CO2", `${fireTwin?.co2_level?.toFixed(2) ?? "0.00"}`],
      ["Humidity", `${fireTwin?.humidity?.toFixed(2) ?? "0.00"}%`],
      ["Electrical Load", `${fireTwin?.electrical_load?.toFixed(2) ?? "0.00"}%`],
      ["Occupancy", String(state.occupancy_twin.total_occupancy)],
      ["HVAC Running", hvacZone3?.status === "ISOLATED" ? "0" : "1"],
      ["Sprinkler Active", sprinklerActive ? "1" : "0"],
    ];
  }, [fireTwin, state]);

  return (
    <div>
      <PageHeader
        title="Predictive Intelligence"
        description="ML fire-risk pipeline with live Fire & Environment Twin inference and test-set performance evidence."
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Selected Model" value={selectedModelName} helper={modelOnline ? "Selected by critical-recall-first policy" : modelInfo?.error ?? "Fallback active"} statusLabel={modelStatusLabel} statusTone={modelOnline ? "safe" : "warning"} />
        <MetricCard label="Accuracy" value={metrics ? asPercent(metrics.accuracy) : "N/A"} helper="Test set" />
        <MetricCard label="Macro F1" value={metrics ? asPercent(metrics.macro_f1) : "N/A"} helper="Macro average" />
        <MetricCard label="Critical Recall" value={metrics ? asPercent(metrics.critical_recall) : "N/A"} helper="Primary safety metric" statusLabel={metrics ? asPercent(metrics.critical_recall) : "N/A"} statusTone="warning" />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.3fr_1fr]">
        <Panel title="Current Prediction" subtitle="Live inference from Fire & Environment Twin sensors">
          {loading ? <p className="text-sm text-[var(--fg-muted)]">Loading model metrics...</p> : null}
          {fireTwin ? (
            <div>
              <div className="mb-3 flex items-center gap-3">
                <StatusBadge label={fireTwin.risk_level} tone={toneForRisk(fireTwin.risk_level)} />
                <p className="text-sm text-[var(--fg-muted)]">Confidence {asPercent(fireTwin.prediction_confidence)}</p>
              </div>
              <p className="text-sm text-[var(--fg-muted)]">
                Source: {fireTwin.prediction_source} | Model: {fireTwin.model_version ?? "N/A"} | Last update: {new Date(fireTwin.last_updated).toLocaleString()}
              </p>

              <div className="mt-4 space-y-3">
                {PROBABILITY_ORDER.map((label) => {
                  const value = fireTwin.risk_probabilities[label] ?? 0;
                  return (
                    <div key={label}>
                      <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]">
                        <span>{label}</span>
                        <span>{asPercent(value)}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-white/10">
                        <div
                          className={label === "CRITICAL" ? "h-full bg-[var(--accent-red)]" : label === "WARNING" ? "h-full bg-[var(--accent-orange)]" : "h-full bg-[var(--accent-green)]"}
                          style={{ width: `${Math.max(2, value * 100)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
          {error ? <p className="mt-3 text-sm text-[var(--accent-red)]">{error}</p> : null}
        </Panel>

        <Panel title="Model Health" subtitle="Startup model-load state and fallback disclosure">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Status</span><span>{modelInfo?.status ?? (modelOnline ? "ONLINE" : "FALLBACK")}</span></div>
            <div className="system-row"><span>Model Version</span><span>{modelInfo?.model_version ?? "N/A"}</span></div>
            <div className="system-row"><span>Prediction Source</span><span>{fireTwin?.prediction_source ?? modelInfo?.prediction_source ?? "NOT_AVAILABLE"}</span></div>
            <div className="system-row"><span>Random Seed</span><span>{typeof modelInfo?.random_state === "number" ? modelInfo.random_state : "N/A"}</span></div>
            <div className="system-row"><span>Dataset Type</span><span>{modelInfo?.dataset_type === "synthetic" ? "Synthetic Training Dataset" : (modelInfo?.dataset_type ?? "N/A")}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Panel title="Current Sensor Inputs" subtitle="Physical state to ML prediction traceability">
          <div className="grid gap-2 sm:grid-cols-2">
            {sensorRows.map(([label, value]) => (
              <div key={label} className="system-row text-sm">
                <span>{label}</span>
                <span>{value}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Selected Model Metrics" subtitle="Unseen test set performance">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>ROC-AUC (OvR)</span><span>{metrics ? asPercent(metrics.roc_auc) : "N/A"}</span></div>
            <div className="system-row"><span>Macro Precision</span><span>{metrics ? asPercent(metrics.macro_precision) : "N/A"}</span></div>
            <div className="system-row"><span>Macro Recall</span><span>{metrics ? asPercent(metrics.macro_recall) : "N/A"}</span></div>
            <div className="system-row"><span>Critical Precision</span><span>{metrics ? asPercent(metrics.critical_precision) : "N/A"}</span></div>
            <div className="system-row"><span>Critical F1</span><span>{metrics ? asPercent(metrics.critical_f1) : "N/A"}</span></div>
            <div className="system-row"><span>Weighted F1</span><span>{metrics ? asPercent(metrics.weighted_f1) : "N/A"}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Model Comparison" subtitle="Logistic Regression vs Random Forest vs Gradient Boosting">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-[var(--fg-muted)]">
                  <th className="px-2 py-2">Model</th>
                  <th className="px-2 py-2">Accuracy</th>
                  <th className="px-2 py-2">Macro F1</th>
                  <th className="px-2 py-2">ROC-AUC</th>
                  <th className="px-2 py-2">Critical Recall</th>
                </tr>
              </thead>
              <tbody>
                {(modelInfo?.model_comparison ?? []).map((row) => {
                  const model = String(row.Model ?? "Unknown");
                  const selected = model === selectedModelName;
                  return (
                    <tr key={model} className={selected ? "bg-white/10" : "border-t border-white/8"}>
                      <td className="px-2 py-2">{model}</td>
                      <td className="px-2 py-2">{asPercent(Number(row.Accuracy ?? 0))}</td>
                      <td className="px-2 py-2">{asPercent(Number(row["Macro F1"] ?? 0))}</td>
                      <td className="px-2 py-2">{asPercent(Number(row["ROC-AUC"] ?? 0))}</td>
                      <td className="px-2 py-2">{asPercent(Number(row["Critical Recall"] ?? 0))}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Confusion Matrix" subtitle="Selected model test-set confusion matrix (NORMAL, WARNING, CRITICAL)">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-[var(--fg-muted)]">
                  <th className="px-2 py-2">Actual \ Pred</th>
                  <th className="px-2 py-2">NORMAL</th>
                  <th className="px-2 py-2">WARNING</th>
                  <th className="px-2 py-2">CRITICAL</th>
                </tr>
              </thead>
              <tbody>
                {(modelInfo?.confusion_matrix ?? []).map((row) => (
                  <tr key={row.actual} className="border-t border-white/8">
                    <td className="px-2 py-2">{row.actual}</td>
                    <td className="px-2 py-2">{row.NORMAL}</td>
                    <td className="px-2 py-2">{row.WARNING}</td>
                    <td className="px-2 py-2">{row.CRITICAL}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Synthetic Training Dataset Disclaimer" subtitle="Academic prototype scope and limitations">
          <p className="text-sm text-[var(--fg-muted)]">
            {modelInfo?.synthetic_dataset_disclaimer ?? "Model trained on synthetic fire-sensor data generated for academic simulation. Results demonstrate the prototype pipeline and are not certified for real building safety deployment."}
          </p>
        </Panel>
      </section>
    </div>
  );
}
