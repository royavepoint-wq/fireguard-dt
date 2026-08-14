from __future__ import annotations

from fastapi import APIRouter

from app.models.orchestrator import OrchestratorSnapshot
from app.services import orchestrator_service

router = APIRouter(prefix="/api")


@router.get("/orchestrator/status", response_model=OrchestratorSnapshot)
def get_orchestrator_status() -> OrchestratorSnapshot:
    return orchestrator_service.get_snapshot()