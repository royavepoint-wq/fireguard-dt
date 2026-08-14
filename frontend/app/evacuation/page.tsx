"use client";

import { useEffect, useMemo, useState } from "react";

import { MetricCard } from "@/components/ui/MetricCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { compareEvacuationRoutes, getDigitalTwinState, getEvacuationRoute } from "@/lib/api";
import type { EvacuationComparisonResponse, EvacuationRouteResponse, EvacuationRouteStrategy, StatusTone } from "@/lib/types";

const STRATEGIES: EvacuationRouteStrategy[] = ["STATIC_PLAN", "SHORTEST_PATH", "TWIN_OPTIMIZED"];

function toneFromRouteStatus(status: string | undefined): StatusTone {
  if (status === "OPEN") {
    return "safe";
  }
  if (status === "CONGESTED") {
    return "warning";
  }
  return "critical";
}

function numberOrNA(value: number | undefined, digits = 2): string {
  if (typeof value !== "number") {
    return "N/A";
  }
  return value.toFixed(digits);
}

function zoneLabel(zoneId: string): string {
  return zoneId.replaceAll("-", " ");
}

export default function EvacuationPage() {
  const [selectedStrategy, setSelectedStrategy] = useState<EvacuationRouteStrategy>("TWIN_OPTIMIZED");
  const [startZoneId, setStartZoneId] = useState<string>("zone-1a");
  const [route, setRoute] = useState<EvacuationRouteResponse | null>(null);
  const [comparison, setComparison] = useState<EvacuationComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (strategy: EvacuationRouteStrategy, zoneId: string) => {
    setRunning(true);
    try {
      const [nextRoute, nextCompare] = await Promise.all([
        getEvacuationRoute({ start_zone_id: zoneId, strategy }),
        compareEvacuationRoutes({ start_zone_id: zoneId, strategy }),
      ]);
      setRoute(nextRoute);
      setComparison(nextCompare);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to compute evacuation routes.");
    } finally {
      setRunning(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const bootstrap = async () => {
      try {
        const state = await getDigitalTwinState();
        if (!active) {
          return;
        }
        const zoneCandidate = state.fire_twin.zone_id || state.occupancy_twin.zones[0]?.zone_id || "zone-1a";
        setStartZoneId(zoneCandidate);
      } catch {
        if (active) {
          setStartZoneId("zone-1a");
        }
      }
    };

    void bootstrap();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void load(selectedStrategy, startZoneId);
    }, 3000);

    return () => {
      window.clearInterval(interval);
    };
  }, [selectedStrategy, startZoneId]);

  const fastest = useMemo(() => {
    if (!comparison) {
      return null;
    }
    const candidates = comparison.results.filter((item) => item.status !== "NO_SAFE_ROUTE");
    if (candidates.length === 0) {
      return null;
    }
    return candidates.reduce((current, next) => (next.estimated_time_seconds < current.estimated_time_seconds ? next : current));
  }, [comparison]);

  const safest = useMemo(() => {
    if (!comparison) {
      return null;
    }
    const candidates = comparison.results.filter((item) => item.status !== "NO_SAFE_ROUTE");
    if (candidates.length === 0) {
      return null;
    }
    return candidates.reduce((current, next) => {
      const currentUnsafe = current.unsafe_segments;
      const nextUnsafe = next.unsafe_segments;
      if (nextUnsafe !== currentUnsafe) {
        return nextUnsafe < currentUnsafe ? next : current;
      }
      if (next.hazard_exposure_score !== current.hazard_exposure_score) {
        return next.hazard_exposure_score < current.hazard_exposure_score ? next : current;
      }
      if (next.peak_route_congestion !== current.peak_route_congestion) {
        return next.peak_route_congestion < current.peak_route_congestion ? next : current;
      }
      return next.estimated_time_seconds < current.estimated_time_seconds ? next : current;
    });
  }, [comparison]);

  const recommended = safest;

  return (
    <div>
      <PageHeader
        title="Evacuation Optimizer"
        description="Dynamic risk-aware evacuation optimization across static, shortest-path, and twin-optimized strategies."
        actions={
          <div className="flex items-center gap-2">
            <select
              className="filter-btn"
              value={selectedStrategy}
              onChange={(event) => {
                const strategy = event.target.value as EvacuationRouteStrategy;
                setSelectedStrategy(strategy);
                void load(strategy, startZoneId);
              }}
              disabled={running}
            >
              {STRATEGIES.map((strategy) => (
                <option key={strategy} value={strategy}>{strategy.replaceAll("_", " ")}</option>
              ))}
            </select>
            <button type="button" className="action-btn" disabled={running} onClick={() => void load(selectedStrategy, startZoneId)}>
              {running ? "Calculating..." : "Recalculate"}
            </button>
          </div>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Selected Strategy"
          value={route?.strategy?.replaceAll("_", " ") ?? selectedStrategy.replaceAll("_", " ")}
          helper={`Start zone: ${zoneLabel(startZoneId)}`}
          statusLabel={route?.status ?? "N/A"}
          statusTone={toneFromRouteStatus(route?.status)}
        />
        <MetricCard
          label="Estimated Evacuation Time"
          value={route ? `${numberOrNA(route.estimated_time_seconds, 1)} s` : "N/A"}
          helper="distance / max(0.35, 1.2 / congestion_factor)"
        />
        <MetricCard
          label="Fastest Route"
          value={fastest?.strategy?.replaceAll("_", " ") ?? "N/A"}
          helper={fastest ? `${numberOrNA(fastest.estimated_time_seconds, 1)} s` : "No safe path"}
          statusLabel={fastest?.status ?? "NO_SAFE_ROUTE"}
          statusTone={toneFromRouteStatus(fastest?.status)}
        />
        <MetricCard
          label="Safest / Recommended"
          value={recommended?.strategy?.replaceAll("_", " ") ?? "N/A"}
          helper={safest ? `Exposure ${numberOrNA(safest.hazard_exposure_score, 2)} | Unsafe segments ${safest.unsafe_segments}` : "No safe path"}
          statusLabel={recommended?.status ?? "NO_SAFE_ROUTE"}
          statusTone={toneFromRouteStatus(recommended?.status)}
        />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel
          title="Selected Route Details"
          subtitle="Live optimizer output for the selected strategy"
          action={<StatusBadge label={route?.status ?? "N/A"} tone={toneFromRouteStatus(route?.status)} />}
        >
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Algorithm</span><span>{route?.algorithm ?? "N/A"}</span></div>
            <div className="system-row"><span>Selected Exit</span><span>{route?.selected_exit ?? "None"}</span></div>
            <div className="system-row"><span>Distance (m)</span><span>{numberOrNA(route?.distance_meters, 3)}</span></div>
            <div className="system-row"><span>Total Cost</span><span>{numberOrNA(route?.total_cost, 3)}</span></div>
            <div className="system-row"><span>Hazard Exposure</span><span>{numberOrNA(route?.hazard_exposure_score, 3)}</span></div>
            <div className="system-row"><span>Peak Congestion Cost</span><span>{numberOrNA(route?.peak_route_congestion, 3)}</span></div>
            <div className="system-row"><span>Unsafe Segments</span><span>{route?.unsafe_segments ?? "N/A"}</span></div>
            <div className="system-row"><span>Recalculation Trigger</span><span>{route?.recalculation_trigger ?? "state change"}</span></div>
          </div>
          <div className="mt-3 text-sm text-[var(--fg-muted)]">
            Path: {route?.path_nodes.length ? route.path_nodes.join(" -> ") : "No safe path"}
          </div>
        </Panel>

        <Panel title="Cost Decomposition" subtitle="How the twin optimizer balances safety and travel efficiency">
          <div className="space-y-2 text-sm">
            <div className="system-row"><span>Distance Component</span><span>{numberOrNA(route?.distance_meters, 3)}</span></div>
            <div className="system-row"><span>Fire Risk Cost</span><span>{numberOrNA(route?.fire_risk_cost, 3)}</span></div>
            <div className="system-row"><span>Smoke Risk Cost</span><span>{numberOrNA(route?.smoke_risk_cost, 3)}</span></div>
            <div className="system-row"><span>Congestion Cost</span><span>{numberOrNA(route?.congestion_cost, 3)}</span></div>
          </div>
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Strategy Comparison" subtitle="Static baseline versus shortest-path versus hazard-aware optimization">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-[var(--fg-muted)]">
                  <th className="px-2 py-2">Strategy</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Exit</th>
                  <th className="px-2 py-2">Distance</th>
                  <th className="px-2 py-2">Time (s)</th>
                  <th className="px-2 py-2">Total Cost</th>
                  <th className="px-2 py-2">Exposure</th>
                </tr>
              </thead>
              <tbody>
                {(comparison?.results ?? []).map((item) => (
                  <tr key={item.strategy} className="border-t border-white/8">
                    <td className="px-2 py-2">{item.strategy.replaceAll("_", " ")}</td>
                    <td className="px-2 py-2">{item.status}</td>
                    <td className="px-2 py-2">{item.selected_exit ?? "None"}</td>
                    <td className="px-2 py-2">{numberOrNA(item.distance_meters, 2)}</td>
                    <td className="px-2 py-2">{numberOrNA(item.estimated_time_seconds, 1)}</td>
                    <td className="px-2 py-2">{numberOrNA(item.total_cost, 3)}</td>
                    <td className="px-2 py-2">{numberOrNA(item.hazard_exposure_score, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {loading ? <p className="mt-3 text-sm text-[var(--fg-muted)]">Loading optimization output...</p> : null}
          {error ? <p className="mt-3 text-sm text-[var(--accent-red)]">{error}</p> : null}
        </Panel>
      </section>
    </div>
  );
}
