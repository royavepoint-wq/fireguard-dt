import { type StatusTone } from "@/lib/types";

type StatusBadgeProps = {
  label: string;
  tone?: StatusTone;
};

const toneClasses: Record<StatusTone, string> = {
  safe: "badge-safe",
  warning: "badge-warning",
  critical: "badge-critical",
  info: "badge-info",
  muted: "badge-muted",
};

export function StatusBadge({ label, tone = "info" }: StatusBadgeProps) {
  return <span className={`badge max-w-full break-words text-center leading-tight ${toneClasses[tone]}`}>{label}</span>;
}
