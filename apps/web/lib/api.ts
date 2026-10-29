
export type ApiAgent = {
  id: string;
  name: string;
  role: string;
};

export type AgentsResponse = {
  agents: ApiAgent[];
  total: number;
};

export type HealthResponse = {
  status: string;
  service: string;
};


export type TaskStatus =
  | "queued"
  | "running"
  | "blocked"
  | "failed"
  | "completed";

export type StudioTask = {
  id: string;
  task: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  selected_agents: string[];
  outputs: Record<string, string>;
  qa_status: string | null;
  review_status: string | null;
  feedback: string | null;
};

export async function submitEngineeringTask(
  task: string,
): Promise<StudioTask> {
  const response = await fetch(
    `${API_BASE_URL}/tasks`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task }),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Task submission failed: HTTP ${response.status}`,
    );
  }

  return (await response.json()) as StudioTask;
}

export async function getEngineeringTask(
  id: string,
  signal?: AbortSignal,
): Promise<StudioTask> {
  return apiGet<StudioTask>(
    `/tasks/${encodeURIComponent(id)}`,
    signal,
  );
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1";

async function apiGet<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    signal,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API returned HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export const studioApi = {
  health: (signal?: AbortSignal) =>
    apiGet<HealthResponse>("/health", signal),

  agents: (signal?: AbortSignal) =>
    apiGet<AgentsResponse>("/agents", signal),
};

