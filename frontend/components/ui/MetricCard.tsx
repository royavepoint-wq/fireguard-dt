import { type ReactNode } from "react";
import { type MetricValue, type StatusTone } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type MetricCardProps = {
  label: string;
  value: MetricValue;
  helper?: string;
  statusLabel?: string;
  statusTone?: StatusTone;
  icon?: ReactNode;
};

export function MetricCard({
  label,
  value,
  helper,
  statusLabel,
  statusTone = "info",
  icon,
}: MetricCardProps) {
  return (
    <article className="card min-w-0 w-full">
      <div className="mb-3 flex items-start justify-between gap-3">
        <p className="card-label">{label}</p>
        {icon ? <span className="text-[var(--accent-cyan)]">{icon}</span> : null}
      </div>
      <p className="card-value break-words leading-tight">{value}</p>
      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="min-w-0 text-xs text-[var(--fg-muted)]">{helper}</p>
        {statusLabel ? <StatusBadge label={statusLabel} tone={statusTone} /> : null}
      </div>
    </article>
  );
}
