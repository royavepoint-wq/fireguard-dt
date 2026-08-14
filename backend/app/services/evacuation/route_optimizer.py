from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import networkx as nx

from app.models.common import RiskLevel
from app.models.evacuation import EvacuationComparisonResponse, EvacuationRouteResponse
from app.models.fire_environment import FireEnvironmentTwinState
from app.models.occupancy import OccupancyEvacuationTwinState, RouteCoordinate, RouteStatus, RouteStrategy
from app.models.building import BuildingInfrastructureTwinState
from app.services.evacuation.baseline_routes import static_plan_route
from app.services.evacuation.cost_model import RouteCostWeights
from app.services.evacuation.graph_builder import NODES, build_base_graph, resolve_start_node
from app.services.evacuation.metrics import estimate_time_seconds


@dataclass(frozen=True)
class _PathMetrics:
    distance_meters: float
    total_cost: float
    fire_risk_cost: float
    smoke_risk_cost: float
    congestion_cost: float
    hazard_exposure_score: float
    peak_route_congestion: float
    unsafe_segments: int


class EvacuationRouteOptimizer:
    def __init__(self, *, weights: RouteCostWeights | None = None, algorithm: str = "dijkstra") -> None:
        self._weights = weights or RouteCostWeights()
        self._algorithm = algorithm

    def _node_fire_risk(self, node_id: str, fire_state: FireEnvironmentTwinState) -> float:
        if node_id in {fire_state.zone_id, "room-electrical-01"}:
            return float(fire_state.fire_risk_probability)
        if node_id == "corridor-c":
            return float(max(fire_state.fire_risk_probability * 0.85, fire_state.smoke_level * 0.7))
        return float(min(1.0, fire_state.fire_risk_probability * 0.3))

    def _node_smoke_risk(self, node_id: str, fire_state: FireEnvironmentTwinState) -> float:
        if node_id == "corridor-c":
            return float(min(1.0, fire_state.smoke_level * 1.3))
        if node_id == "room-electrical-01":
            return float(min(1.0, fire_state.smoke_level * 1.1))
        return float(min(1.0, fire_state.smoke_level * 0.35))

    def _zone_congestion_factor(self, occupancy_state: OccupancyEvacuationTwinState, start_zone_id: str) -> float:
        zone = next((item for item in occupancy_state.zones if item.zone_id == start_zone_id), None)
        density = zone.density if zone is not None else 0.35
        vulnerable_count = zone.vulnerable_count if zone is not None else 0
        vulnerability_boost = 1.25 if vulnerable_count > 0 else 1.0
        congestion_band = {
            "LOW": 1.0,
            "MODERATE": 1.25,
            "HIGH": 1.55,
        }.get(occupancy_state.congestion_level.value, 1.0)
        return float(max(1.0, (1.0 + density) * congestion_band * vulnerability_boost))

    def _build_dynamic_graph(
        self,
        *,
        fire_state: FireEnvironmentTwinState,
        building_state: BuildingInfrastructureTwinState,
        occupancy_state: OccupancyEvacuationTwinState,
        start_zone_id: str,
        strategy: RouteStrategy,
    ) -> nx.Graph:
        graph = build_base_graph()

        blocked_edges = set()
        corridor_c = next((corridor for corridor in building_state.corridors if corridor.corridor_id == "corridor-c"), None)
        if corridor_c is not None and (not corridor_c.is_accessible or corridor_c.status in {"UNSAFE", "CRITICAL_UNSAFE", "BLOCKED"}):
            blocked_edges.add("corridor-c")

        blocked_exits = {exit_item.exit_id for exit_item in building_state.exits if (exit_item.is_blocked or not exit_item.is_available)}
        for exit_id in blocked_exits:
            if graph.has_node(exit_id):
                graph.remove_node(exit_id)

        congestion_factor = self._zone_congestion_factor(occupancy_state, start_zone_id)

        for src, dst, data in list(graph.edges(data=True)):
            edge_id = str(data.get("edge_id", ""))
            if edge_id in blocked_edges:
                graph.remove_edge(src, dst)
                continue

            distance = float(data.get("distance", 1.0))
            fire_risk = max(self._node_fire_risk(src, fire_state), self._node_fire_risk(dst, fire_state))
            smoke_risk = max(self._node_smoke_risk(src, fire_state), self._node_smoke_risk(dst, fire_state))
            crowd_risk = max(0.0, congestion_factor - 1.0)

            if strategy == RouteStrategy.SHORTEST_PATH:
                total_cost = distance
            elif strategy == RouteStrategy.STATIC_PLAN:
                total_cost = distance
            else:
                total_cost = (
                    self._weights.distance * distance
                    + self._weights.fire * fire_risk
                    + self._weights.smoke * smoke_risk
                    + self._weights.crowd * crowd_risk
                )

            data["distance_cost"] = distance
            data["fire_risk_cost"] = self._weights.fire * fire_risk if strategy == RouteStrategy.TWIN_OPTIMIZED else 0.0
            data["smoke_risk_cost"] = self._weights.smoke * smoke_risk if strategy == RouteStrategy.TWIN_OPTIMIZED else 0.0
            data["crowd_cost"] = self._weights.crowd * crowd_risk if strategy == RouteStrategy.TWIN_OPTIMIZED else 0.0
            data["weight"] = float(total_cost)

        return graph

    def _path_coordinates(self, path_nodes: Iterable[str]) -> list[RouteCoordinate]:
        rows: list[RouteCoordinate] = []
        for node_id in path_nodes:
            node = NODES.get(node_id)
            if node is None:
                continue
            rows.append(RouteCoordinate(node_id=node_id, x=node.x, y=node.y, z=node.z, floor_id=node.floor_id))
        return rows

    def _path_metrics(self, graph: nx.Graph, path_nodes: list[str]) -> _PathMetrics:
        distance = 0.0
        total_cost = 0.0
        fire_cost = 0.0
        smoke_cost = 0.0
        congestion_cost = 0.0
        exposure = 0.0
        peak_segment_congestion = 0.0
        unsafe_segments = 0

        for src, dst in zip(path_nodes[:-1], path_nodes[1:]):
            edge = graph.get_edge_data(src, dst, default={})
            distance += float(edge.get("distance_cost", edge.get("distance", 0.0)))
            total_cost += float(edge.get("weight", 0.0))
            fire_cost += float(edge.get("fire_risk_cost", 0.0))
            smoke_cost += float(edge.get("smoke_risk_cost", 0.0))
            congestion_segment = float(edge.get("crowd_cost", 0.0))
            congestion_cost += congestion_segment
            peak_segment_congestion = max(peak_segment_congestion, congestion_segment)
            exposure += float(edge.get("fire_risk_cost", 0.0) + edge.get("smoke_risk_cost", 0.0))
            if float(edge.get("fire_risk_cost", 0.0)) + float(edge.get("smoke_risk_cost", 0.0)) >= 7.5:
                unsafe_segments += 1

        return _PathMetrics(
            distance_meters=round(distance, 3),
            total_cost=round(total_cost, 6),
            fire_risk_cost=round(fire_cost, 6),
            smoke_risk_cost=round(smoke_cost, 6),
            congestion_cost=round(congestion_cost, 6),
            hazard_exposure_score=round(exposure, 6),
            peak_route_congestion=round(peak_segment_congestion, 6),
            unsafe_segments=unsafe_segments,
        )

    def _candidate_exits(self, graph: nx.Graph, target_exit_id: str | None) -> list[str]:
        if target_exit_id is not None:
            return [target_exit_id] if graph.has_node(target_exit_id) else []
        return [node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") == "exit"]

    def _find_best_path(self, graph: nx.Graph, start_node: str, target_exit_id: str | None) -> tuple[list[str], str | None, RouteStatus]:
        exits = self._candidate_exits(graph, target_exit_id)
        if start_node not in graph:
            return [], None, RouteStatus.NO_SAFE_ROUTE

        best_path: list[str] = []
        best_exit: str | None = None
        best_cost = float("inf")

        for exit_id in exits:
            try:
                path = nx.shortest_path(graph, source=start_node, target=exit_id, weight="weight", method="dijkstra")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

            metrics = self._path_metrics(graph, path)
            if metrics.total_cost < best_cost:
                best_cost = metrics.total_cost
                best_path = path
                best_exit = exit_id

        if not best_path:
            return [], None, RouteStatus.NO_SAFE_ROUTE
        return best_path, best_exit, RouteStatus.OPEN

    def route(
        self,
        *,
        start_zone_id: str,
        strategy: RouteStrategy,
        fire_state: FireEnvironmentTwinState,
        building_state: BuildingInfrastructureTwinState,
        occupancy_state: OccupancyEvacuationTwinState,
        target_exit_id: str | None = None,
        recalculation_trigger: str | None = None,
    ) -> EvacuationRouteResponse:
        start_node = resolve_start_node(start_zone_id)

        if strategy == RouteStrategy.STATIC_PLAN:
            graph = self._build_dynamic_graph(
                fire_state=fire_state,
                building_state=building_state,
                occupancy_state=occupancy_state,
                start_zone_id=start_zone_id,
                strategy=RouteStrategy.SHORTEST_PATH,
            )
            static_path = static_plan_route()
            valid = all(graph.has_edge(src, dst) for src, dst in zip(static_path[:-1], static_path[1:])) and graph.has_node(static_path[-1])
            if not valid:
                return EvacuationRouteResponse(
                    strategy=strategy,
                    algorithm="STATIC",
                    start_zone_id=start_zone_id,
                    selected_exit=None,
                    status=RouteStatus.NO_SAFE_ROUTE,
                    recalculation_trigger=recalculation_trigger,
                )
            path_nodes = static_path
            selected_exit = static_path[-1]
            status = RouteStatus.OPEN
        else:
            graph = self._build_dynamic_graph(
                fire_state=fire_state,
                building_state=building_state,
                occupancy_state=occupancy_state,
                start_zone_id=start_zone_id,
                strategy=strategy,
            )
            path_nodes, selected_exit, status = self._find_best_path(graph, start_node, target_exit_id)

        if status == RouteStatus.NO_SAFE_ROUTE:
            return EvacuationRouteResponse(
                strategy=strategy,
                algorithm="DIJKSTRA",
                start_zone_id=start_zone_id,
                selected_exit=None,
                status=status,
                recalculation_trigger=recalculation_trigger,
            )

        metrics = self._path_metrics(graph, path_nodes)
        congestion_factor = self._zone_congestion_factor(occupancy_state, start_zone_id)

        return EvacuationRouteResponse(
            strategy=strategy,
            algorithm="DIJKSTRA",
            start_zone_id=start_zone_id,
            selected_exit=selected_exit,
            path_nodes=path_nodes,
            path_coordinates=self._path_coordinates(path_nodes),
            distance_meters=metrics.distance_meters,
            total_cost=metrics.total_cost,
            fire_risk_cost=metrics.fire_risk_cost,
            smoke_risk_cost=metrics.smoke_risk_cost,
            congestion_cost=metrics.congestion_cost,
            hazard_exposure_score=metrics.hazard_exposure_score,
            peak_route_congestion=metrics.peak_route_congestion,
            unsafe_segments=metrics.unsafe_segments,
            estimated_time_seconds=round(estimate_time_seconds(metrics.distance_meters, congestion_factor), 3),
            status=status,
            recalculation_trigger=recalculation_trigger,
        )

    def compare(
        self,
        *,
        start_zone_id: str,
        fire_state: FireEnvironmentTwinState,
        building_state: BuildingInfrastructureTwinState,
        occupancy_state: OccupancyEvacuationTwinState,
        target_exit_id: str | None = None,
    ) -> EvacuationComparisonResponse:
        results = [
            self.route(
                start_zone_id=start_zone_id,
                strategy=strategy,
                fire_state=fire_state,
                building_state=building_state,
                occupancy_state=occupancy_state,
                target_exit_id=target_exit_id,
            )
            for strategy in (RouteStrategy.STATIC_PLAN, RouteStrategy.SHORTEST_PATH, RouteStrategy.TWIN_OPTIMIZED)
        ]

        return EvacuationComparisonResponse(start_zone_id=start_zone_id, target_exit_id=target_exit_id, results=results)
