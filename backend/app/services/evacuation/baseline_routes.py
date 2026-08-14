from __future__ import annotations

from app.services.evacuation.graph_builder import STATIC_ROUTE


def static_plan_route() -> list[str]:
    return list(STATIC_ROUTE)
