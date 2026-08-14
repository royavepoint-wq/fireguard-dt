"use client";

import { useEffect, useState } from "react";
import { EventTimeline } from "@/components/ui/EventTimeline";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TwinCard } from "@/components/ui/TwinCard";
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
  StatusTone,
} from "@/lib/types";

type TwinKey = "fire" | "building" | "occupancy" | "response";
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

function toneForTwinStatus(status: string): StatusTone {
  if (status === "OFFLINE") {
    return "critical";
  }
  if (status === "DEGRADED") {
    return "warning";
  }
  return "safe";
}

function toneForOrchestratorStatus(status: string): StatusTone {
  if (status === "CRITICAL") {
    return "critical";
  }
  if (status === "WARNING" || status === "DEGRADED") {
    return "warning";
  }
  return "safe";
}

export function TwinEcosystemClient() {
  const [debugMode] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    try {
      const params = new URLSearchParams(window.location.search);
      return params.get("debug") === "true";
    } catch {
      return false;
    }
  });
  const [systemState, setSystemState] = useState<CombinedDigitalTwinState | null>(null);
  const [events, setEvents] = useState<DigitalTwinEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTwin, setSelectedTwin] = useState<TwinKey | null>(null);
  const [activeFilter, setActiveFilter] = useState<EventFilter>("all");
  const [activeAction, setActiveAction] = useState<string | null>(null);

  async function fetchDashboardData() {
    const [nextState, nextEvents] = await Promise.all([getDigitalTwinState(), getEvents()]);
    return {
      nextState,
      nextEvents: nextEvents.slice().reverse(),
    };
  }

  async function loadDashboard(showSpinner = true) {
    if (showSpinner) {
      setLoading(true);
    }
    setError(null);

    try {
      const { nextState, nextEvents } = await fetchDashboardData();
      setSystemState(nextState);
      setEvents(nextEvents);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load digital twin state.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadOnMount() {
      try {
        const { nextState, nextEvents } = await fetchDashboardData();
        if (!active) {
          return;
        }
        setSystemState(nextState);
        setEvents(nextEvents);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load digital twin state.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadOnMount();

    return () => {
      active = false;
    };
  }, []);

  async function runDeveloperAction(action: string) {
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

      await loadDashboard();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Developer action failed.");
    } finally {
      setActiveAction(null);
    }
  }

  const filteredEvents = activeFilter === "all"
    ? events
    : events.filter((event) => event.source_twin === activeFilter);

  const detailTwin = systemState
    ? {
        fire: systemState.fire_twin,
        building: systemState.building_twin,
        occupancy: systemState.occupancy_twin,
        response: systemState.response_twin,
      }[selectedTwin ?? "fire"]
    : null;

  return (
    <div>
      <PageHeader
        title="Twin Ecosystem"
        description="Live backend state across the four domain twins, shared event bus, and AI / Decision Orchestrator."
      />

      {loading ? (
        <Panel title="Loading Twin State" subtitle="Requesting live API data">
          <p className="text-sm text-[var(--fg-muted)]">Loading digital twin state and recent events...</p>
        </Panel>
      ) : null}

      {!loading && error ? (
        <Panel title="API Error" subtitle="The Twin Ecosystem page requires the backend API">
          <div className="space-y-4">
            <p className="text-sm text-[var(--accent-red)]">{error}</p>
            <button type="button" className="action-btn" onClick={() => void loadDashboard()}>
              Retry
            </button>
          </div>
        </Panel>
      ) : null}

      {!loading && !error && systemState ? (
        <>
          <section className="grid gap-4 lg:grid-cols-2">
            <TwinCard
              title="Fire & Environment Twin"
              status={systemState.fire_twin.status}
              tone={toneForTwinStatus(systemState.fire_twin.status)}
              lastUpdated={formatTimestamp(systemState.fire_twin.last_updated)}
              onClick={() => setSelectedTwin("fire")}
              metrics={[
                { label: "Fire Risk", value: systemState.fire_twin.risk_level },
                { label: "Temperature", value: `${systemState.fire_twin.temperature.toFixed(1)}°C` },
                { label: "Smoke", value: systemState.fire_twin.smoke_level.toFixed(2) },
                { label: "CO", value: systemState.fire_twin.co_level.toFixed(1) },
              ]}
            />

            <TwinCard
              title="Building Infrastructure Twin"
              status={systemState.building_twin.status}
              tone={toneForTwinStatus(systemState.building_twin.status)}
              lastUpdated={formatTimestamp(systemState.building_twin.last_updated)}
              onClick={() => setSelectedTwin("building")}
              metrics={[
                { label: "Floors", value: systemState.building_twin.floors.length },
                { label: "Rooms", value: systemState.building_twin.rooms.length },
                { label: "Available Exits", value: systemState.building_twin.exits.filter((exitItem) => exitItem.is_available).length },
                { label: "HVAC Zones", value: systemState.building_twin.hvac_zones.length },
              ]}
            />

            <TwinCard
              title="Occupancy & Evacuation Twin"
              status={systemState.occupancy_twin.status}
              tone={toneForTwinStatus(systemState.occupancy_twin.status)}
              lastUpdated={formatTimestamp(systemState.occupancy_twin.last_updated)}
              onClick={() => setSelectedTwin("occupancy")}
              metrics={[
                { label: "Occupancy", value: systemState.occupancy_twin.total_occupancy },
                { label: "Zones", value: systemState.occupancy_twin.zones.length },
                { label: "Evacuating", value: systemState.occupancy_twin.evacuating_count },
                { label: "Congestion", value: systemState.occupancy_twin.congestion_level },
              ]}
            />

            <TwinCard
              title="Emergency Response Twin"
              status={systemState.response_twin.status}
              tone={toneForTwinStatus(systemState.response_twin.status)}
              lastUpdated={formatTimestamp(systemState.response_twin.last_updated)}
              onClick={() => setSelectedTwin("response")}
              metrics={[
                { label: "Crews", value: systemState.response_twin.crews.length },
                { label: "Drones", value: systemState.response_twin.drones.length },
                { label: "Dispatch Queue", value: systemState.response_twin.dispatch_queue.length },
                { label: "Incidents", value: systemState.response_twin.active_incidents.length },
              ]}
            />
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
            <Panel title="AI / Decision Orchestrator" subtitle="Cross-twin coordination and governance-aware monitoring">
              <div className="mb-4 flex items-center gap-3">
                <StatusBadge label={systemState.orchestrator.status} tone={toneForOrchestratorStatus(systemState.orchestrator.status)} />
                <span className="text-sm text-[var(--fg-muted)]">Human Oversight {systemState.orchestrator.human_oversight ? "Enabled" : "Disabled"}</span>
              </div>
              <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <div className="kv-item"><dt>Twins Online</dt><dd>{systemState.orchestrator.twins_online}</dd></div>
                <div className="kv-item"><dt>Fire Risk Probability</dt><dd>{Number(systemState.orchestrator.cross_twin_state.fire_risk_probability ?? 0).toFixed(2)}</dd></div>
                <div className="kv-item"><dt>Total Occupancy</dt><dd>{String(systemState.orchestrator.cross_twin_state.total_occupancy ?? 0)}</dd></div>
                <div className="kv-item"><dt>Blocked Exits</dt><dd>{Array.isArray(systemState.orchestrator.cross_twin_state.blocked_exits) ? (systemState.orchestrator.cross_twin_state.blocked_exits as string[]).length : 0}</dd></div>
                <div className="kv-item"><dt>Dispatch Queue</dt><dd>{String(systemState.orchestrator.cross_twin_state.dispatch_queue_size ?? 0)}</dd></div>
                <div className="kv-item"><dt>Last Updated</dt><dd>{formatTimestamp(systemState.orchestrator.last_updated)}</dd></div>
              </dl>
              <div className="mt-4">
                <h4 className="text-xs uppercase tracking-[0.22em] text-[var(--fg-muted)]">Active Alerts</h4>
                {systemState.orchestrator.active_alerts.length > 0 ? (
                  <ul className="mt-3 space-y-2 text-sm text-white">
                    {systemState.orchestrator.active_alerts.map((alert) => (
                      <li key={alert} className="rounded-xl border border-amber-400/25 bg-amber-400/8 px-3 py-2">{alert}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-[var(--fg-muted)]">No active orchestrator alerts.</p>
                )}
              </div>
            </Panel>

            {debugMode ? (
              <Panel title="Debug Controls" subtitle="Manual API actions for development diagnostics">
                <div className="grid gap-3">
                  <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => void runDeveloperAction("increase-temperature")}>Increase Fire Twin Temperature</button>
                  <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => void runDeveloperAction("set-smoke-warning")}>Set Smoke Warning</button>
                  <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => void runDeveloperAction("block-exit-b")}>Block Exit B</button>
                  <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => void runDeveloperAction("increase-occupancy")}>Increase Occupancy</button>
                  <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => void runDeveloperAction("assign-crew-1")}>Mark Crew 1 Assigned</button>
                  <button type="button" className="action-btn" disabled={activeAction !== null} onClick={() => void runDeveloperAction("reset-all")}>Reset All Twins</button>
                </div>
                {activeAction ? <p className="mt-3 text-sm text-[var(--fg-muted)]">Applying debug action...</p> : null}
              </Panel>
            ) : null}
          </section>

          <section className="mt-4">
            <Panel title="Live Event Timeline" subtitle="Recent in-memory event bus activity">
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
              {filteredEvents.length > 0 ? (
                <EventTimeline
                  events={filteredEvents.map((event) => ({
                    ...event,
                    timestamp: formatTimestamp(event.timestamp),
                  }))}
                />
              ) : (
                <EmptyState
                  title="No events yet"
                  description="Start a simulation run to observe shared event publication in real time."
                  bullets={["TWIN_STATE_UPDATED", "SYSTEM_INITIALIZED", "In-memory event bus"]}
                />
              )}
            </Panel>
          </section>
        </>
      ) : null}

      {selectedTwin && detailTwin && systemState ? (
        <div className="detail-backdrop" onClick={() => setSelectedTwin(null)}>
          <aside className="detail-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-white">{detailTwin.name}</h2>
                <p className="mt-1 text-sm text-[var(--fg-muted)]">Last Updated {formatTimestamp(detailTwin.last_updated)}</p>
              </div>
              <button type="button" className="filter-btn" onClick={() => setSelectedTwin(null)}>Close</button>
            </div>

            {selectedTwin === "fire" ? (
              <dl className="detail-grid">
                <div className="kv-item"><dt>Temperature</dt><dd>{systemState.fire_twin.temperature.toFixed(1)}°C</dd></div>
                <div className="kv-item"><dt>Temperature Rate</dt><dd>{systemState.fire_twin.temperature_rate.toFixed(1)}°C/min</dd></div>
                <div className="kv-item"><dt>Smoke</dt><dd>{systemState.fire_twin.smoke_level.toFixed(2)}</dd></div>
                <div className="kv-item"><dt>CO</dt><dd>{systemState.fire_twin.co_level.toFixed(1)}</dd></div>
                <div className="kv-item"><dt>CO2</dt><dd>{systemState.fire_twin.co2_level.toFixed(0)}</dd></div>
                <div className="kv-item"><dt>Humidity</dt><dd>{systemState.fire_twin.humidity.toFixed(0)}%</dd></div>
                <div className="kv-item"><dt>Electrical Load</dt><dd>{systemState.fire_twin.electrical_load.toFixed(0)}%</dd></div>
                <div className="kv-item"><dt>Risk Probability</dt><dd>{systemState.fire_twin.fire_risk_probability.toFixed(2)}</dd></div>
                <div className="kv-item"><dt>Risk Level</dt><dd>{systemState.fire_twin.risk_level}</dd></div>
                <div className="kv-item"><dt>Sensor Health</dt><dd>{systemState.fire_twin.sensor_health}</dd></div>
              </dl>
            ) : null}

            {selectedTwin === "building" ? (
              <div className="space-y-4">
                <dl className="detail-grid">
                  <div className="kv-item"><dt>Floors</dt><dd>{systemState.building_twin.floors.length}</dd></div>
                  <div className="kv-item"><dt>Rooms</dt><dd>{systemState.building_twin.rooms.length}</dd></div>
                  <div className="kv-item"><dt>Corridors</dt><dd>{systemState.building_twin.corridors.length}</dd></div>
                  <div className="kv-item"><dt>Exits</dt><dd>{systemState.building_twin.exits.length}</dd></div>
                  <div className="kv-item"><dt>HVAC Zones</dt><dd>{systemState.building_twin.hvac_zones.length}</dd></div>
                  <div className="kv-item"><dt>Sprinklers</dt><dd>{systemState.building_twin.sprinklers.length}</dd></div>
                </dl>
                <div>
                  <h4 className="mb-2 text-xs uppercase tracking-[0.22em] text-[var(--fg-muted)]">Exit States</h4>
                  <ul className="space-y-2">
                    {systemState.building_twin.exits.map((exitItem) => (
                      <li key={exitItem.exit_id} className="system-row">
                        <span>{exitItem.name}</span>
                        <StatusBadge label={exitItem.is_blocked ? "BLOCKED" : "AVAILABLE"} tone={exitItem.is_blocked ? "critical" : "safe"} />
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}

            {selectedTwin === "occupancy" ? (
              <div className="space-y-4">
                <dl className="detail-grid">
                  <div className="kv-item"><dt>Total Occupancy</dt><dd>{systemState.occupancy_twin.total_occupancy}</dd></div>
                  <div className="kv-item"><dt>Evacuating</dt><dd>{systemState.occupancy_twin.evacuating_count}</dd></div>
                  <div className="kv-item"><dt>Evacuated</dt><dd>{systemState.occupancy_twin.evacuated_count}</dd></div>
                  <div className="kv-item"><dt>Congestion</dt><dd>{systemState.occupancy_twin.congestion_level}</dd></div>
                </dl>
                <div>
                  <h4 className="mb-2 text-xs uppercase tracking-[0.22em] text-[var(--fg-muted)]">Zone Distribution</h4>
                  <ul className="space-y-2">
                    {systemState.occupancy_twin.zones.map((zone) => (
                      <li key={zone.zone_id} className="rounded-2xl border border-white/8 bg-white/4 px-3 py-2 text-sm text-white">
                        <div className="flex items-center justify-between gap-3">
                          <span>{zone.zone_id}</span>
                          <span>{zone.occupancy_count} occupants</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}

            {selectedTwin === "response" ? (
              <div className="space-y-4">
                <dl className="detail-grid">
                  <div className="kv-item"><dt>Crews</dt><dd>{systemState.response_twin.crews.length}</dd></div>
                  <div className="kv-item"><dt>Drones</dt><dd>{systemState.response_twin.drones.length}</dd></div>
                  <div className="kv-item"><dt>Dispatch Queue</dt><dd>{systemState.response_twin.dispatch_queue.length}</dd></div>
                  <div className="kv-item"><dt>Active Incidents</dt><dd>{systemState.response_twin.active_incidents.length}</dd></div>
                </dl>
                <div>
                  <h4 className="mb-2 text-xs uppercase tracking-[0.22em] text-[var(--fg-muted)]">Crew Availability</h4>
                  <ul className="space-y-2">
                    {systemState.response_twin.crews.map((crew) => (
                      <li key={crew.crew_id} className="system-row">
                        <span>{crew.name}</span>
                        <StatusBadge label={crew.status} tone={crew.status === "AVAILABLE" ? "safe" : "warning"} />
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </aside>
        </div>
      ) : null}
    </div>
  );
}