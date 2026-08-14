"""Singleton service registry for the FireGuard DT backend."""

from app.services.building_twin_service import BuildingTwinService
from app.services.evacuation.route_optimizer import EvacuationRouteOptimizer
from app.experiments.runner import ExperimentRunner
from app.services.event_bus import InMemoryEventBus
from app.services.explainability.explainer import FireRiskExplainer
from app.services.fire_twin_service import FireTwinService
from app.services.ml.fire_predictor import FireRiskPredictor
from app.services.ml.model_loader import FireRiskModelLoader
from app.services.occupancy_twin_service import OccupancyTwinService
from app.services.orchestrator import DecisionOrchestratorService
from app.services.roi.calculator import RoiCalculator
from app.services.response_twin_service import ResponseTwinService
from app.simulation.engine import SimulationEngine

event_bus = InMemoryEventBus(max_events=500)
fire_twin_service = FireTwinService(event_bus)
building_twin_service = BuildingTwinService(event_bus)
occupancy_twin_service = OccupancyTwinService(event_bus)
response_twin_service = ResponseTwinService(event_bus)
fire_risk_model_loader = FireRiskModelLoader()
fire_risk_predictor = FireRiskPredictor(loader=fire_risk_model_loader)
fire_risk_explainer = FireRiskExplainer(loader=fire_risk_model_loader, predictor=fire_risk_predictor)
evacuation_route_optimizer = EvacuationRouteOptimizer()
orchestrator_service = DecisionOrchestratorService(
	fire_twin_service=fire_twin_service,
	building_twin_service=building_twin_service,
	occupancy_twin_service=occupancy_twin_service,
	response_twin_service=response_twin_service,
	fire_risk_predictor=fire_risk_predictor,
)
simulation_engine = SimulationEngine(
	event_bus=event_bus,
	fire_twin_service=fire_twin_service,
	building_twin_service=building_twin_service,
	occupancy_twin_service=occupancy_twin_service,
	response_twin_service=response_twin_service,
	fire_risk_predictor=fire_risk_predictor,
	evacuation_route_optimizer=evacuation_route_optimizer,
)
experiment_runner = ExperimentRunner(simulation_engine=simulation_engine, event_bus=event_bus, fire_risk_predictor=fire_risk_predictor)
roi_calculator = RoiCalculator()
