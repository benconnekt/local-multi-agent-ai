
import json
import re
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.supervisor import select_agents
from app.agents.team import run_agent


ReviewStatus = Literal[
    "approved",
    "changes_requested",
    "blocked",
]

WorkflowStatus = Literal[
    "running",
    "approved",
    "blocked",
]


class SupervisorState(TypedDict, total=False):
    task: str
    selected_agents: list[str]
    outputs: dict[str, str]
    current_index: int

    revision_count: int
    max_revisions: int

    review_status: ReviewStatus
    review_feedback: str
    workflow_status: WorkflowStatus

    qa_status: Literal["pending", "passed", "failed", "blocked"]
    qa_feedback: str
    qa_source_sha256: str | None

def supervisor(state: SupervisorState) -> dict:
    agents = select_agents(state["task"])

    return {
        "selected_agents": agents,
        "outputs": {},
        "current_index": 0,
        "revision_count": 0,
        "max_revisions": state.get("max_revisions", 2),
        "review_status": "blocked",
        "review_feedback": "",
        "workflow_status": "running",

        "qa_status": "pending",
        "qa_feedback": "",
        "qa_source_sha256": None,
    }


def build_prompt(state: SupervisorState, role: str) -> str:
    outputs = state.get("outputs", {})

    # Keep context bounded for our local Ollama model.
    context = "\n\n".join(
        f"{name.upper()}:\n{content[:600]}"
        for name, content in outputs.items()
        if name != role
    )

    feedback = state.get("review_feedback", "")

    return (
        f"Original task:\n{state['task'][:600]}\n\n"
        f"Previous agent outputs:\n{context[:1200]}\n\n"
        f"Review feedback:\n{feedback[:600]}\n\n"
        f"Your role: {role}.\n"
        "Complete your responsibility concisely. "
        "Do not invent test execution or verification evidence."
    )


def execute_agent(state: SupervisorState) -> dict:
    agents = state["selected_agents"]
    index = state["current_index"]
    role = agents[index]

    # Review-capable workflows use a separate review node.
    if role == "reviewer" and "developer" in agents:
        return {"current_index": index + 1}

    result = run_agent(role, build_prompt(state, role))

    return {
        "outputs": {
            **state.get("outputs", {}),
            role: result,
        },
        "current_index": index + 1,
    }


def next_agent(state: SupervisorState) -> str:
    agents = state["selected_agents"]
    index = state["current_index"]

    if index < len(agents):
        return "execute_agent"

    if "developer" in agents:
        return "qa_gate"

    return "complete"


def parse_review(raw: str) -> tuple[ReviewStatus, str]:
    # Accept JSON even if the model wraps it in a Markdown code fence.
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw.strip(),
        flags=re.IGNORECASE,
    )

    try:
        data = json.loads(cleaned)

        if not isinstance(data, dict):
            raise ValueError("Review must be a JSON object")

        status = data.get("status")
        feedback = data.get("feedback", "")

        if status not in {
            "approved",
            "changes_requested",
            "blocked",
        }:
            raise ValueError("Invalid review status")

        if not isinstance(feedback, str):
            raise ValueError("Feedback must be a string")

        if status == "changes_requested" and not feedback.strip():
            raise ValueError("Changes requested without feedback")

        return status, feedback

    except (json.JSONDecodeError, ValueError):
        return (
            "blocked",
            "Reviewer did not return valid structured feedback.",
        )



def qa_gate(state: SupervisorState) -> dict:
    """
    Temporary fail-closed QA gate.

    Real execution will be connected through
    VerificationCoordinator in LG-02.
    """
    return {
        "qa_status": "blocked",
        "qa_feedback": (
            "No verified test execution evidence is available. "
            "Real QA execution is not connected."
        ),
        "qa_source_sha256": None,
    }


def after_qa(state: SupervisorState) -> str:
    if state.get("qa_status") == "passed":
        return "review"

    # Do not retry when verification infrastructure
    # is unavailable or evidence is missing.
    return "blocked"

def review(state: SupervisorState) -> dict:
    outputs = state.get("outputs", {})

    prompt = (
        "Review the implementation against the original task.\n"
        "Do not invent defects. Do not claim tests passed unless "
        "test execution evidence is provided.\n\n"
        f"Task:\n{state['task'][:500]}\n\n"
        f"Implementation:\n{outputs.get('developer', '')[:1200]}\n\n"
        f"QA assessment:\n{outputs.get('tester', '')[:600]}\n\n"
        "Return ONLY a JSON object with these fields:\n"
        '{"status":"approved|changes_requested|blocked",'
        '"feedback":"brief explanation"}'
    )

    raw = run_agent("reviewer", prompt)
    status, feedback = parse_review(raw)

    return {
        "outputs": {
            **outputs,
            "reviewer": raw,
        },
        "review_status": status,
        "review_feedback": feedback,
    }


def after_review(state: SupervisorState) -> str:
    if state["review_status"] == "approved":
        return "complete"

    if (
        state["review_status"] == "changes_requested"
        and state["revision_count"] < state["max_revisions"]
    ):
        return "revise"

    return "blocked"


def revise(state: SupervisorState) -> dict:
    return {
        "revision_count": state["revision_count"] + 1,
        "current_index": state["selected_agents"].index("developer"),
        "outputs": {
            key: value
            for key, value in state.get("outputs", {}).items()
            if key not in {"developer", "tester", "reviewer"}
        },
    }


def complete(state: SupervisorState) -> dict:
    agents = state.get("selected_agents", [])

    if "developer" in agents:
        # Until the real QA gate is connected,
        # development workflows must not be approved.
        return {
            "workflow_status": "blocked",
            "review_feedback": (
                "Real QA execution and evidence-based "
                "approval gates are not yet connected."
            ),
        }

    return {
        "workflow_status": "blocked",
        "review_feedback": (
            "No verified completion policy is configured "
            "for this workflow."
        ),
    }


def blocked(state: SupervisorState) -> dict:
    return {"workflow_status": "blocked"}



builder = StateGraph(SupervisorState)

# Register each node exactly once.
builder.add_node("supervisor", supervisor)
builder.add_node("execute_agent", execute_agent)
builder.add_node("qa_gate", qa_gate)
builder.add_node("review", review)
builder.add_node("revise", revise)
builder.add_node("complete", complete)
builder.add_node("blocked", blocked)

# Entry point.
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "execute_agent")

# Execute selected agents, then apply QA where required.
builder.add_conditional_edges(
    "execute_agent",
    next_agent,
    {
        "execute_agent": "execute_agent",
        "qa_gate": "qa_gate",
        "complete": "complete",
    },
)

# QA must pass before the reviewer can run.
builder.add_conditional_edges(
    "qa_gate",
    after_qa,
    {
        "review": "review",
        "blocked": "blocked",
    },
)

# Reviewer may approve, request revisions or block.
builder.add_conditional_edges(
    "review",
    after_review,
    {
        "complete": "complete",
        "revise": "revise",
        "blocked": "blocked",
    },
)

# Revision and terminal paths.
builder.add_edge("revise", "execute_agent")
builder.add_edge("complete", END)
builder.add_edge("blocked", END)

supervisor_graph = builder.compile()
