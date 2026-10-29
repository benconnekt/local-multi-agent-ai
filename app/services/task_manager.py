
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import BoundedSemaphore, Lock
from uuid import UUID, uuid4
import logging

from app.api.schemas.tasks import (
    CreateTaskRequest,
    TaskResponse,
    TaskStatus,
)
from app.graphs.supervisor_graph import supervisor_graph

logger = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now(timezone.utc)


class TaskQueueFullError(Exception):
    pass


class TaskManager:
    def __init__(self, capacity: int = 4):
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="studio-agent",
        )
        self._slots = BoundedSemaphore(capacity)
        self._lock = Lock()
        self._tasks: dict[UUID, TaskResponse] = {}

    def submit(self, request: CreateTaskRequest) -> TaskResponse:
        if not self._slots.acquire(blocking=False):
            raise TaskQueueFullError(
                "Task capacity reached. Try again later."
            )

        task = TaskResponse(
            id=uuid4(),
            task=request.task,
            status=TaskStatus.queued,
            created_at=now(),
            updated_at=now(),
        )

        with self._lock:
            self._tasks[task.id] = task

        try:
            self._executor.submit(self._execute, task.id)
        except Exception:
            with self._lock:
                self._tasks.pop(task.id, None)
            self._slots.release()
            raise

        return task.model_copy(deep=True)

    def get(self, task_id: UUID) -> TaskResponse | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return task.model_copy(deep=True) if task else None

    def _update(self, task_id: UUID, **changes: object) -> None:
        with self._lock:
            existing = self._tasks[task_id]
            self._tasks[task_id] = existing.model_copy(
                update={**changes, "updated_at": now()}
            )

    def _execute(self, task_id: UUID) -> None:
        try:
            self._update(task_id, status=TaskStatus.running)

            task = self.get(task_id)
            if task is None:
                return

            result = supervisor_graph.invoke(
                {
                    "task": task.task,
                    "max_revisions": 2,
                },
                config={"recursion_limit": 30},
            )

            approved = (
                result.get("workflow_status") == "approved"
                and result.get("qa_status") == "passed"
                and result.get("review_status") == "approved"
                and bool(result.get("qa_source_sha256"))
            )

            # The current graph has no trusted approval path.
            # This additional check does not substitute for
            # evidence validation in the future.
            status = (
                TaskStatus.completed
                if approved
                else TaskStatus.blocked
            )

            self._update(
                task_id,
                status=status,
                selected_agents=result.get("selected_agents", []),
                outputs=result.get("outputs", {}),
                qa_status=result.get("qa_status"),
                review_status=result.get("review_status"),
                feedback=(
                    result.get("qa_feedback")
                    or result.get("review_feedback")
                ),
            )

        except Exception:
            logger.exception(
                "Task %s failed during workflow execution",
                task_id,
            )
            self._update(
                task_id,
                status=TaskStatus.failed,
                feedback="Workflow execution failed. Check server logs.",
        )

        finally:
            self._slots.release()


task_manager = TaskManager()
