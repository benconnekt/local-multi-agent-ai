
from app.agents.supervisor import select_agents


def test_default_task_routing():
    assert select_agents("Write a Python function") == [
        "developer",
        "tester",
        "reviewer",
    ]


def test_api_task_routing():
    assert select_agents("Build a REST API") == [
        "architect",
        "developer",
        "tester",
        "security",
        "reviewer",
    ]


def test_frontend_task_routing():
    assert select_agents("Build a Flutter screen") == [
        "designer",
        "developer",
        "tester",
        "reviewer",
    ]


def test_review_task_routing():
    assert select_agents("Review this code") == [
        "reviewer",
        "security",
    ]

def test_build_does_not_match_ui():
    agents = select_agents("Build a REST API")

    assert agents[0] == "architect"
    assert "designer" not in agents
