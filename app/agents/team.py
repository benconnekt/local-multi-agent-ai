
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.registry import AGENTS
from app.core.llm import get_llm


def run_agent(role: str, task: str) -> str:
    agent = AGENTS.get(role)

    if agent is None:
        raise ValueError(f"Unknown agent: {role}")

    response = get_llm().invoke([
        SystemMessage(content=agent.system_prompt),
        HumanMessage(content=task),
    ])

    return str(response.content)
