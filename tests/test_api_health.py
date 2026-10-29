
from fastapi.testclient import TestClient

from app.agents.registry import AGENTS
from app.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness():
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["api"] == "ready"


def test_agents_match_registry():
    response = client.get("/api/v1/agents")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == len(AGENTS)
    assert {a["id"] for a in payload["agents"]} == set(AGENTS)

    for agent in payload["agents"]:
        assert "system_prompt" not in agent


def test_unknown_endpoint():
    response = client.get("/api/v1/unknown")

    assert response.status_code == 404
