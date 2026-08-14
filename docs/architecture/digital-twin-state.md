# Digital Twin State and Event Architecture

FireGuard DT Step 2 establishes the backend foundation for four coordinated domain twins, a shared event bus, and a lightweight decision orchestrator.

## Current Flow

```text
Physical / Simulated Inputs
        ↓
Domain Twin State
        ↓
Event Bus
        ↓
AI / Decision Orchestrator
        ↓
Frontend / Future 3D Spatial Model
```

## Domain Twins

### Fire & Environment Twin

Tracks demo baseline telemetry for a monitored zone:
- temperature
- temperature rate
- smoke level
- CO and CO2 levels
- humidity
- electrical load
- fire risk probability
- sensor health
- HVAC effect

### Building Infrastructure Twin

Tracks the current static building state for `FG-BLDG-01`:
- floors
- rooms
- corridors
- exits
- HVAC zones
- sprinklers
- electrical zones

Each entity uses stable spatial identifiers so later stages can attach shared 3D geometry without replacing the state model.

### Occupancy & Evacuation Twin

Tracks anonymous aggregate occupancy only:
- total occupancy
- zone occupancy counts
- density
- vulnerable counts
- evacuation status
- active evacuation routes

No personal identity data is modeled in Step 2.

### Emergency Response Twin

Tracks baseline response readiness:
- crews
- drones
- active incidents
- dispatch queue
- average response ETA

## Shared Event Bus

Step 2 uses an in-memory event bus under `backend/app/services/event_bus.py`.

Current characteristics:
- bounded rolling history of 500 events
- no Redis, Kafka, MQTT, or database yet
- supports publish, recent reads, twin filtering, and clearing

Current event types include:
- `SYSTEM_INITIALIZED`
- `TWIN_STATE_UPDATED`
- `SENSOR_UPDATE`
- `RISK_LEVEL_CHANGED`
- `INFRASTRUCTURE_STATUS_CHANGED`
- `OCCUPANCY_UPDATED`
- `ROUTE_UPDATED`
- `ROUTE_RECALCULATION_REQUESTED`
- `ROUTE_BLOCKED`
- `NO_SAFE_ROUTE`
- `RESOURCE_STATUS_CHANGED`
- `DISPATCH_CREATED`
- `APPROVAL_REQUIRED`
- `APPROVAL_GRANTED`
- `APPROVAL_REJECTED`
- `ANOMALY_DETECTED`

## Orchestrator Foundation

The Step 2 orchestrator is intentionally conservative.

It does not produce AI predictions.

It currently:
- reads all four twin states
- produces a combined cross-twin snapshot
- calculates a basic overall system status
- surfaces active alerts
- exposes the human oversight flag

This gives later stages a stable coordination layer without introducing fake decision intelligence.

## API Shape

Primary orchestration APIs:
- `GET /api/digital-twin/state`
- `POST /api/digital-twin/reset`
- `GET /api/orchestrator/status`
- `GET /api/events`

Twin APIs:
- `GET|PATCH|POST /api/twins/fire`
- `GET|PATCH|POST /api/twins/building`
- `GET|PATCH|POST /api/twins/occupancy`
- `GET|PATCH|POST /api/twins/response`

## Step 2 Boundaries

Still deferred to later stages:
- shared 3D building runtime
- machine learning
- SHAP explainability
- evacuation optimization
- fire propagation simulation
- scenario simulation engine
- ROI models