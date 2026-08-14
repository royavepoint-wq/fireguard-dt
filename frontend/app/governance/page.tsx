import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";

export default function GovernancePage() {
  return (
    <div>
      <PageHeader
        title="Governance & Security"
        description="Control posture and trust framework baseline for FireGuard DT."
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard label="Device & Communication" value="Active" helper="Encrypted telemetry channels" statusLabel="ACTIVE" statusTone="safe" />
        <MetricCard label="Platform Security" value="Monitored" helper="Access and runtime checks" statusLabel="ACTIVE" statusTone="safe" />
        <MetricCard label="Sensor Trust" value="Baseline" helper="Integrity policy applied" statusLabel="ACTIVE" statusTone="safe" />
        <MetricCard label="Resilience" value="Baseline" helper="Fallback paths configured" statusLabel="ACTIVE" statusTone="safe" />
        <MetricCard label="Human Approval" value="Enabled" helper="Decision gating enforced" statusLabel="ENABLED" statusTone="info" />
        <MetricCard label="Audit Log" value="Enabled" helper="Action history retained" statusLabel="ENABLED" statusTone="info" />
      </section>
    </div>
  );
}
