
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    blocked = "blocked"
    failed = "failed"
    completed = "completed"


class CreateTaskRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)


class TaskResponse(BaseModel):
    id: UUID
    task: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    selected_agents: list[str] = Field(default_factory=list)
    outputs: dict[str, str] = Field(default_factory=dict)
    qa_status: str | None = None
    review_status: str | None = None
    feedback: str | None = None
