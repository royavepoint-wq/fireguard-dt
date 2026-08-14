"use client";

import { useEffect, useState } from "react";

import {
  approveSimulationActionById,
  getSimulationRuns,
  getSimulationScenarios,
  getSimulationStatus,
  pauseSimulation,
  rejectSimulationActionById,
  resetSimulation,
  resumeSimulation,
  setSimulationSpeed,
  startSimulation,
  stopSimulation,
} from "@/lib/api";
import type { SimulationRunSummary, SimulationScenario, SimulationStartRequest, SimulationState } from "@/lib/types";

type UseSimulationRuntimeOptions = {
  pollMs?: number;
};

const defaultStartRequest: SimulationStartRequest = {
  scenario_id: "electrical-room-fire",
  speed_multiplier: 1,
  auto_approve: true,
  presentation_mode: false,
};

export function useSimulationRuntime(options: UseSimulationRuntimeOptions = {}) {
  const pollMs = options.pollMs ?? 1000;
  const [autoApprovePreference, setAutoApprovePreference] = useState(true);
  const [simulation, setSimulation] = useState<SimulationState | null>(null);
  const [scenarios, setScenarios] = useState<SimulationScenario[]>([]);
  const [runs, setRuns] = useState<SimulationRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  async function refresh(showSpinner = false) {
    if (showSpinner) {
      setLoading(true);
    }
    setError(null);

    try {
      const [nextStatus, nextScenarios, nextRuns] = await Promise.all([
        getSimulationStatus(),
        getSimulationScenarios(),
        getSimulationRuns(),
      ]);
      setSimulation(nextStatus);
      setScenarios(nextScenarios);
      setRuns(nextRuns.slice().reverse());
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unable to load simulation runtime.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    async function loadOnMount() {
      try {
        const [nextStatus, nextScenarios, nextRuns] = await Promise.all([
          getSimulationStatus(),
          getSimulationScenarios(),
          getSimulationRuns(),
        ]);
        if (!active) {
          return;
        }
        setSimulation(nextStatus);
        setScenarios(nextScenarios);
        setRuns(nextRuns.slice().reverse());
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load simulation runtime.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadOnMount();

    const timer = window.setInterval(() => {
      void refresh(false);
    }, pollMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [pollMs]);

  async function runStart(payload?: Partial<SimulationStartRequest>) {
    setPending("start");
    try {
      await startSimulation({ ...defaultStartRequest, auto_approve: autoApprovePreference, ...payload });
      await refresh(false);
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Unable to start simulation.");
    } finally {
      setPending(null);
    }
  }

  async function runPresentationDemo() {
    await runStart({ scenario_id: "electrical-room-fire", speed_multiplier: 5, auto_approve: autoApprovePreference, presentation_mode: true });
  }

  async function runAction(action: "pause" | "resume" | "stop" | "reset" | "approve" | "reject", speed?: number) {
    setPending(action);
    setError(null);

    try {
      if (action === "pause") {
        await pauseSimulation();
      }
      if (action === "resume") {
        await resumeSimulation();
      }
      if (action === "stop") {
        await stopSimulation();
      }
      if (action === "reset") {
        await resetSimulation();
      }
      if (action === "approve") {
        const approvalId = simulation?.pending_approval?.approval_id;
        if (!approvalId) {
          throw new Error("No pending approval request exists.");
        }
        await approveSimulationActionById(approvalId);
      }
      if (action === "reject") {
        const approvalId = simulation?.pending_approval?.approval_id;
        if (!approvalId) {
          throw new Error("No pending approval request exists.");
        }
        await rejectSimulationActionById(approvalId);
      }
      if (typeof speed === "number") {
        await setSimulationSpeed(speed);
      }
      await refresh(false);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Unable to update simulation state.");
    } finally {
      setPending(null);
    }
  }

  async function changeSpeed(speed: number) {
    setPending(`speed-${speed}`);
    setError(null);
    try {
      await setSimulationSpeed(speed);
      await refresh(false);
    } catch (speedError) {
      setError(speedError instanceof Error ? speedError.message : "Unable to update simulation speed.");
    } finally {
      setPending(null);
    }
  }

  async function runAgain() {
    const scenarioId = simulation?.scenario_id ?? defaultStartRequest.scenario_id;
    const speedMultiplier = simulation?.speed_multiplier ?? defaultStartRequest.speed_multiplier;

    setPending("run-again");
    setError(null);
    try {
      await resetSimulation();
      await startSimulation({
        scenario_id: scenarioId,
        speed_multiplier: speedMultiplier,
        auto_approve: autoApprovePreference,
        presentation_mode: false,
      });
      await refresh(false);
    } catch (runAgainError) {
      setError(runAgainError instanceof Error ? runAgainError.message : "Unable to run the scenario again.");
    } finally {
      setPending(null);
    }
  }

  return {
    simulation,
    scenarios,
    runs,
    loading,
    error,
    pending,
    autoApprovePreference,
    setAutoApprovePreference,
    refresh,
    runStart,
    runPresentationDemo,
    runAction,
    changeSpeed,
    runAgain,
  };
}