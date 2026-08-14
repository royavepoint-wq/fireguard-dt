"use client";

import { useEffect, useMemo, useState } from "react";

import { getDigitalTwinState, getEvents, getFireRiskExplanation, getSimulationRuns, getSimulationStatus } from "@/lib/api";
import type {
  CombinedDigitalTwinState,
  DigitalTwinEvent,
  FireRiskExplanationResponse,
  SimulationRunSummary,
  SimulationState,
} from "@/lib/types";

type UseIntegratedRuntimeOptions = {
  pollMs?: number;
  eventLimit?: number;
  includeSimulation?: boolean;
  includeRuns?: boolean;
  includeExplanation?: boolean;
};

type IntegratedRuntimeState = {
  systemState: CombinedDigitalTwinState | null;
  simulation: SimulationState | null;
  runs: SimulationRunSummary[];
  explanation: FireRiskExplanationResponse | null;
  events: DigitalTwinEvent[];
  loading: boolean;
  error: string | null;
  refresh: (showSpinner?: boolean) => Promise<void>;
};

const MEANINGFUL_EVENT_TYPES = new Set([
  "ANOMALY_DETECTED",
  "RISK_LEVEL_CHANGED",
  "SIMULATION_PHASE_CHANGED",
  "DISPATCH_CREATED",
  "INFRASTRUCTURE_STATUS_CHANGED",
  "OCCUPANCY_UPDATED",
  "SIMULATION_COMPLETED",
  "SIMULATION_STARTED",
  "SIMULATION_PAUSED",
  "SIMULATION_RESUMED",
  "SIMULATION_STOPPED",
  "SYSTEM_INITIALIZED",
  "APPROVAL_REQUESTED",
  "APPROVAL_DECIDED",
  "ROUTE_RECALCULATED",
]);

export function useIntegratedRuntime(options: UseIntegratedRuntimeOptions = {}): IntegratedRuntimeState {
  const pollMs = options.pollMs ?? 1000;
  const eventLimit = options.eventLimit ?? 150;
  const includeSimulation = options.includeSimulation ?? false;
  const includeRuns = options.includeRuns ?? false;
  const includeExplanation = options.includeExplanation ?? true;

  const [systemState, setSystemState] = useState<CombinedDigitalTwinState | null>(null);
  const [simulation, setSimulation] = useState<SimulationState | null>(null);
  const [runs, setRuns] = useState<SimulationRunSummary[]>([]);
  const [explanation, setExplanation] = useState<FireRiskExplanationResponse | null>(null);
  const [events, setEvents] = useState<DigitalTwinEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async (showSpinner = false) => {
    if (showSpinner) {
      setLoading(true);
    }
    try {
      const [nextState, nextSimulation, nextRuns, nextEvents, nextExplanation] = await Promise.all([
        getDigitalTwinState(),
        includeSimulation ? getSimulationStatus() : Promise.resolve(null),
        includeRuns ? getSimulationRuns() : Promise.resolve([] as SimulationRunSummary[]),
        getEvents(),
        includeExplanation ? getFireRiskExplanation() : Promise.resolve(null),
      ]);
      setSystemState(nextState);
      setSimulation(nextSimulation);
      setRuns(nextRuns.slice().reverse());
      setExplanation(nextExplanation);
      const filtered = nextEvents
        .filter((item) => MEANINGFUL_EVENT_TYPES.has(item.event_type))
        .slice(-eventLimit)
        .reverse();
      setEvents(filtered);
      setError(null);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Backend connection unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [nextState, nextSimulation, nextRuns, nextEvents, nextExplanation] = await Promise.all([
          getDigitalTwinState(),
          includeSimulation ? getSimulationStatus() : Promise.resolve(null),
          includeRuns ? getSimulationRuns() : Promise.resolve([] as SimulationRunSummary[]),
          getEvents(),
          includeExplanation ? getFireRiskExplanation() : Promise.resolve(null),
        ]);
        if (!active) {
          return;
        }
        setSystemState(nextState);
        setSimulation(nextSimulation);
        setRuns(nextRuns.slice().reverse());
        setExplanation(nextExplanation);
        const filtered = nextEvents
          .filter((item) => MEANINGFUL_EVENT_TYPES.has(item.event_type))
          .slice(-eventLimit)
          .reverse();
        setEvents(filtered);
        setError(null);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Backend connection unavailable.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();

    const timer = window.setInterval(() => {
      void load();
    }, pollMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [eventLimit, includeExplanation, includeRuns, includeSimulation, pollMs]);

  const stableEvents = useMemo(() => events, [events]);

  return {
    systemState,
    simulation,
    runs,
    explanation,
    events: stableEvents,
    loading,
    error,
    refresh,
  };
}
