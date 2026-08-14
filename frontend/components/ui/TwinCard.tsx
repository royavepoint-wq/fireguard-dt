import { type TwinMetric } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type TwinCardProps = {
  title: string;
  status: string;
  lastUpdated?: string;
  tone?: "safe" | "warning" | "critical" | "info" | "muted";
  metrics: TwinMetric[];
  onClick?: () => void;
};

export function TwinCard({ title, status, lastUpdated, tone = "safe", metrics, onClick }: TwinCardProps) {
  const content = (
    <>
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="panel-title">{title}</h3>
          {lastUpdated ? <p className="panel-subtitle">Last Updated {lastUpdated}</p> : null}
        </div>
        <div className="flex items-center gap-2">
          {onClick ? <span className="text-xs uppercase tracking-[0.2em] text-[var(--fg-muted)]">View Details</span> : null}
          <StatusBadge label={status} tone={tone} />
        </div>
      </header>
      <dl className="space-y-2">
        {metrics.map((metric) => (
          <div key={metric.label} className="flex min-w-0 items-center justify-between gap-4 text-sm">
            <dt className="text-[var(--fg-muted)]">{metric.label}</dt>
            <dd className="min-w-0 break-words text-right font-medium text-white">{metric.value}</dd>
          </div>
        ))}
      </dl>
    </>
  );

  if (onClick) {
    return (
      <button type="button" className="panel w-full min-w-0 cursor-pointer text-left transition hover:-translate-y-0.5 hover:border-cyan-400/45" onClick={onClick}>
        {content}
      </button>
    );
  }

  return (
    <section className="panel min-w-0 w-full">
      {content}
    </section>
  );
}
