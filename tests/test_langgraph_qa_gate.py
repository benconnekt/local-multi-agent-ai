
from app.graphs.supervisor_graph import (
    qa_gate,
    after_qa,
    complete,
)


def test_missing_qa_evidence_blocks_execution():
    state = {
        "task": "Create a Python function",
        "selected_agents": [
            "developer",
            "tester",
            "reviewer",
        ],
        "outputs": {
            "developer": "def example(): return 1",
        },
    }

    result = qa_gate(state)

    assert result["qa_status"] == "blocked"
    assert result["qa_source_sha256"] is None
    assert after_qa({**state, **result}) == "blocked"


def test_successful_qa_status_routes_to_review():
    state = {
        "qa_status": "passed",
    }

    assert after_qa(state) == "review"


def test_completion_remains_blocked():
    state = {
        "selected_agents": [
            "developer",
            "tester",
            "reviewer",
        ],
        "review_status": "approved",
        "qa_status": "passed",
    }

    result = complete(state)

    assert result["workflow_status"] == "blocked"
