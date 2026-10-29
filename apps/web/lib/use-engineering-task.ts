"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  getEngineeringTask,
  submitEngineeringTask,
  type StudioTask,
} from "@/lib/api";

const POLL_INTERVAL_MS = 2500;

function isActive(task: StudioTask | null): boolean {
  return task?.status === "queued" || task?.status === "running";
}

export function useEngineeringTask() {
  const [task, setTask] = useState<StudioTask | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lock = useRef(false);
  const activeTask = useRef(false);

  const submit = useCallback(async (description: string): Promise<boolean> => {
    const trimmed = description.trim();
    if (!trimmed || trimmed.length > 4000 || lock.current || activeTask.current) {
      return false;
    }

    lock.current = true;
    setSubmitting(true);
    setError(null);
    try {
      const created = await submitEngineeringTask(trimmed);
      activeTask.current = isActive(created);
      setTask(created);
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to submit task.");
      return false;
    } finally {
      lock.current = false;
      setSubmitting(false);
    }
  }, []);

  const taskId = task?.id;
  const taskStatus = task?.status;

  useEffect(() => {
    if (!taskId || (taskStatus !== "queued" && taskStatus !== "running")) return;

    const id = taskId;
    const controller = new AbortController();
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const updated = await getEngineeringTask(id, controller.signal);
        if (stopped) return;
        activeTask.current = isActive(updated);
        setTask(updated);
        setError(null);
        if (isActive(updated)) timer = setTimeout(poll, POLL_INTERVAL_MS);
      } catch (cause) {
        if (stopped || controller.signal.aborted) return;
        setError(cause instanceof Error ? cause.message : "Unable to refresh task.");
        timer = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    void poll();
    return () => {
      stopped = true;
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [taskId, taskStatus]);

  return { task, submitting, running: isActive(task), error, submit };
}
