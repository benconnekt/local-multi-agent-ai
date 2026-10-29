
from fastapi import APIRouter

from app.agents.registry import AGENTS
from app.api.schemas.agents import AgentResponse, AgentsResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentsResponse)
def list_agents() -> AgentsResponse:
    agents = [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
        )
        for agent in AGENTS.values()
    ]

    return AgentsResponse(
        agents=agents,
        total=len(agents),
    )
