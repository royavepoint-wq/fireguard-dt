"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusBadge } from "./StatusBadge";

type HealthResponse = {
  status: string;
  service: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function ApiStatusBadge() {
  const [isConnected, setIsConnected] = useState(false);

  const healthUrl = useMemo(() => `${API_BASE_URL}/health`, []);

  useEffect(() => {
    let active = true;

    const checkHealth = async () => {
      try {
        const response = await fetch(healthUrl, {
          method: "GET",
          cache: "no-store",
        });

        if (!response.ok) {
          if (active) setIsConnected(false);
          return;
        }

        const body = (await response.json()) as HealthResponse;
        if (active) {
          setIsConnected(body.status === "ok");
        }
      } catch {
        if (active) setIsConnected(false);
      }
    };

    void checkHealth();
    const timer = window.setInterval(() => {
      void checkHealth();
    }, 15000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [healthUrl]);

  return isConnected ? (
    <StatusBadge label="API CONNECTED" tone="safe" />
  ) : (
    <StatusBadge label="API OFFLINE" tone="critical" />
  );
}
