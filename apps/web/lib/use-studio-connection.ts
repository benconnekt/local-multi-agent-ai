
"use client";

import { useEffect, useState } from "react";
import {
  studioApi,
  type ApiAgent,
} from "@/lib/api";

type ConnectionState = {
  status: "checking" | "connected" | "disconnected";
  agents: ApiAgent[];
  error: string | null;
};

export function useStudioConnection(): ConnectionState {
  const [state, setState] = useState<ConnectionState>({
    status: "checking",
    agents: [],
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();

    async function connect() {
      try {
        const health = await studioApi.health(controller.signal);

        if (health.status !== "ok") {
          throw new Error("API health check failed");
        }

        const response = await studioApi.agents(
          controller.signal,
        );

        if (!controller.signal.aborted) {
          setState({
            status: "connected",
            agents: response.agents,
            error: null,
          });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setState({
            status: "disconnected",
            agents: [],
            error:
              error instanceof Error
                ? error.message
                : "Connection failed",
          });
        }
      }
    }

    void connect();

    return () => controller.abort();
  }, []);

  return state;
}
