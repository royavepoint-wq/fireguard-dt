# Step 7 Emergency Response Metrics

## Objective

Replace response placeholders with simulation-derived metrics and live twin state values.

## ETA Rules

- No active incident: ETA is N/A.
- Active dispatch: ETA uses deterministic twin ETA values for crew and drone resources.
- On-scene resources show 00:00.

## Timing Definitions

Relative to critical incident trigger:

- time_to_first_dispatch: critical trigger -> first dispatch assignment
- time_to_first_response: critical trigger -> first resource ON_SCENE
- time_to_containment: critical trigger -> containment transition
- time_to_resolution: critical trigger -> stable resolved condition

## Stable Resolved Condition

RESOLVED means:

- hazard no longer uncontrolled critical
- containment achieved
- evacuation stabilized/completed
- response actions complete
- no pending governance approval

## Page Surfaces

Emergency Response page now includes:

- Active Incident details (id, location, severity, phase, age)
- Crew status table (status, assignment, ETA, location)
- Drone status table (status, assignment, ETA, location)
- Dispatch timeline from event stream
- Completed run metrics from simulation summaries

These values are deterministic simulation outputs and not live external dispatch telemetry.
