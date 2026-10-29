
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.tasks import (
    CreateTaskRequest,
    TaskResponse,
)
from app.services.task_manager import (
    TaskQueueFullError,
    task_manager,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_task(request: CreateTaskRequest) -> TaskResponse:
    try:
        return task_manager.submit(request)
    except TaskQueueFullError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID) -> TaskResponse:
    task = task_manager.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task
