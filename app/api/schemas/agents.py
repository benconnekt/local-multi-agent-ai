
from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str


class AgentsResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
