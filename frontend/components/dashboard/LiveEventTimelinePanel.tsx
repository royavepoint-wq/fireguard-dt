"use client";

import { useEffect, useState } from "react";
import { EventTimeline } from "@/components/ui/EventTimeline";
import { EmptyState } from "@/components/ui/EmptyState";
import { Panel } from "@/components/ui/Panel";
import { getEvents } from "@/lib/api";
import type { DigitalTwinEvent } from "@/lib/types";

type EventFilter = "all" | "fire_environment" | "building_infrastructure" | "occupancy_evacuation" | "emergency_response" | "orchestrator";

const FILTERS: { label: string; value: EventFilter }[] = [
  { label: "All", value: "all" },
  { label: "Fire", value: "fire_environment" },
  { label: "Building", value: "building_infrastructure" },
  { label: "Occupancy", value: "occupancy_evacuation" },
  { label: "Response", value: "emergency_response" },
  { label: "Orchestrator", value: "orchestrator" },
];

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

export function LiveEventTimelinePanel({
  externalEvents,
  externalLoading,
  externalError,
}: {
  externalEvents?: DigitalTwinEvent[];
  externalLoading?: boolean;
  externalError?: string | null;
}) {
  const [events, setEvents] = useState<DigitalTwinEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<EventFilter>("all");
  const usingExternalSource = externalEvents !== undefined;
  const displayedEvents = externalEvents ?? events;
  const displayedLoading = usingExternalSource ? Boolean(externalLoading) : loading;
  const displayedError = usingExternalSource ? (externalError ?? null) : error;

  async function refreshEvents(showSpinner = true) {
    if (showSpinner) {
      setLoading(true);
    }
    setError(null);

    try {
      const nextEvents = await getEvents();
      setEvents(nextEvents.slice().reverse());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load live events.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (usingExternalSource) {
      return;
    }

    let active = true;

    async function loadOnMount() {
      try {
        const nextEvents = await getEvents();
        if (!active) {
          return;
        }
        setEvents(nextEvents.slice().reverse());
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load live events.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadOnMount();

    const timer = window.setInterval(() => {
      void refreshEvents(false);
    }, 1000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [usingExternalSource]);

  const filteredEvents = activeFilter === "all"
    ? displayedEvents
    : displayedEvents.filter((event) => event.source_twin === activeFilter);

  return (
    <Panel
      title="Live Event Timeline"
      subtitle="Integrated simulation, twin, ML, optimizer, response, and governance events"
      action={<button type="button" className="filter-btn" onClick={() => void refreshEvents()}>Refresh</button>}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.value}
            type="button"
            className={filter.value === activeFilter ? "filter-btn filter-btn-active" : "filter-btn"}
            onClick={() => setActiveFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {displayedLoading ? <p className="text-sm text-[var(--fg-muted)]">Loading recent events...</p> : null}
      {!displayedLoading && displayedError ? (
        <div className="space-y-4">
          <p className="text-sm text-[var(--accent-red)]">{displayedError}</p>
          <button type="button" className="action-btn" onClick={() => void refreshEvents()}>
            Retry Event Load
          </button>
        </div>
      ) : null}
      {!displayedLoading && !displayedError && filteredEvents.length > 0 ? (
        <EventTimeline
          events={filteredEvents.map((event) => ({
            ...event,
            timestamp: formatTimestamp(event.timestamp),
          }))}
        />
      ) : null}
      {!displayedLoading && !displayedError && filteredEvents.length === 0 ? (
        <EmptyState
          title="No recent events"
          description="Run the emergency demo to stream meaningful cross-system events."
          bullets={["Simulation lifecycle", "Governance decisions", "Route recalculations"]}
        />
      ) : null}
    </Panel>
  );
}