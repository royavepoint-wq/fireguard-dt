# FireGuard DT - Slide Update Map

## Slide 1 - Title and Scope

Use project framing from README and final architecture narrative.

Source:
- README.md
- docs/architecture/final-system-architecture.md

## Slide 2 - Problem and Motivation

Use command-center storyline and adaptive response framing.

Source:
- README.md
- docs/final-results.md

## Slide 3 - Architecture

Map to final architecture chain:
Physical or Simulated Environment -> Domain Digital Twins -> Event and State Backbone -> AI / Decision Orchestrator -> ML + Optimization + Governance -> Shared 3D Spatial Model -> Emergency Command Center.

Source:
- docs/architecture/final-system-architecture.md

## Slide 4 - Digital Twin System

Use canonical terminology:
- Fire & Environment Twin
- Building Infrastructure Twin
- Occupancy & Evacuation Twin
- Emergency Response Twin
- AI / Decision Orchestrator
- Shared 3D Spatial Model (shared context, not a fifth twin)

Source:
- README.md
- docs/technical-facts.md

## Slide 5 - Simulation and Governance Flow

Use final demo sequence with approval branch split and different outcomes.

Source:
- docs/demo-script-final.md
- data/final/governance_comparison.csv

## Slide 6 - Predictive Intelligence

Use held-out synthetic test metrics:

- Accuracy: 0.979111
- Macro Precision: 0.971994
- Macro Recall: 0.975503
- Macro F1: 0.973639
- Weighted F1: 0.979072
- Critical Precision: 0.955882
- Critical Recall: 0.984848
- Critical F1: 0.970149
- ROC-AUC: 0.997537

Source:
- backend/models/fire_risk_model_metadata.json
- data/final/ml_metrics.csv

## Slide 7 - Explainable AI

Use one NORMAL/WARNING/CRITICAL comparison:

- NORMAL: class NORMAL, confidence 0.999672
- WARNING: class WARNING, confidence 0.69713
- CRITICAL: class CRITICAL, confidence 1.0

Physical consistency examples:
- NORMAL payload: INSUFFICIENT_MULTI_SENSOR_SUPPORT
- WARNING payload: PHYSICALLY_CONSISTENT
- CRITICAL payload: PHYSICALLY_CONSISTENT

Source:
- verified API outputs from /api/ml/fire-risk/explain
- docs/final-results.md

## Slide 8 - Shared 3D and Operations View

Use Command Center and Presentation Mode screenshots/elements:
- incident overlay
- route update
- response state
- governance state

Source:
- frontend live app routes

## Slide 9 - Scenario Lab and Evacuation Strategies

For Standard Electrical Fire:

- Static Plan: time 107.402, distance 14.992, exit-a, exposure 0.0
- Shortest Path: time 55.0, distance 7.677, exit-b, exposure 0.0, label FASTEST
- Twin Optimized: time 55.0, distance 7.677, exit-b, exposure 18.319, peak congestion 0.875, label SAFEST / RECOMMENDED

Source:
- data/final/scenario_comparison.csv

## Slide 10 - Emergency Response Performance

Use measured times:
- First dispatch: 0 s
- First response: 37 s
- Containment: 42 s
- Resolution: 70 s
- Resources dispatched: 2

Source:
- data/final/response_metrics.csv

## Slide 11 - Governance Impact

Use Standard Electrical Fire branch comparison:

- APPROVE: containment 42, unsafe-zone duration 42, outcome OPTIMAL, HVAC ISOLATED
- REJECT: containment 70, unsafe-zone duration 90, outcome DEGRADED, HVAC APPROVAL_BLOCKED

Source:
- data/final/governance_comparison.csv

## Slide 12 - ROI and Feasibility

Use wording Projected 3-Year ROI.

- Conservative: 1.34%
- Base: 78.91%
- Optimistic: 149.81%
- Base payback: 15.5 months

Label: Illustrative Project Assumption.

Source:
- data/final/roi_scenarios.csv
- /api/roi/scenarios

## Slide 13 - Limitations and Responsible Use

Use explicit disclaimers:
- synthetic dataset
- simplified simulation models
- illustrative ROI assumptions
- not safety-certified

Source:
- README.md
- docs/final-results.md

## Slide 14 - Final Results

Recommended headline metrics:

- Prediction Accuracy: 0.979111
- Prediction Macro F1: 0.973639
- Evacuation improvement metric: Hazard Exposure Reduction vs Static = N/A (baseline zero), therefore report Twin Optimized Hazard Exposure = 28.463 and Twin Optimized Time Change vs Static = 36.593%
- Response metric: First Response Time = 37 s (do not claim reduction without baseline)
- Projected 3-Year ROI (Base): 78.91%

Guidance:
- Prefer Hazard Exposure Reduction when defined.
- If reduction is undefined due to zero baseline, explicitly state N/A and provide direct measured exposure/time metrics.
- Use First Response Time rather than Response Time Reduction unless a valid baseline exists.

Source:
- data/final/project_metrics.json
- data/results/slide_metrics.json
- data/final/submission_metrics.json
