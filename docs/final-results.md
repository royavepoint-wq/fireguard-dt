# FireGuard DT - Final Results

## Predictive ML

Selected model: Logistic Regression.

Held-out synthetic test metrics:

- Accuracy: 0.979111
- Macro Precision: 0.971994
- Macro Recall: 0.975503
- Macro F1: 0.973639
- Weighted F1: 0.979072
- Critical Precision: 0.955882
- Critical Recall: 0.984848
- Critical F1: 0.970149
- ROC-AUC: 0.997537

Authoritative source: backend/models/fire_risk_model_metadata.json.

## Evacuation Optimization

Multi-scenario aggregate (4 scenarios):

- Static Plan time: 94.302 s
- Shortest Path time: 55.0 s
- Twin Optimized time: 55.0 s
- Twin Optimized time change vs Static: 36.593%
- Twin Optimized hazard exposure: 28.463
- Twin Optimized peak congestion: 0.875

Hazard exposure reduction vs Static is N/A because static baseline hazard exposure is zero in the aggregated output.

Authoritative source: data/final/project_metrics.json and data/final/scenario_comparison.csv.

## Emergency Response

Measured response metrics:

- Time to first dispatch: 0 s
- Time to first response: 37 s
- Time to containment: 42 s
- Time to resolution: 70 s
- Resources dispatched: 2

No active incident expectation:

- Response ETA shown as N/A (not TBD) for empty active-incident context.

Authoritative source: data/final/response_metrics.csv and simulation status summaries.

## Governance Decision Impact

Standard Electrical Fire branch comparison:

- Approved branch:
  - HVAC final status: ISOLATED
  - Containment: 42 s
  - Resolution: 70 s
  - Hazard exposure score: 18.319
  - Unsafe-zone duration: 42 s
  - Outcome quality: OPTIMAL
- Rejected branch:
  - HVAC final status: APPROVAL_BLOCKED
  - Containment: 70 s
  - Resolution: 90 s
  - Hazard exposure score: 7.407
  - Unsafe-zone duration: 90 s
  - Outcome quality: DEGRADED

Measured difference: containment and resolution are slower in rejection branch, unsafe-zone duration is longer, and outcome degrades from OPTIMAL to DEGRADED.

Authoritative source: data/final/governance_comparison.csv and repeated simulation runs.

## ROI

Illustrative financial model outputs:

- Conservative projected 3-year ROI: 1.34%
- Base projected 3-year ROI: 78.91%
- Optimistic projected 3-year ROI: 149.81%
- Base payback period: 15.5 months
- Base initial investment: 820000.0 SGD
- Base annual benefit: 820000.0 SGD

All ROI values are illustrative project assumptions, not measured real-world savings.

Authoritative source: data/final/roi_scenarios.csv and /api/roi/scenarios.

## Explainable AI Verification

Model-derived explanation checks were verified across three classes using explicit input payloads:

- NORMAL case: class NORMAL, confidence 0.999672, critical probability 0.0
- WARNING case: class WARNING, confidence 0.69713, critical probability 0.30287
- CRITICAL case: class CRITICAL, confidence 1.0, critical probability 1.0

Top contributors and physical-consistency status changed with each case.

## Scenario Lab Verification

Verified scenarios:

- standard-electrical-fire
- blocked-exit
- peak-occupancy
- sprinkler-failure

Results differ by scenario conditions and strategy outputs (time, distance, selected exit, exposure, congestion).

## Limitations

- Synthetic training dataset and synthetic simulation environment
- Simplified fire and smoke progression model
- Simplified occupant movement dynamics
- Prototype route cost weighting
- Illustrative ROI assumptions
- Academic prototype, not safety-certified for real emergency-management deployment
