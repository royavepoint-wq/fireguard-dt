"use client";

import { useEffect, useState } from "react";

import {
  getDigitalTwinState,
  getEvents,
  resetDigitalTwin,
  updateBuildingTwin,
  updateFireTwin,
  updateOccupancyTwin,
  updateResponseTwin,
} from "@/lib/api";
import type {
  BuildingTwinState,
  CombinedDigitalTwinState,
  DigitalTwinEvent,
  FireTwinState,
  OccupancyTwinState,
  ResponseTwinState,
} from "@/lib/types";

export type DeveloperActionName =
  | "increase-temperature"
  | "set-smoke-warning"
  | "block-exit-b"
  | "increase-occupancy"
  | "assign-crew-1"
  | "reset-all";

type UseDigitalTwinRuntimeOptions = {
  pollMs?: number;
  includeEvents?: boolean;
};

export function useDigitalTwinRuntime(options: UseDigitalTwinRuntimeOptions = {}) {
  const pollMs = options.pollMs ?? 2000;
  const includeEvents = options.includeEvents ?? false;

  const [systemState, setSystemState] = useState<CombinedDigitalTwinState | null>(null);
  const [events, setEvents] = useState<DigitalTwinEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<DeveloperActionName | null>(null);

  async function refresh(showSpinner = false) {
    if (showSpinner) {
      setLoading(true);
    }
    setError(null);

    try {
      const results = await Promise.all([
        getDigitalTwinState(),
        includeEvents ? getEvents() : Promise.resolve([] as DigitalTwinEvent[]),
      ]);
      const nextState = results[0];
      const nextEvents = results[1].slice().reverse();
      setSystemState(nextState);
      if (includeEvents) {
        setEvents(nextEvents);
      }
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unable to load digital twin runtime.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadOnMount() {
      try {
        const results = await Promise.all([
          getDigitalTwinState(),
          includeEvents ? getEvents() : Promise.resolve([] as DigitalTwinEvent[]),
        ]);
        const nextState = results[0];
        const nextEvents = results[1].slice().reverse();
        if (!active) {
          return;
        }
        setSystemState(nextState);
        if (includeEvents) {
          setEvents(nextEvents);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load digital twin runtime.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadOnMount();

    const timer = window.setInterval(() => {
      void (async () => {
        try {
          const results = await Promise.all([
            getDigitalTwinState(),
            includeEvents ? getEvents() : Promise.resolve([] as DigitalTwinEvent[]),
          ]);
          if (!active) {
            return;
          }
          setSystemState(results[0]);
          if (includeEvents) {
            setEvents(results[1].slice().reverse());
          }
          setError(null);
        } catch (pollError) {
          if (active) {
            setError(pollError instanceof Error ? pollError.message : "Unable to load digital twin runtime.");
          }
        }
      })();
    }, pollMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [includeEvents, pollMs]);

  async function runDeveloperAction(action: DeveloperActionName) {
    if (!systemState) {
      return;
    }

    setActiveAction(action);
    setError(null);

    try {
      if (action === "increase-temperature") {
        const nextRiskProbability = Number(Math.min(systemState.fire_twin.fire_risk_probability + 0.12, 1).toFixed(2));
        const fireTwin: Partial<FireTwinState> = {
          temperature: Number((systemState.fire_twin.temperature + 5).toFixed(1)),
          temperature_rate: 0.6,
          fire_risk_probability: nextRiskProbability,
          risk_level: nextRiskProbability >= 0.2 ? "WARNING" : "NORMAL",
        };
        await updateFireTwin(fireTwin);
      }

      if (action === "set-smoke-warning") {
        await updateFireTwin({
          smoke_level: 0.35,
          fire_risk_probability: 0.38,
          risk_level: "WARNING",
          temperature_rate: 1.2,
        });
      }

      if (action === "block-exit-b") {
        const exits = systemState.building_twin.exits.map((exitItem) =>
          exitItem.exit_id === "exit-b"
            ? { ...exitItem, is_available: false, is_blocked: true }
            : exitItem,
        );
        await updateBuildingTwin({ exits } as Partial<BuildingTwinState>);
      }

      if (action === "increase-occupancy") {
        const zones = systemState.occupancy_twin.zones.map((zone, index) =>
          index === 0
            ? {
                ...zone,
                occupancy_count: zone.occupancy_count + 12,
                density: Number((zone.density + 0.07).toFixed(2)),
              }
            : zone,
        );
        await updateOccupancyTwin({
          zones,
          total_occupancy: systemState.occupancy_twin.total_occupancy + 12,
          congestion_level: "MODERATE",
        } as Partial<OccupancyTwinState>);
      }

      if (action === "assign-crew-1") {
        const crews = systemState.response_twin.crews.map((crew) =>
          crew.crew_id === "crew-1"
            ? { ...crew, status: "ASSIGNED", current_zone_id: "zone-1a", eta_minutes: 4 }
            : crew,
        );
        await updateResponseTwin({
          crews,
          average_response_eta: 4,
        } as Partial<ResponseTwinState>);
      }

      if (action === "reset-all") {
        await resetDigitalTwin();
      }

      await refresh(false);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Developer action failed.");
    } finally {
      setActiveAction(null);
    }
  }

  return {
    systemState,
    events,
    loading,
    error,
    activeAction,
    refresh,
    runDeveloperAction,
  };
}