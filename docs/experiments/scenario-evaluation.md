# Step 7 Scenario Evaluation Methodology

## Scope

Step 7 introduces a deterministic Scenario Experiment Engine to produce repeatable metrics for:

- Standard Electrical Fire
- Blocked Exit
- Peak Occupancy
- HVAC Smoke Propagation
- Sprinkler Failure
- Sensor Anomaly (limited)

## Fair Strategy Comparison

For each scenario run, route strategies are evaluated against the same underlying hazard state:

- STATIC_PLAN
- SHORTEST_PATH
- TWIN_OPTIMIZED

Hazard conditions are not re-randomized per strategy. This keeps comparison fair.

## Core Metrics

Per scenario and strategy, the engine records:

- evacuation_time
- hazard_exposure_score
- peak_congestion
- unsafe_segment_count
- distance_travelled
- selected_exit
- time_to_warning
- time_to_critical
- time_to_evacuation
- time_to_first_dispatch
- time_to_first_response
- time_to_containment
- time_to_resolution
- occupants_at_risk
- occupants_evacuated
- resources_dispatched

When unavailable, metrics are reported as N/A.

## Hazard Exposure Prototype Metric

Prototype simulation metric:

hazard_exposure = sum(occupants_on_segment * segment_hazard_risk * time_on_segment)

The current implementation uses route hazard score, affected occupancy, and evacuation window scaling to produce a deterministic normalized score.

This is a simulation risk score and not a clinical or certified safety-damage metric.

## Congestion Definition

peak_congestion is the maximum route-edge congestion observed during evacuation.

Values come from route optimization metrics with fallback to occupancy-level congestion bands.

## Strategy Deltas

Comparison outputs include:

- evacuation_time_change_vs_static_pct
- hazard_exposure_reduction_vs_static_pct
- congestion_reduction_vs_static_pct

Formula (for lower-is-better metrics):

Improvement % = (Baseline - Proposed) / Baseline * 100

If a value is negative, it indicates slower/higher than baseline and is shown honestly.
