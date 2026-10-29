
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="local-agent-studio",
    )


@router.get("/ready", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    # FE-02A checks only local API prerequisites.
    # Ollama and Docker probes will be added separately.
    return ReadinessResponse(
        status="ready",
        checks={"api": "ready", "agent_registry": "ready"},
    )
