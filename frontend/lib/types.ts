export type StatusTone = "safe" | "warning" | "critical" | "info" | "muted";

export type TwinStatus = "ONLINE" | "DEGRADED" | "OFFLINE";

export type RiskLevel = "NORMAL" | "WARNING" | "CRITICAL";
export type PredictionSource = "ML_MODEL" | "RULE_BASED_FALLBACK" | "NOT_AVAILABLE";
export type ExplanationMethod = "SHAP" | "LOGISTIC_CONTRIBUTION" | "PERTURBATION_FALLBACK";
export type ContributionDirection = "increases_risk" | "decreases_risk" | "neutral";
export type PhysicalConsistencyStatus = "PHYSICALLY_CONSISTENT" | "SENSOR_CONFLICT" | "INSUFFICIENT_MULTI_SENSOR_SUPPORT";

export type SensorHealth = "HEALTHY" | "WARNING" | "FAULT";

export type ResourceStatus = "AVAILABLE" | "ASSIGNED" | "EN_ROUTE" | "ON_SCENE" | "UNAVAILABLE";

export type EventSeverity = "INFO" | "WARNING" | "CRITICAL";

export type OrchestratorStatus = "NORMAL" | "WARNING" | "CRITICAL" | "DEGRADED";

export type TimelineEvent = {
  event_id?: string;
  time?: string;
  timestamp?: string;
  severity?: EventSeverity;
  source_twin?: string;
  event_type?: string;
  payload?: Record<string, unknown>;
  message: string;
};

export type MetricValue = string | number;

export type TwinMetric = {
  label: string;
  value: MetricValue;
};

export type Floor = {
  floor_id: string;
  name: string;
  level: number;
  zone_ids: string[];
};

export type Room = {
  room_id: string;
  name: string;
  floor_id: string;
  zone_id: string;
  room_type: string;
  occupancy_limit: number | null;
};

export type Corridor = {
  corridor_id: string;
  name: string;
  floor_id: string;
  zone_id: string;
  is_accessible: boolean;
  status?: string;
};

export type Exit = {
  exit_id: string;
  name: string;
  floor_id: string | null;
  zone_id: string | null;
  is_available: boolean;
  is_blocked: boolean;
};

export type HVACZone = {
  hvac_zone_id: string;
  name: string;
  floor_id: string;
  status: string;
  airflow_percentage: number;
};

export type Sprinkler = {
  sprinkler_id: string;
  zone_id: string;
  status: string;
  is_active: boolean;
};

export type ElectricalZone = {
  electrical_zone_id: string;
  name: string;
  floor_id: string;
  load_percentage: number;
  status: string;
};

export type FireTwinState = {
  twin_id: string;
  name: string;
  status: TwinStatus;
  last_updated: string;
  building_id: string;
  floor_id: string;
  zone_id: string;
  temperature: number;
  temperature_rate: number;
  smoke_level: number;
  co_level: number;
  co2_level: number;
  humidity: number;
  electrical_load: number;
  fire_risk_probability: number;
  risk_level: RiskLevel;
  risk_probabilities: Record<RiskLevel, number>;
  prediction_source: PredictionSource;
  model_version: string | null;
  prediction_confidence: number;
  sensor_health: SensorHealth;
  hvac_effect: number;
};

export type BuildingTwinState = {
  twin_id: string;
  name: string;
  status: TwinStatus;
  last_updated: string;
  building_id: string;
  floors: Floor[];
  rooms: Room[];
  corridors: Corridor[];
  exits: Exit[];
  hvac_zones: HVACZone[];
  sprinklers: Sprinkler[];
  electrical_zones: ElectricalZone[];
};

export type OccupancyZone = {
  zone_id: string;
  occupancy_count: number;
  density: number;
  vulnerable_count: number;
  evacuation_status: "STABLE" | "EVACUATING" | "EVACUATED";
};

export type EvacuationRoute = {
  route_id: string;
  from_zone_id: string;
  to_exit_id: string;
  status: "OPEN" | "CONGESTED" | "BLOCKED" | "NO_SAFE_ROUTE";
  estimated_capacity: number;
  strategy?: "STATIC_PLAN" | "SHORTEST_PATH" | "TWIN_OPTIMIZED";
  path_nodes?: string[];
  path_coordinates?: RouteCoordinate[];
  distance_meters?: number;
  estimated_time_seconds?: number;
  total_cost?: number;
  fire_risk_cost?: number;
  smoke_risk_cost?: number;
  congestion_cost?: number;
  hazard_exposure_score?: number;
  peak_route_congestion?: number;
  unsafe_segments?: number;
};

export type RouteCoordinate = {
  node_id: string;
  x: number;
  y: number;
  z: number;
  floor_id: string;
};

