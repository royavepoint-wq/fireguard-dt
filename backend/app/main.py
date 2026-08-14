from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.events import router as events_router
from app.api.experiments import router as experiments_router
from app.api.evacuation import router as evacuation_router
from app.api.ml import router as ml_router
from app.api.orchestrator import router as orchestrator_router
from app.api.roi import router as roi_router
from app.api.simulation import router as simulation_router
from app.api.system import router as system_router
from app.api.twins import router as twins_router
from app.services import fire_risk_model_loader

app = FastAPI(title="FireGuard DT API")
logger = logging.getLogger("fireguard.ml")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "FireGuard DT API",
    }


@app.on_event("startup")
def startup_ml_health() -> None:
    bundle = fire_risk_model_loader.load()
    logger.info("[ML] Dataset type: %s", bundle.metadata.get("dataset_type", "synthetic"))
    logger.info("[ML] Selected model: %s", bundle.metadata.get("model_name", "ML Model Unavailable"))
    logger.info("[ML] Model version: %s", bundle.metadata.get("model_version", "fire-risk-v1"))
    logger.info("[ML] Artifact loaded: %s", "YES" if bundle.available else "NO")
    metrics = bundle.metadata.get("metrics") or bundle.metadata.get("test_metrics", {})
    if metrics:
        logger.info("[ML] Test Macro F1: %s", metrics.get("macro_f1"))
        logger.info("[ML] Critical Recall: %s", metrics.get("critical_recall"))
    if not bundle.available:
        logger.warning("[ML] Falling back to rule-based risk")
        logger.warning("[ML] Reason: %s", bundle.message)


app.include_router(system_router)
app.include_router(twins_router)
app.include_router(events_router)
app.include_router(orchestrator_router)
app.include_router(simulation_router)
app.include_router(ml_router)
app.include_router(evacuation_router)
app.include_router(experiments_router)
app.include_router(roi_router)
