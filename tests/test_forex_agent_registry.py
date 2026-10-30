from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.trading.agents.router import router

def test_forex_registry_is_research_only():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    r = client.get("/api/v1/trading/agents")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 6
    assert data["decision"] == "NO_TRADE"
    assert data["research_only"] is True
    assert len(data["agents"]) == 6
    assert all(a.get("id") for a in data["agents"])

def test_readiness_fail_closed_and_no_fake_activity():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    readiness = client.get("/api/v1/trading/agents/readiness").json()
    assert readiness["broker_execution_enabled"] is False
    assert readiness["orchestrator_connected"] is True
    assert readiness["independently_certified"] is False
    activity = client.get("/api/v1/trading/agents/activity").json()

    assert isinstance(activity["events"], list)

    assert all(
        event["agent_id"] in {
            "market_data",
            "price_action",
            "technical",
            "sentiment",
            "risk",
            "supervisor",
        }
        for event in activity["events"]
)