export type OccupancyTwinState = {
  twin_id: string;
  name: string;
  status: TwinStatus;
  last_updated: string;
  building_id: string;
  total_occupancy: number;
  zones: OccupancyZone[];
  evacuating_count: number;
  evacuated_count: number;
  congestion_level: "LOW" | "MODERATE" | "HIGH";
  active_routes: EvacuationRoute[];
};

export type ResponseCrew = {
  crew_id: string;
  name: string;
  status: ResourceStatus;
  current_zone_id: string | null;
  eta_minutes: number;
};

export type InspectionDrone = {
  drone_id: string;
  name: string;
  status: ResourceStatus;
  current_zone_id: string | null;
  battery_level: number;
  eta_minutes: number;
};

export type DispatchTask = {
  task_id: string;
  resource_id: string;
  resource_type: string;
  status: ResourceStatus;
  target_zone_id: string | null;
  description: string;
};

export type Incident = {
  incident_id: string;
  incident_type: string;
  severity: EventSeverity;
  status: string;
  zone_id: string | null;
  description: string;
};

export type ResponseTwinState = {
  twin_id: string;
  name: string;
  status: TwinStatus;
  last_updated: string;
  crews: ResponseCrew[];
  drones: InspectionDrone[];
  active_incidents: Incident[];
  dispatch_queue: DispatchTask[];
  average_response_eta: number;
};

export type DigitalTwinEvent = {
  event_id: string;
  event_type: string;
  source_twin: string;
  target_twins: string[];
  severity: EventSeverity;
  timestamp: string;
  building_id: string | null;
  floor_id: string | null;
  zone_id: string | null;
  room_id: string | null;
  corridor_id: string | null;
  exit_id: string | null;
  message: string;
  payload: Record<string, unknown>;
};

export type OrchestratorSnapshot = {
  status: OrchestratorStatus;
  human_oversight: boolean;
  active_alerts: string[];
  twins_online: number;
  cross_twin_state: Record<string, unknown>;
  last_updated: string;
};

export type SimulationStatus = "STOPPED" | "RUNNING" | "PAUSED" | "WAITING_FOR_APPROVAL" | "COMPLETED" | "ERROR";

export type SimulationPauseReason = "MANUAL" | "AWAITING_APPROVAL";

export type SimulationPhase =
  | "NORMAL"
  | "ANOMALY"
  | "WARNING"
  | "CRITICAL"
  | "EVACUATION"
  | "RESPONSE"
  | "CONTAINMENT"
  | "RESOLVED";

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export type ScenarioSupportLevel = "FULL" | "PARAMETERIZED" | "LIMITED";

export type GovernanceDecision = "PENDING" | "HVAC_ISOLATION_APPROVED" | "HVAC_ISOLATION_REJECTED";

export type OutcomeQuality = "OPTIMAL" | "DEGRADED";

export type SimulationApprovalState = {
  approval_id: string;
  action_type: string;
  action_description: string;
  risk_level: RiskLevel;
  requested_simulation_time: number;
  status: ApprovalStatus;
  requested_at: string;
  decision: ApprovalStatus | null;
  decided_at: string | null;
  decision_source: string | null;
  auto_approve: boolean;
  message: string;
};

export type SimulationRunSummary = {
  run_id: string;
  scenario: string;
  started_at: string;
  completed_at: string | null;
  duration: number;
  max_risk: string;
  occupants_at_risk: number;
  evacuated: number;
  response_dispatch_time: number | null;
  containment_time: number | null;
  status: SimulationStatus;
  time_to_warning: number | null;
  time_to_critical: number | null;
  time_to_evacuation: number | null;
  time_to_first_dispatch: number | null;
  time_to_first_response: number | null;
  time_to_containment: number | null;
  time_to_resolution: number | null;
  evacuation_completion_time: number | null;
  peak_congestion: string | null;
  resources_dispatched: number;
  unsafe_zone_duration: number;
  risk_exposure_score: number;
  governance_decision: GovernanceDecision;
  outcome_quality: OutcomeQuality | null;
  decision_impact_summary: string | null;
  model_version: string | null;
  prediction_source: PredictionSource;
  max_critical_probability: number;
  first_warning_prediction_time: number | null;
  first_critical_prediction_time: number | null;
  static_plan_metrics: Record<string, unknown> | null;
  shortest_path_metrics: Record<string, unknown> | null;
  twin_optimized_metrics: Record<string, unknown> | null;
};

export type SimulationState = {
  simulation_id: string;
  scenario_id: string | null;
  scenario_name: string | null;
  status: SimulationStatus;
  phase: SimulationPhase;
  elapsed_seconds: number;
  speed_multiplier: number;
  is_paused: boolean;
  pause_reason: SimulationPauseReason | null;
  started_at: string | null;
  completed_at: string | null;
  current_step: number;
  total_steps: number;
  progress: number;
  auto_approve: boolean;
  current_stage_label: string;
  presentation_mode: boolean;
  run_id: string | null;
  pending_approval: SimulationApprovalState | null;
  approved_actions: string[];
  rejected_actions: string[];
  governance_decision: GovernanceDecision;
  outcome_quality: OutcomeQuality | null;
  last_error: string | null;
  latest_run_summary: SimulationRunSummary | null;
};

