# Shared 3D Spatial Model

FireGuard DT Step 3 adds a shared 3D spatial visualization layer on top of the existing four domain twins.

This 3D model is not a fifth digital twin.

It is the spatial integration layer that lets multiple twins reference the same building context through stable spatial IDs.

## Architectural Flow

```text
Four Domain Twins
       │
       ▼
Shared Spatial IDs
       │
       ▼
Spatial Mapper
       │
       ▼
React Three Fiber
       │
       ▼
Shared 3D Building Model
```

## Purpose

The shared 3D spatial model provides:
- a presentation-friendly building view for the Command Center
- a dedicated `/spatial` exploration surface
- a common geometry and ID layer for hazards, routes, occupancy, and response resources
- a stable foundation for later simulation, optimization, and decision-support steps

## Building Scope

Current building:
- `FG-BLDG-01`

Current floors:
- `floor-1`
- `floor-2`
- `floor-3`

Named areas currently modeled:
- Electrical Room
- Office Zone A
- Office Zone B
- Meeting Room
- Server / Utility Room
- Operations Deck
- Corridor A
- Corridor B
- Corridor C
- Exit A
- Exit B
- Exit C
- Exit D
- Stairwell A
- Stairwell B

## Stable Spatial IDs

The 3D layer reuses backend-aligned identifiers wherever possible, including:
- `room-electrical-01`
- `corridor-c`
- `exit-a`
- `exit-b`
- `exit-c`
- `exit-d`

These IDs allow the spatial mapper to connect live twin state to visual entities without embedding API logic into rendering components.

## Spatial Configuration

Geometry is defined centrally in:
- `frontend/data/building-layout.ts`

Each spatial entity includes:
- `id`
- `name`
- `type`
- `floorId`
- `position`
- `size`
- `rotation`

This keeps geometry data separate from React Three Fiber scene logic.

## Spatial Mapper

The mapper lives in:
- `frontend/lib/spatial-mapper.ts`

Its job is to transform backend twin state into visual state:
- fire risk -> room and corridor hazard tone
- smoke level -> smoke overlay visibility
- exit state -> available or blocked exit visuals
- occupancy zone data -> anonymous occupancy markers and density indicators
- response resource state -> crew and drone marker status
- backend routes -> safe, warning, or blocked route overlays

If a spatial mapping is missing, the scene should not crash. The model logs a useful warning and falls back to `N/A` where needed.

## Current Scene Controls

Current toolbar controls:
- `Building`
- `Floor 1`
- `Floor 2`
- `Floor 3`
- `Exploded`
- `Occupants`
- `Hazards`
- `Routes`
- `Resources`
- `Auto Rotate`
- `Reset Camera`

## Current Visual Layers

Implemented in Step 3:
- room geometry
- corridor geometry
- stairs
- exit markers
- occupant markers
- response resource markers
- route overlays
- warning and critical hazard overlays
- smoke visualization placeholder
- scene legend
- room information panel

Not yet implemented:
- real fire propagation
- dynamic route optimization
- evacuation simulation
- detailed agent movement
- advanced physics

## Live State Updates

The spatial pages use the Step 2 backend API:
- `GET /api/digital-twin/state`

Step 3 currently uses simple polling:
- every 2 seconds

This keeps the scene synchronized with developer actions such as:
- Increase Fire Twin Temperature
- Set Smoke Warning
- Block Exit B
- Increase Occupancy
- Assign Crew 1
- Reset All

## Command Center Integration

The Command Center now includes the shared 3D spatial model in the main layout:

```text
KPI Cards
    ↓
3D Model + Live System
    ↓
Event Timeline
```

## Future Extension Path

Later stages can build on this shared spatial layer for:
- hazard propagation and simulation
- evacuation pathfinding and optimization
- crew movement and dispatch planning
- explainability overlays
- scenario playback

Those later steps should reuse the same spatial IDs and mapper contract rather than creating a separate geometry system.