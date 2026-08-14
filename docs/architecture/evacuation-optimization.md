# Evacuation Optimization Architecture (Step 6)

Step 6 replaces static route switching with graph-based dynamic optimization driven by live twin state.

## Objectives

- Compute safe egress routes from current hazard and infrastructure conditions.
- Compare baseline and optimized strategies in the same API response shape.
- Recalculate during simulation when constraints change.
- Expose route lifecycle events for operator awareness.

## Components

- `backend/app/services/evacuation/graph_builder.py`
- `backend/app/services/evacuation/cost_model.py`
- `backend/app/services/evacuation/route_optimizer.py`
- `backend/app/api/evacuation.py`
- `backend/app/simulation/engine.py` Step 6 integration

## Strategies

- `STATIC_PLAN`: fixed baseline path if still valid.
- `SHORTEST_PATH`: pure distance minimization.
- `TWIN_OPTIMIZED`: distance + hazard + congestion weighted cost.

## Weighted Cost Model

For twin-optimized routing, per-edge cost is:

$$
C_e = w_d d_e + w_f r^{fire}_e + w_s r^{smoke}_e + w_c r^{crowd}_e
$$

Where:

- $d_e$: edge distance
- $r^{fire}_e$: fire-risk term
- $r^{smoke}_e$: smoke-risk term
- $r^{crowd}_e$: congestion term
- $w_d, w_f, w_s, w_c$: configured weights in `cost_model.py`

Current assumptions:

- corridors/exits flagged inaccessible are hard constraints
- congestion uses occupancy density + vulnerable-count factor
- estimated evacuation time uses distance and congestion-adjusted walking speed
- graph solved with Dijkstra

## Event Model

Simulation publishes route lifecycle events:

- `ROUTE_RECALCULATION_REQUESTED`
- `ROUTE_UPDATED`
- `ROUTE_BLOCKED`
- `NO_SAFE_ROUTE`

## API Surface

- `POST /api/evacuation/route`
- `POST /api/evacuation/compare`

Response includes:

- selected exit and node path
- 3D path coordinates for frontend overlays
- distance, time, and cost decomposition
- exposure and unsafe-segment indicators
- route status (`OPEN`, `CONGESTED`, `BLOCKED`, `NO_SAFE_ROUTE`)

## Frontend Consumption

- `frontend/app/evacuation/page.tsx` for strategy selection and comparison
- `frontend/lib/spatial-mapper.ts` maps backend path coordinates directly into 3D route overlays

## Boundaries

Still excluded from Step 6:

- multi-building city-scale routing
- smoke CFD and full fire-physics simulation
- cloud IoT streaming
- production dispatch optimization or legal-compliance tooling
