"use client";

import { useEffect, useMemo, useState } from "react";

import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getFireRiskExplanation, getFireRiskFeatureImportance } from "@/lib/api";
import type { FeatureContribution, FireRiskExplanationResponse, FireRiskFeatureImportanceResponse, StatusTone } from "@/lib/types";

function asPercent(value: number | undefined): string {
  if (typeof value !== "number") {
    return "N/A";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function toneFromConsistency(status: string | undefined): StatusTone {
  if (status === "PHYSICALLY_CONSISTENT") {
    return "safe";
  }
  if (status === "INSUFFICIENT_MULTI_SENSOR_SUPPORT") {
    return "warning";
  }
  return "critical";
}

function toneFromRiskClass(label: string | undefined): StatusTone {
  if (label === "CRITICAL") {
    return "critical";
  }
  if (label === "WARNING") {
    return "warning";
  }
  return "safe";
}

function contributionColor(direction: string): string {
  if (direction === "increases_risk") {
    return "bg-[var(--accent-red)]";
  }
  if (direction === "decreases_risk") {
    return "bg-[var(--accent-green)]";
  }
  return "bg-[var(--fg-muted)]";
}

function ContributionRows({ rows }: { rows: FeatureContribution[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-[var(--fg-muted)]">No contributors available.</p>;
  }

  const maxAbs = Math.max(...rows.map((row) => Math.abs(row.contribution)), 0.00001);

  return (
    <div className="space-y-3">
      {rows.map((row) => {
        const width = Math.max(6, (Math.abs(row.contribution) / maxAbs) * 100);
        return (
          <div key={`${row.feature}-${row.direction}`}>
            <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]">
              <span>{row.feature_label}</span>
              <span>{row.contribution.toFixed(4)}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/10">
              <div className={`h-full ${contributionColor(row.direction)}`} style={{ width: `${width}%` }} />
            </div>
            <div className="mt-1 text-[11px] text-[var(--fg-muted)]">Value: {row.value.toFixed(3)} | {row.direction.replaceAll("_", " ")}</div>
          </div>
        );
      })}
    </div>
  );
}

export default function ExplainabilityPage() {
  const [explanation, setExplanation] = useState<FireRiskExplanationResponse | null>(null);
  const [importance, setImportance] = useState<FireRiskFeatureImportanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [nextExplanation, nextImportance] = await Promise.all([
          getFireRiskExplanation(),
          getFireRiskFeatureImportance(),
        ]);
        if (!active) {
          return;
        }
        setExplanation(nextExplanation);
        setImportance(nextImportance);
        setError(null);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load explainability data.");
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
    }, 2000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const topGlobal = useMemo(() => (importance?.features ?? []).slice(0, 6), [importance]);

  return (
    <div>
      <PageHeader
        title="Explainable AI"
        description="Trust layer with local explanation, physical consistency checks, and global feature importance for live fire-risk predictions."
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Predicted Class"
          value={explanation?.predicted_class ?? "N/A"}
          helper="Current live inference"
          statusLabel={explanation?.predicted_class ?? "N/A"}
          statusTone={toneFromRiskClass(explanation?.predicted_class)}
        />
        <MetricCard label="Confidence" value={asPercent(explanation?.confidence)} helper="Prediction confidence" />
        <MetricCard
          label="Critical Probability"
          value={asPercent(explanation?.critical_probability)}
          helper="P(class = CRITICAL)"
          statusLabel={asPercent(explanation?.critical_probability)}
          statusTone="warning"
        />
        <MetricCard
          label="Explanation Method"
          value={explanation?.explanation_method ?? "N/A"}
          helper={`Model ${explanation?.model_version ?? "N/A"}`}
          statusLabel={explanation?.prediction_source ?? "N/A"}
          statusTone="info"
        />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel
          title="Physical Consistency Check"
          subtitle="Deterministic safety guardrail on top of statistical model output"
          action={<StatusBadge label={explanation?.physical_consistency.status ?? "N/A"} tone={toneFromConsistency(explanation?.physical_consistency.status)} />}
        >
          <p className="text-sm text-[var(--fg-muted)]">{explanation?.physical_consistency.message ?? "Waiting for live state..."}</p>
          <div className="mt-3 space-y-2 text-sm">
            {Object.entries(explanation?.physical_consistency.checks ?? {}).map(([key, value]) => (
              <div key={key} className="system-row">
                <span>{key.replaceAll("_", " ")}</span>
                <span>{value ? "pass" : "fail"}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Global Feature Importance" subtitle="Model-level explanation aggregated across training behavior">
          {topGlobal.length === 0 ? <p className="text-sm text-[var(--fg-muted)]">No importance data available.</p> : null}
          <div className="space-y-3">
            {topGlobal.map((item) => (
              <div key={item.feature}>
                <div className="mb-1 flex items-center justify-between text-xs text-[var(--fg-muted)]">
                  <span>{item.feature_label}</span>
                  <span>{(item.normalized_importance * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full bg-[var(--accent-cyan)]" style={{ width: `${Math.max(4, item.normalized_importance * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Top Risk-Increasing Contributors" subtitle="Features pushing this prediction toward a higher fire-risk class">
          <ContributionRows rows={explanation?.top_positive_contributors ?? []} />
        </Panel>

        <Panel title="Top Risk-Reducing Contributors" subtitle="Features pulling this prediction toward a lower fire-risk class">
          <ContributionRows rows={explanation?.top_negative_contributors ?? []} />
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Live Input Trace" subtitle="Raw feature values passed into the prediction and explanation pipeline">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 text-sm">
            {Object.entries(explanation?.input_features ?? {}).map(([key, value]) => (
              <div key={key} className="system-row">
                <span>{key.replaceAll("_", " ")}</span>
                <span>{String(value)}</span>
              </div>
            ))}
          </div>
          {loading ? <p className="mt-3 text-sm text-[var(--fg-muted)]">Loading explainability streams...</p> : null}
          {error ? <p className="mt-3 text-sm text-[var(--accent-red)]">{error}</p> : null}
        </Panel>
      </section>
    </div>
  );
}
