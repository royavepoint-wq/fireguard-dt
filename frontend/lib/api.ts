import type {
  BuildingTwinState,
  CombinedDigitalTwinState,
  DigitalTwinEvent,
  EvidenceRefreshResponse,
  ExperimentResultsResponse,
  ExperimentRunRequest,
  ExperimentScenarioDefinition,
  ExperimentStatus,
  EvacuationComparisonResponse,
  EvacuationRouteRequest,
  EvacuationRouteResponse,
  FireRiskExplanationResponse,
  FireRiskFeatureImportanceResponse,
  FireRiskMetrics,
  FireRiskModelInfo,
  FireRiskPredictionRequest,
  FireRiskPredictionResponse,
  FireTwinState,
  OccupancyTwinState,
  RoiCalculationRequest,
  RoiCalculationResult,
  RoiScenarioSetResponse,
  ResponseTwinState,
  SimulationRunSummary,
  SimulationScenario,
  SimulationStartRequest,
  SimulationState,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body = (await response.json()) as { detail?: string | { msg?: string }[] };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        message = body.detail[0].msg;
      }
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function getDigitalTwinState(): Promise<CombinedDigitalTwinState> {
  return request<CombinedDigitalTwinState>("/api/digital-twin/state");
}

export function getEvents(sourceTwin?: string): Promise<DigitalTwinEvent[]> {
  const suffix = sourceTwin ? `?source_twin=${encodeURIComponent(sourceTwin)}` : "";
  return request<DigitalTwinEvent[]>(`/api/events${suffix}`);
}

export function updateFireTwin(payload: Partial<FireTwinState>): Promise<FireTwinState> {
  return request<FireTwinState>("/api/twins/fire", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateBuildingTwin(payload: Partial<BuildingTwinState>): Promise<BuildingTwinState> {
  return request<BuildingTwinState>("/api/twins/building", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateOccupancyTwin(payload: Partial<OccupancyTwinState>): Promise<OccupancyTwinState> {
  return request<OccupancyTwinState>("/api/twins/occupancy", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateResponseTwin(payload: Partial<ResponseTwinState>): Promise<ResponseTwinState> {
  return request<ResponseTwinState>("/api/twins/response", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function resetDigitalTwin(): Promise<CombinedDigitalTwinState> {
  return request<CombinedDigitalTwinState>("/api/digital-twin/reset", {
    method: "POST",
  });
}

export function clearEvents(): Promise<{ status: string }> {
  return request<{ status: string }>("/api/events", {
    method: "DELETE",
  });
}

export function getSimulationStatus(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/status");
}

export function getSimulationScenarios(): Promise<SimulationScenario[]> {
  return request<SimulationScenario[]>("/api/simulation/scenarios");
}

export function getSimulationRuns(): Promise<SimulationRunSummary[]> {
  return request<SimulationRunSummary[]>("/api/simulation/runs");
}

export function startSimulation(payload: SimulationStartRequest): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function pauseSimulation(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/pause", { method: "POST" });
}

export function resumeSimulation(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/resume", { method: "POST" });
}

export function stopSimulation(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/stop", { method: "POST" });
}

export function resetSimulation(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/reset", { method: "POST" });
}

export function setSimulationSpeed(speed_multiplier: number): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/speed", {
    method: "POST",
    body: JSON.stringify({ speed_multiplier }),
  });
}

export function approveSimulationAction(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/approve", { method: "POST" });
}

export function rejectSimulationAction(): Promise<SimulationState> {
  return request<SimulationState>("/api/simulation/reject", { method: "POST" });
}

export function approveSimulationActionById(approvalId: string): Promise<SimulationState> {
  return request<SimulationState>(`/api/simulation/approval/${encodeURIComponent(approvalId)}/approve`, { method: "POST" });
}

export function rejectSimulationActionById(approvalId: string): Promise<SimulationState> {
  return request<SimulationState>(`/api/simulation/approval/${encodeURIComponent(approvalId)}/reject`, { method: "POST" });
}

export function predictFireRisk(payload: FireRiskPredictionRequest): Promise<FireRiskPredictionResponse> {
  return request<FireRiskPredictionResponse>("/api/ml/fire-risk/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getFireRiskModelInfo(): Promise<FireRiskModelInfo> {
  return request<FireRiskModelInfo>("/api/ml/fire-risk/model-info");
}

export function getFireRiskMetrics(): Promise<FireRiskMetrics> {
  return request<FireRiskMetrics>("/api/ml/fire-risk/metrics");
}

export function getFireRiskExplanation(): Promise<FireRiskExplanationResponse> {
  return request<FireRiskExplanationResponse>("/api/ml/fire-risk/explanation");
}

export function explainFireRisk(payload: FireRiskPredictionRequest): Promise<FireRiskExplanationResponse> {
  return request<FireRiskExplanationResponse>("/api/ml/fire-risk/explain", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getFireRiskFeatureImportance(): Promise<FireRiskFeatureImportanceResponse> {
  return request<FireRiskFeatureImportanceResponse>("/api/ml/fire-risk/feature-importance");
}

export function getEvacuationRoute(payload: EvacuationRouteRequest): Promise<EvacuationRouteResponse> {
  return request<EvacuationRouteResponse>("/api/evacuation/route", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function compareEvacuationRoutes(payload: EvacuationRouteRequest): Promise<EvacuationComparisonResponse> {
  return request<EvacuationComparisonResponse>("/api/evacuation/compare", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getExperimentScenarioLibrary(): Promise<ExperimentScenarioDefinition[]> {
  return request<ExperimentScenarioDefinition[]>("/api/experiments/library");
}

export function runExperiments(payload: ExperimentRunRequest): Promise<ExperimentStatus> {
  return request<ExperimentStatus>("/api/experiments/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getExperimentStatus(): Promise<ExperimentStatus> {
  return request<ExperimentStatus>("/api/experiments/status");
}

export function getExperimentResults(params?: { scenario?: string; strategy?: string }): Promise<ExperimentResultsResponse> {
  const search = new URLSearchParams();
  if (params?.scenario) {
    search.set("scenario", params.scenario);
  }
  if (params?.strategy) {
    search.set("strategy", params.strategy);
  }
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request<ExperimentResultsResponse>(`/api/experiments/results${suffix}`);
}

export function refreshEvidencePackage(): Promise<EvidenceRefreshResponse> {
  return request<EvidenceRefreshResponse>("/api/experiments/evidence/refresh", {
    method: "POST",
  });
}

export function getResultsJsonExportUrl(): string {
  return `${API_BASE_URL}/api/experiments/export/json`;
}

export function getResultsCsvExportUrl(kind = "scenario_comparison"): string {
  return `${API_BASE_URL}/api/experiments/export/csv?kind=${encodeURIComponent(kind)}`;
}

export function getRoiAssumptions(): Promise<RoiScenarioSetResponse> {
  return request<RoiScenarioSetResponse>("/api/roi/assumptions");
}

export function getRoiScenarios(): Promise<RoiScenarioSetResponse> {
  return request<RoiScenarioSetResponse>("/api/roi/scenarios");
}

export function calculateRoi(payload: RoiCalculationRequest): Promise<RoiCalculationResult> {
  return request<RoiCalculationResult>("/api/roi/calculate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}