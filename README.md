# FireGuard DT

FireGuard DT is an academic multi-digital-twin prototype for adaptive fire-emergency decision support.

## Project Overview

FireGuard DT demonstrates one integrated operational story:

1. Monitor a normal building state
2. Detect sensor anomalies
3. Predict fire-risk escalation with ML
4. Explain the prediction with feature contributors and physical consistency checks
5. Update fire, building, occupancy, and response twins
6. Recompute evacuation routes from live hazard and congestion state
7. Dispatch response resources
8. Pause for governance approval when required
9. Resolve incident and report technical plus business-impact metrics

## Architecture

Core architecture flow:

Physical or Simulated Environment
-> Domain Digital Twins
-> Shared Event and State Backbone
-> AI / Decision Orchestrator
-> ML + Optimization + Governance
-> Shared 3D Spatial Context
-> Emergency Command Center and Presentation Mode

Digital twin domains:

- Fire & Environment Twin
- Building Infrastructure Twin
- Occupancy & Evacuation Twin
- Emergency Response Twin
- AI / Decision Orchestrator
- Shared 3D Spatial Model (shared context, not a fifth twin)

## Major Capabilities

### ML Pipeline

- Trained fire-risk classifier (NORMAL, WARNING, CRITICAL)
- Model evaluation metrics and confusion matrix
- Live inference from current Fire Twin state
- Honest fallback labeling when ML artifacts are unavailable

### Explainable AI

- Local explanation (top risk-increasing and risk-reducing contributors)
- Global feature importance
- Physical consistency checks over multi-sensor behavior

### Dynamic Evacuation Optimization

- Strategies: STATIC_PLAN, SHORTEST_PATH, TWIN_OPTIMIZED
- Route recomputation using hazard, smoke, congestion, and distance signals
- Safety-first recommendation labeling with deterministic scoring

### Simulation and Governance

- Deterministic emergency lifecycle simulation
- Approval gating for high-risk actions
- Branch outcomes for approved vs rejected governance decisions
- Time-to-warning, critical, dispatch, response, containment, and resolution metrics

### Scenario Lab and Evaluation

- Repeatable multi-scenario experiment runs
- Strategy comparison and governance impact outputs
- Unified evaluation and provenance display

### ROI Analytics

- Conservative, Base, Optimistic scenarios
- Initial investment, annual benefit, payback, 3-year ROI
- Explicit separation of simulation evidence vs illustrative financial assumptions

## Repository Structure

- frontend: Next.js app (Command Center, twin pages, 3D spatial UI, presentation mode)
- backend: FastAPI API, simulation engine, orchestration, ML and explainability services
- data/experiments: generated deterministic experiment outputs
- data/results: consolidated project and slide metrics
- data/final: exportable final evidence package for assignment submission
- docs: architecture and methodology documentation

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## ML Training and Artifact Regeneration

If ML artifacts are missing or you want to retrain using the synthetic dataset pipeline:

```bash
cd backend
source .venv/bin/activate
python scripts/run_step5_pipeline.py
```

This regenerates model artifacts under `backend/models/` and evaluation outputs under `data/ml/` used by live inference and evidence exports.

Optional frontend API override:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Run and Demo

### Main Routes

- / Command Center
- /twins Twin Ecosystem
- /spatial Shared 3D Spatial Model
- /prediction Predictive Intelligence
- /explainability Explainable AI
- /evacuation Evacuation Optimizer
- /scenarios Scenario Lab
- /response Emergency Response
- /governance Governance and Security
- /roi ROI and Evaluation Summary
- /presentation Presentation Mode

### One-Click Demo

Use RUN FULL DEMO from Command Center or Presentation Mode.

Presentation demo controls support:

- AUTO APPROVAL mode
- MANUAL APPROVAL mode (pauses at approval checkpoint)
- RESET DEMO for repeatable reruns

See docs/demo-script.md for a recommended 3-5 minute live flow.

## Testing

### Backend

```bash
cd backend
source .venv/bin/activate
pytest -q
```

### Frontend

```bash
cd frontend
npm test -- --run
npm run lint
npm run build
```

## Final Evidence Outputs

Generated files:

- data/results/slide_metrics.json
- data/results/final_project_metrics.json
- data/final/project_metrics.json
- data/final/ml_metrics.csv
- data/final/scenario_comparison.csv
- data/final/governance_comparison.csv
- data/final/response_metrics.csv
- data/final/roi_scenarios.csv

Metrics provenance types used in outputs:

- MODEL_TEST_RESULT
- SIMULATION_RESULT
- ILLUSTRATIVE_ROI

## Limitations

- Synthetic fire sensor data
- Simplified fire and smoke progression model
- Simplified occupant movement dynamics
- Prototype route cost weights and assumptions
- Illustrative ROI assumptions
- Not safety-certified and not production emergency-management software

## Academic Disclaimer

FireGuard DT is an academic simulation and decision-support prototype.
It is not certified for real emergency-management deployment.
