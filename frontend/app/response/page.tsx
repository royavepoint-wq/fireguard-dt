"use client";

import { useEffect, useMemo, useState } from "react";

import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { getDigitalTwinState, getEvents, getSimulationStatus } from "@/lib/api";
import type { CombinedDigitalTwinState, DigitalTwinEvent, SimulationState } from "@/lib/types";

function formatEta(minutes: number | null): string {
  if (minutes === null || minutes <= 0) {
    return "00:00";
  }
  const totalSeconds = Math.round(minutes * 60);
  const mm = Math.floor(totalSeconds / 60);
  const ss = totalSeconds % 60;
  return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

function incidentAge(simulation: SimulationState | null, incidentDetectedEvent: DigitalTwinEvent | undefined): string {
  if (!simulation || !incidentDetectedEvent) {
    return "N/A";
  }
  const incidentTime = Number(incidentDetectedEvent.payload?.elapsed_seconds ?? 0);
  const age = Math.max(0, simulation.elapsed_seconds - incidentTime);
  return `${Math.floor(age / 60)}m ${age % 60}s`;
}

export default function ResponsePage() {
  const [state, setState] = useState<CombinedDigitalTwinState | null>(null);
  const [events, setEvents] = useState<DigitalTwinEvent[]>([]);
  const [simulation, setSimulation] = useState<SimulationState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const [nextState, nextEvents, nextSimulation] = await Promise.all([
          getDigitalTwinState(),
          getEvents(),
          getSimulationStatus(),
        ]);
        if (!active) {
          return;
        }
        setState(nextState);
        setEvents(nextEvents);
        setSimulation(nextSimulation);
        setError(null);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load response state.");
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

  const responseTwin = state?.response_twin ?? null;
  const activeIncident = responseTwin?.active_incidents.find((item) => item.status === "ACTIVE") ?? null;
  const dispatchEvents = useMemo(
    () => events.filter((event) => event.event_type === "DISPATCH_CREATED" || event.event_type === "RISK_LEVEL_CHANGED" || event.event_type === "INFRASTRUCTURE_STATUS_CHANGED" || event.event_type === "OCCUPANCY_UPDATED"),
    [events],
  );

  const firstDispatchEta = useMemo(() => {
    if (!responseTwin) {
      return null;
    }
    const crewEtas = responseTwin.crews.filter((crew) => crew.status !== "AVAILABLE").map((crew) => crew.eta_minutes);
    const droneEtas = responseTwin.drones.filter((drone) => drone.status !== "AVAILABLE").map((drone) => drone.eta_minutes);
    const values = [...crewEtas, ...droneEtas].filter((value) => value > 0);
    if (values.length === 0) {
      return null;
    }
    return Math.min(...values);
  }, [responseTwin]);

  const incidentDetectedEvent = events.find((event) => event.event_type === "RISK_LEVEL_CHANGED" && String(event.payload?.phase ?? "") === "CRITICAL");

  const latestRun = simulation?.latest_run_summary;

  return (
    <div>
      <PageHeader
        title="Emergency Response"
        description="Emergency response analytics with live ETA, dispatch timeline, and completed incident performance metrics."
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Available Crews" value={responseTwin ? responseTwin.crews.filter((crew) => crew.status === "AVAILABLE").length : "N/A"} helper="Current standby" statusLabel="LIVE" statusTone="info" />
        <MetricCard label="Available Drones" value={responseTwin ? responseTwin.drones.filter((drone) => drone.status === "AVAILABLE").length : "N/A"} helper="Current standby" statusLabel="LIVE" statusTone="info" />
        <MetricCard label="Active Dispatches" value={responseTwin?.dispatch_queue.length ?? "N/A"} helper="Assigned or en route resources" statusLabel={responseTwin?.dispatch_queue.length ? "ACTIVE" : "CLEAR"} statusTone={responseTwin?.dispatch_queue.length ? "warning" : "safe"} />
        <MetricCard label="First Response ETA" value={activeIncident ? (firstDispatchEta === null ? "N/A" : formatEta(firstDispatchEta)) : "N/A"} helper={activeIncident ? "Live deterministic ETA" : "No Active Incident"} statusLabel={activeIncident ? "ACTIVE" : "N/A"} statusTone={activeIncident ? "warning" : "muted"} />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Active Incident" subtitle="Current incident state">
          {activeIncident ? (
            <div className="space-y-2 text-sm">
              <div className="system-row"><span>Incident ID</span><span>{activeIncident.incident_id}</span></div>
              <div className="system-row"><span>Location</span><span>{activeIncident.zone_id ?? "N/A"}</span></div>
              <div className="system-row"><span>Severity</span><span>{activeIncident.severity}</span></div>
              <div className="system-row"><span>Current Phase</span><span>{simulation?.phase ?? "N/A"}</span></div>
              <div className="system-row"><span>Incident Age</span><span>{incidentAge(simulation, incidentDetectedEvent)}</span></div>
            </div>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="system-row"><span>Status</span><span>No Active Incident</span></div>
              <div className="system-row"><span>Readiness</span><span>All emergency resources are ready.</span></div>
              <div className="system-row"><span>Response ETA</span><span>N/A</span></div>
            </div>
          )}
        </Panel>

        <Panel title="Completed Incident Metrics" subtitle="Latest completed simulation run">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Time to First Dispatch</span><span>{latestRun?.time_to_first_dispatch ?? "N/A"}</span></div>
            <div className="system-row"><span>Time to First Response</span><span>{latestRun?.time_to_first_response ?? "N/A"}</span></div>
            <div className="system-row"><span>Time to Containment</span><span>{latestRun?.time_to_containment ?? "N/A"}</span></div>
            <div className="system-row"><span>Time to Resolution</span><span>{latestRun?.time_to_resolution ?? "N/A"}</span></div>
            <div className="system-row"><span>Resources Used</span><span>{latestRun?.resources_dispatched ?? "N/A"}</span></div>
            <div className="system-row"><span>Outcome Quality</span><span>{latestRun?.outcome_quality ?? "N/A"}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Crew Status" subtitle="Live crew assignment and ETA">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead><tr className="text-[var(--fg-muted)]"><th className="px-2 py-2">Crew</th><th className="px-2 py-2">Status</th><th className="px-2 py-2">Assignment</th><th className="px-2 py-2">ETA</th><th className="px-2 py-2">Location</th></tr></thead>
              <tbody>
                {(responseTwin?.crews ?? []).map((crew) => (
                  <tr key={crew.crew_id} className="border-t border-white/8">
                    <td className="px-2 py-2">{crew.name}</td>
                    <td className="px-2 py-2">{crew.status}</td>
                    <td className="px-2 py-2">{activeIncident?.description ?? "N/A"}</td>
                    <td className="px-2 py-2">{crew.status === "AVAILABLE" ? "N/A" : formatEta(crew.eta_minutes)}</td>
                    <td className="px-2 py-2">{crew.current_zone_id ?? "Staging Area"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Drone Status" subtitle="Live drone assignment and ETA">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead><tr className="text-[var(--fg-muted)]"><th className="px-2 py-2">Drone</th><th className="px-2 py-2">Status</th><th className="px-2 py-2">Assignment</th><th className="px-2 py-2">ETA</th><th className="px-2 py-2">Location</th></tr></thead>
              <tbody>
                {(responseTwin?.drones ?? []).map((drone) => (
                  <tr key={drone.drone_id} className="border-t border-white/8">
                    <td className="px-2 py-2">{drone.name}</td>
                    <td className="px-2 py-2">{drone.status}</td>
                    <td className="px-2 py-2">{activeIncident?.description ?? "N/A"}</td>
                    <td className="px-2 py-2">{drone.status === "AVAILABLE" ? "N/A" : formatEta(drone.eta_minutes)}</td>
                    <td className="px-2 py-2">{drone.current_zone_id ?? "Drone Bay"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Dispatch Timeline" subtitle="Event-driven response sequence">
          <ul className="space-y-2 text-sm">
            {dispatchEvents.slice(-12).reverse().map((event) => (
              <li key={event.event_id} className="rounded-xl border border-white/8 bg-white/4 p-3">
                <div className="flex items-center justify-between"><span>{event.message}</span><span className="text-[var(--fg-muted)]">{event.payload?.simulation_time ? String(event.payload.simulation_time) : "N/A"}</span></div>
                <p className="mt-1 text-xs text-[var(--fg-muted)]">{event.event_type}</p>
              </li>
            ))}
          </ul>
          {error ? <p className="mt-3 text-sm text-[var(--accent-red)]">{error}</p> : null}
        </Panel>
      </section>
    </div>
  );
}
