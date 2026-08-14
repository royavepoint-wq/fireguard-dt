from __future__ import annotations

from app.simulation.models import SimulationPhase

PHASE_SCHEDULE: list[tuple[int, int, SimulationPhase, str]] = [
    (0, 10, SimulationPhase.NORMAL, "Monitoring"),
    (10, 20, SimulationPhase.ANOMALY, "Anomaly Detected"),
    (20, 35, SimulationPhase.WARNING, "Predictive Warning"),
    (35, 50, SimulationPhase.CRITICAL, "Critical Emergency"),
    (50, 70, SimulationPhase.EVACUATION, "Evacuation"),
    (70, 85, SimulationPhase.RESPONSE, "Emergency Response"),
    (85, 105, SimulationPhase.CONTAINMENT, "Containment"),
    (105, 121, SimulationPhase.RESOLVED, "Resolved"),
]


def get_phase_for_elapsed(elapsed_seconds: int) -> SimulationPhase:
    for start, end, phase, _label in PHASE_SCHEDULE:
        if start <= elapsed_seconds < end:
            return phase
    return SimulationPhase.RESOLVED


def get_stage_label(phase: SimulationPhase) -> str:
    for _start, _end, current_phase, label in PHASE_SCHEDULE:
        if current_phase == phase:
            return label
    return "Monitoring"


def get_step_index(phase: SimulationPhase) -> int:
    for index, (_start, _end, current_phase, _label) in enumerate(PHASE_SCHEDULE, start=1):
        if current_phase == phase:
            return index
    return 1