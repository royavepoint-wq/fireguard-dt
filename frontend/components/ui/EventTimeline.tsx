import { type TimelineEvent } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type EventTimelineProps = {
  events: TimelineEvent[];
};

function toneForSeverity(severity?: string) {
  if (severity === "CRITICAL") {
    return "critical" as const;
  }
  if (severity === "WARNING") {
    return "warning" as const;
  }
  return "info" as const;
}

function dotClassForSeverity(severity?: string) {
  if (severity === "CRITICAL") {
    return "bg-[var(--accent-red)]";
  }
  if (severity === "WARNING") {
    return "bg-[var(--accent-orange)]";
  }
  return "bg-[var(--accent-cyan)]";
}

export function EventTimeline({ events }: EventTimelineProps) {
  return (
    <ol className="space-y-4">
      {events.map((event) => (
        <li key={`${event.event_id ?? event.timestamp ?? event.time}-${event.message}`} className="flex gap-3 rounded-2xl border border-white/6 bg-white/4 p-3">
          <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${dotClassForSeverity(event.severity)}`} />
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--fg-muted)]">{event.timestamp ?? event.time}</p>
              {typeof event.payload?.simulation_time === "string" ? <span className="rounded-full border border-cyan-400/20 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-cyan-200">{event.payload.simulation_time}</span> : null}
              {event.severity ? <StatusBadge label={event.severity} tone={toneForSeverity(event.severity)} /> : null}
              {event.source_twin ? <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-[var(--fg-muted)]">{event.source_twin.replaceAll("_", " ")}</span> : null}
              {event.event_type ? <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-[var(--fg-muted)]">{event.event_type.replaceAll("_", " ")}</span> : null}
            </div>
            <p className="text-sm text-white">{event.message}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
