from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import networkx as nx


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    x: float
    y: float
    z: float
    floor_id: str
    node_type: str


NODES: dict[str, GraphNode] = {
    "room-electrical-01": GraphNode("room-electrical-01", -5.2, 0.25, 2.8, "floor-1", "room"),
    "room-office-a-01": GraphNode("room-office-a-01", 2.4, 0.25, 3.0, "floor-1", "room"),
    "corridor-c": GraphNode("corridor-c", -1.2, 0.25, -1.4, "floor-1", "corridor"),
    "junction-a": GraphNode("junction-a", 2.4, 0.25, -1.3, "floor-1", "junction"),
    "junction-b": GraphNode("junction-b", -5.2, 0.25, -1.2, "floor-1", "junction"),
    "exit-a": GraphNode("exit-a", 7.4, 0.25, -3.8, "floor-1", "exit"),
    "exit-b": GraphNode("exit-b", -7.8, 0.25, -3.8, "floor-1", "exit"),
}

# edge_id is aligned to corridor or synthetic segments for route semantics
EDGES: list[tuple[str, str, str]] = [
    ("room-electrical-01", "corridor-c", "corridor-c"),
    ("corridor-c", "junction-a", "corridor-c"),
    ("corridor-c", "junction-b", "corridor-c"),
    ("room-electrical-01", "junction-b", "segment-room-to-b"),
    ("room-office-a-01", "junction-a", "segment-office-to-a"),
    ("room-office-a-01", "corridor-c", "corridor-c"),
    ("junction-a", "exit-a", "segment-a-to-exit"),
    ("junction-b", "exit-b", "segment-b-to-exit"),
    ("junction-a", "junction-b", "segment-a-b"),
]

STATIC_ROUTE: list[str] = ["room-electrical-01", "corridor-c", "junction-a", "exit-a"]

ZONE_TO_NODE = {
    "zone-1a": "room-electrical-01",
    "zone-1b": "room-office-a-01",
}


def _distance(a: GraphNode, b: GraphNode) -> float:
    return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def build_base_graph() -> nx.Graph:
    graph = nx.Graph()
    for node in NODES.values():
        graph.add_node(
            node.node_id,
            x=node.x,
            y=node.y,
            z=node.z,
            floor_id=node.floor_id,
            node_type=node.node_type,
        )

    for src, dst, edge_id in EDGES:
        graph.add_edge(src, dst, edge_id=edge_id, distance=_distance(NODES[src], NODES[dst]))

    return graph


def resolve_start_node(start_zone_id: str) -> str:
    if start_zone_id in NODES:
        return start_zone_id
    return ZONE_TO_NODE.get(start_zone_id, start_zone_id)
