from concurrent.futures import Future
from app.trading.agents import run_store
from app.trading.agents.router import create_research_run, ResearchRequest, research_run, forex_agent_activity

def test_background_run(monkeypatch):
    class Immediate:
        def submit(self, fn, *args):
            fn(*args)
            return Future()
    monkeypatch.setattr(run_store, "_EXECUTOR", Immediate())
    result = create_research_run(ResearchRequest(instrument="EURUSD"))
    run = research_run(result["run_id"])
    assert run["status"] == "completed"
    assert len(run["events"]) == 6
    assert run["report"]["decision"] == "NO_TRADE"
    assert run["report"]["broker_execution_enabled"] is False
    assert len(run["findings"]) == 5
    assert any(event["run_id"] == run["run_id"] for event in forex_agent_activity()["events"])
