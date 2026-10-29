
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents.team import run_agent


class TeamState(TypedDict, total=False):
    task: str
    plan: str
    design: str
    implementation: str
    tests: str
    security_review: str
    final_review: str


def architect(state: TeamState):
    return {
        "plan": run_agent("architect", state["task"])
    }


def designer(state: TeamState):
    return {
        "design": run_agent(
            "designer",
            f"Task:\n{state['task']}\n\n"
            f"Architecture:\n{state['plan']}",
        )
    }


def developer(state: TeamState):
    return {
        "implementation": run_agent(
            "developer",
            f"Task:\n{state['task']}\n\n"
            f"Plan:\n{state['plan']}\n\n"
            f"Design:\n{state['design']}",
        )
    }


def tester(state: TeamState):
    return {
        "tests": run_agent(
            "tester",
            state["implementation"],
        )
    }


def security(state: TeamState):
    return {
        "security_review": run_agent(
            "security",
            state["implementation"],
        )
    }


def reviewer(state: TeamState):
    return {
        "final_review": run_agent(
            "reviewer",
            f"Implementation:\n{state['implementation']}\n\n"
            f"Tests:\n{state['tests']}\n\n"
            f"Security:\n{state['security_review']}",
        )
    }


builder = StateGraph(TeamState)

builder.add_node("architect", architect)
builder.add_node("designer", designer)
builder.add_node("developer", developer)
builder.add_node("tester", tester)
builder.add_node("security", security)
builder.add_node("reviewer", reviewer)

builder.add_edge(START, "architect")
builder.add_edge("architect", "designer")
builder.add_edge("designer", "developer")
builder.add_edge("developer", "tester")
builder.add_edge("tester", "security")
builder.add_edge("security", "reviewer")
builder.add_edge("reviewer", END)

software_team = builder.compile()