export type SimulationScenario = {
  scenario_id: string;
  name: string;
  description: string;
  building_id: string;
  floor_id: string;
  origin_zone_id: string;
  affected_corridor_id: string;
  duration_seconds: number;
  initial_occupancy: number;
  affected_zone_occupancy: number;
  support_level: ScenarioSupportLevel;
  initial_exit_b_blocked: boolean;
  peak_occupancy: boolean;
  hvac_smoke_propagation: boolean;
  sprinkler_failure: boolean;
  sensor_anomaly_mode: boolean;
  implementation_note: string;
};

export type SimulationStartRequest = {
  scenario_id: string;
  speed_multiplier: number;
  auto_approve: boolean;
  presentation_mode?: boolean;
};

export type CombinedDigitalTwinState = {
  fire_twin: FireTwinState;
  building_twin: BuildingTwinState;
  occupancy_twin: OccupancyTwinState;
  response_twin: ResponseTwinState;
  orchestrator: OrchestratorSnapshot;
};

export type FireRiskPredictionRequest = {
  temperature: number;
  temperature_rate: number;
  smoke_level: number;
  co_level: number;
  co2_level: number;
  humidity: number;
  electrical_load: number;
  occupancy: number;
  hvac_running: number;
  sprinkler_active: number;
};

export type FireRiskPredictionResponse = {
  model_name: string;
  model_version: string;
  predicted_class: RiskLevel;
  confidence: number;
  probabilities: Record<RiskLevel, number>;
  input_features: FireRiskPredictionRequest;
  prediction_source: PredictionSource;
  timestamp: string;
};

export type FireRiskMetrics = {
  selected_model: string;
  model_version: string;
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  weighted_f1: number;
  roc_auc: number;
  critical_precision: number;
  critical_recall: number;
  critical_f1: number;
};

export type FireRiskModelInfo = {
  status: "ONLINE" | "FALLBACK";
  model_version: string;
  model_name: string;
  loaded_successfully: boolean;
  loaded: boolean;
  prediction_source: PredictionSource;
  features: string[];
  classes: string[];
  random_state: number;
  dataset_type: string;
  synthetic_dataset_disclaimer: string;
  error: string | null;
  evaluation_metrics: Record<string, number>;
  model_comparison: Array<Record<string, string | number>>;
  confusion_matrix: Array<{ actual: string; NORMAL: number; WARNING: number; CRITICAL: number }>;
};

export type FeatureContribution = {
  feature: string;
  feature_label: string;
  value: number;
  contribution: number;
  direction: ContributionDirection;
};

export type PhysicalConsistencyResult = {
  status: PhysicalConsistencyStatus;
  message: string;
  checks: Record<string, boolean>;
};

export type FireRiskExplanationResponse = {
  predicted_class: RiskLevel;
  confidence: number;
  critical_probability: number;
  model_version: string;
  prediction_source: PredictionSource;
  explanation_method: ExplanationMethod;
  top_positive_contributors: FeatureContribution[];
  top_negative_contributors: FeatureContribution[];
  physical_consistency: PhysicalConsistencyResult;
  input_features: FireRiskPredictionRequest;
  timestamp: string;
};

export type FeatureImportanceItem = {
  feature: string;
  feature_label: string;
  importance: number;
  normalized_importance: number;
};

export type FireRiskFeatureImportanceResponse = {
  model_version: string;
  prediction_source: PredictionSource;
  explanation_method: ExplanationMethod;
  features: FeatureImportanceItem[];
};

export type EvacuationRouteStrategy = "STATIC_PLAN" | "SHORTEST_PATH" | "TWIN_OPTIMIZED";

export type EvacuationRouteRequest = {
  start_zone_id: string;
  strategy?: EvacuationRouteStrategy;
  target_exit_id?: string | null;
};

export type EvacuationRouteResponse = {
  strategy: EvacuationRouteStrategy;
  algorithm: string;
  start_zone_id: string;
  selected_exit: string | null;
  path_nodes: string[];
  path_coordinates: RouteCoordinate[];
  distance_meters: number;
  total_cost: number;
  fire_risk_cost: number;
  smoke_risk_cost: number;
  congestion_cost: number;
  hazard_exposure_score: number;
  peak_route_congestion: number;
  unsafe_segments: number;
  estimated_time_seconds: number;
  status: "OPEN" | "CONGESTED" | "BLOCKED" | "NO_SAFE_ROUTE";
  recalculation_trigger: string | null;
};

