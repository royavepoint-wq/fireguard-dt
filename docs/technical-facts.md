# FireGuard DT - Technical Facts

## Why 4 twins?

The system separates fire conditions, building infrastructure, occupant dynamics, and emergency resources into distinct domain twins so each domain can evolve independently while remaining synchronized through shared orchestration state.

## Why the shared 3D model is not a fifth twin

The 3D layer is a visualization and spatial context surface that reads state from the twins and orchestrator. It does not own physical-domain state transitions.

## Why Logistic Regression, Random Forest, and Gradient Boosting

The training pipeline compares multiple model families with deterministic splitting and selects a final model using critical safety-oriented criteria. Logistic Regression won under the selection rule using critical recall, critical F1, macro F1, ROC-AUC, and accuracy.

## Why Critical Recall matters

In fire-risk escalation, missed CRITICAL cases are high cost. Critical recall directly measures how many actual CRITICAL samples are detected.

## Why synthetic data

The project is an academic prototype and uses synthetic fire-sensor data for safe, reproducible experimentation without claiming real incident records.

## Why Dijkstra / A*

Route optimization is graph-based over building connectivity. Deterministic shortest-path methods provide transparent and reproducible route decisions under weighted risk and congestion costs.

## Why shortest path may not be safest

Shortest distance can pass through higher hazard or congestion zones. Risk-aware optimization may choose a longer path if cumulative hazard cost is lower.

## How the route cost function works

Twin-optimized routing combines distance, fire risk, smoke risk, and congestion penalties. Recommended routes prioritize:
1. valid route
2. no unsafe segments
3. lower hazard exposure
4. lower congestion
5. lower evacuation time

## What APPROVE vs REJECT changes

Governance approval controls high-impact actions such as HVAC isolation. In measured runs:
- APPROVE branch: HVAC ends ISOLATED, containment 42 s, resolution 70 s, outcome OPTIMAL.
- REJECT branch: HVAC ends APPROVAL_BLOCKED, containment 70 s, resolution 90 s, outcome DEGRADED.

## What RESOLVED means

RESOLVED indicates the simulation incident lifecycle reached completion with no active emergency phase remaining and a finalized run summary.

## How ROI is calculated

ROI scenarios use an illustrative financial model with explicit assumptions for initial investment and annual benefit, producing payback and projected 3-year ROI outputs.

## Main limitations

- synthetic dataset
- simplified fire/smoke dynamics
- simplified occupant movement
- prototype route weighting
- illustrative ROI assumptions
- not safety-certified for real emergency deployment
