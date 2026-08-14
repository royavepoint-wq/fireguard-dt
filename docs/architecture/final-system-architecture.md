# FireGuard DT Final System Architecture

## End-to-End Architecture

Physical or Simulated Environment
-> Domain Digital Twins
-> Event and State Backbone
-> AI / Decision Orchestrator
-> ML, Explainability, Optimization, Governance
-> Shared 3D Spatial Context
-> Command Center, Scenario Lab, Response, ROI, Presentation Mode

## Domain Twins

- Fire & Environment Twin:
  - sensor state, risk probabilities, risk class
- Building Infrastructure Twin:
  - exits, corridors, HVAC, sprinklers, electrical zones
- Occupancy & Evacuation Twin:
  - occupancy zones, congestion, active routes
- Emergency Response Twin:
  - incidents, crews, drones, dispatch queue

## Decision Layer

- AI / Decision Orchestrator:
  - cross-twin status snapshot
  - active alerts and human-oversight state
- ML fire-risk model:
  - live prediction and evaluated test metrics
- Explainable AI:
  - local contributors, global importance, physical consistency checks
- Evacuation optimizer:
  - static, shortest-path, twin-optimized route outputs
- Governance gate:
  - approval checkpoint for high-risk actions
  - approved/rejected branches affect scenario outcome

## State Ownership

- Backend simulation and twin services are the primary source of truth.
- Frontend pages consume backend APIs and shared runtime polling.
- Presentation mode and command center read synchronized incident state and events.

## Evidence Pipeline

- Deterministic experiment runs generate scenario and governance outputs.
- Aggregation writes final technical and ROI metrics.
- Export package in data/final provides assignment-ready artifacts:
  - project_metrics.json
  - ml_metrics.csv
  - scenario_comparison.csv
  - governance_comparison.csv
  - response_metrics.csv
  - roi_scenarios.csv

## Scope Boundaries

- Included: deterministic simulation, ML evaluation, explainability, optimization, governance branching, ROI calculation, integrated UI.
- Excluded: real external IoT integration, production cloud deployment, advanced CFD fire simulation, safety certification.
