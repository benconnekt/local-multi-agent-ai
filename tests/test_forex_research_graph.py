import pytest
from app.trading.graphs.research_graph import run_research

@pytest.mark.parametrize("pair", ["EURUSD", "GBPUSD", "USDJPY"])
def test_research_fail_closed(pair):
    state = run_research(pair)
    report = state["report"]
    assert report["decision"] == "NO_TRADE"
    assert report["research_only"] is True
    assert report["broker_execution_enabled"] is False
    assert report["independently_certified"] is False
    assert report["research_signal_eligible"] is False
    assert len(state["events"]) == 6
    assert {e["agent_id"] for e in state["events"]} == {
        "market_data", "price_action", "technical", "sentiment", "risk", "supervisor"
    }
    assert state["findings"]["market_data"]["status"] == "unavailable"


def test_unknown_pair_rejected():
    with pytest.raises(ValueError):
        run_research("BTCUSD")