export type EvacuationComparisonResponse = {
  start_zone_id: string;
  target_exit_id: string | null;
  results: EvacuationRouteResponse[];
};

export type ScenarioReadiness = "READY" | "LIMITED";
export type ApprovalMode = "AUTO_APPROVE" | "FORCE_APPROVE" | "FORCE_REJECT";

export type ExperimentScenarioDefinition = {
  scenario_id: string;
  simulation_scenario_id: string;
  name: string;
  description: string;
  fire_origin: string;
  fire_severity: string;
  occupancy: number;
  blocked_exits: string[];
  hvac_state: string;
  sprinkler_state: string;
  scenario_seed: number;
  sensor_anomaly: boolean;
  resource_constraints: string | null;
  readiness: ScenarioReadiness;
};

export type ExperimentRunRequest = {
  scenario_ids: string[];
  strategies: EvacuationRouteStrategy[];
  runs_per_configuration: number;
  include_governance_branches?: boolean;
};

export type ExperimentStatus = {
  is_running: boolean;
  progress: number;
  total_configurations: number;
  completed_configurations: number;
  started_at: string | null;
  completed_at: string | null;
  last_error: string | null;
};

export type ExperimentResultRecord = {
  run_id: string;
  scenario_id: string;
  scenario_name: string;
  strategy: EvacuationRouteStrategy;
  approval_mode: ApprovalMode;
  evacuation_time: number | null;
  hazard_exposure_score: number | null;
  peak_congestion: number | null;
  unsafe_segment_count: number | null;
  distance_travelled: number | null;
  selected_exit: string | null;
  time_to_warning: number | null;
  time_to_critical: number | null;
  time_to_evacuation: number | null;
  time_to_first_dispatch: number | null;
  time_to_first_response: number | null;
  time_to_containment: number | null;
  time_to_resolution: number | null;
  occupants_at_risk: number | null;
  occupants_evacuated: number | null;
  resources_dispatched: number | null;
  outcome_quality: string | null;
  unsafe_zone_duration: number | null;
  status: string;
  generated_at: string;
};

export type StrategyComparisonRecord = {
  scenario_id: string;
  scenario_name: string;
  strategy: EvacuationRouteStrategy;
  evacuation_time: number | null;
  hazard_exposure_score: number | null;
  peak_congestion: number | null;
  distance_travelled: number | null;
  selected_exit: string | null;
  evacuation_time_change_vs_static_pct: number | null;
  hazard_exposure_reduction_vs_static_pct: number | null;
  congestion_reduction_vs_static_pct: number | null;
  recommendation_label: string | null;
};

export type GovernanceComparisonRecord = {
  scenario_id: string;
  branch: ApprovalMode;
  containment_time: number | null;
  hazard_exposure_score: number | null;
  evacuation_time: number | null;
  unsafe_zone_duration: number | null;
  response_resources_used: number | null;
  outcome_quality: string | null;
};

export type ExperimentResultsResponse = {
  status: ExperimentStatus;
  scenario_results: ExperimentResultRecord[];
  strategy_comparison: StrategyComparisonRecord[];
  governance_comparison: GovernanceComparisonRecord[];
};

export type EvidenceRefreshResponse = {
  status: string;
  path: string;
  scenario_results: number;
  strategy_rows: number;
  governance_rows: number;
};

export type RoiScenario = "CONSERVATIVE" | "BASE" | "OPTIMISTIC";

export type RoiAssumptions = {
  scenario: RoiScenario;
  currency: string;
  illustrative_label: string;
  iot_sensor_integration: number;
  edge_gateway_infrastructure: number;
  twin_platform_development: number;
  ml_model_development: number;
  security_hardening: number;
  training_and_drills: number;
  annual_cloud_operations: number;
  annual_maintenance: number;
  avoided_downtime: number;
  damage_risk_reduction: number;
  maintenance_savings: number;
  response_efficiency: number;
  false_alarm_reduction: number;
  compliance_preparedness_value: number;
};

export type RoiCalculationRequest = {
  scenario: RoiScenario;
  assumptions_override?: RoiAssumptions | null;
};

export type RoiCalculationResult = {
  scenario: RoiScenario;
  currency: string;
  illustrative_label: string;
  initial_investment: number;
  annual_operating_cost: number;
  annual_benefit: number;
  annual_net_benefit: number;
  payback_months: number | null;
  payback_statement: string;
  three_year_cost: number;
  three_year_benefit: number;
  three_year_roi_percent: number;
  cost_breakdown: Record<string, number>;
  benefit_breakdown: Record<string, number>;
  technical_evidence: Record<string, string | number>;
  assumption_disclosure: string;
};

export type RoiScenarioSetResponse = {
  scenarios: RoiAssumptions[];
};
